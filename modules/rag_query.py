import time
import json
from utils.utils import (
    read_prompt,
    ret_time,
    indent_string,
    trunc_sysmon_event,
    ts_to_utc,
)
from ioc.ioc import IOC


class RAGQuery:

    def __init__(
        self, query_dict, llm_api, frag, query_state_manager, llm_config, logger
    ):
        self.query_dict = query_dict
        self.llm_api = llm_api
        self.frag = frag
        self.query_state_manager = query_state_manager
        self.llm_config = llm_config
        self.logger = logger
        self.verbose_reasoner = True

    def execute(self):
        """
        Executes a new RAG pipeline query with specified configurations and handles cancellation signals.

        This function retrieves configuration settings from query_dict, generates queries using
        generate_rag_query, and checks for cancellation signals before proceeding. It prunes the
        queries, sets status messages, and sends them to an LLM API while monitoring for cancellation
        signals throughout the process. If a cancellation signal is received at any point, it logs a
        warning and updates the query state manager accordingly. The function iterates through tokens
        from the LLM API response until a sufficient length is reached or if cancelled. Upon completion,
        it sets the status to idle and appends final messages to the query state manager.

        Args:
            self (object): The instance of the class containing this method.

        Raises:
            None explicitly raised but handles cancellation signals gracefully.
        """
        self.verbose_reasoner = self.query_dict.get("verbose_reasoner", True)
        _query_list = self.query_dict.get("query_list")
        query_list = self.generate_rag_query(_query_list)
        if self.query_state_manager.is_status_cancelled() is True:
            self.logger.warning("execute_new_rag_pipeline: Received cancel signal")
            self.query_state_manager.append_reasoner_header("Query Cancelled")
            self.query_state_manager.append_msg_text(" ")
            self.query_state_manager.set_status_idle()
            return
        self.llm_api.prune_queries(query_list)
        self.query_state_manager.set_status("Analyzing Context")
        self.query_state_manager.append_reasoner_header(
            f"Sending {len(query_list):,} Queries to LLM"
        )
        while True:
            if self.query_state_manager.is_status_cancelled() is True:
                self.query_state_manager.append_reasoner_header("Query Cancelled")
                self.query_state_manager.append_msg_text(" ")
                self.query_state_manager.set_status_idle()
                self.logger.warning("execute_new_rag_pipeline: Received cancel signal")
                return
            response_len = 0
            _msg = ""
            for token in self.llm_api.query(None, query_list, self.query_state_manager):
                if token:
                    if self.query_state_manager.is_status_cancelled() is True:
                        self.query_state_manager.append_reasoner_header(
                            "Query Cancelled"
                        )
                        self.query_state_manager.append_msg_text(" ")
                        self.query_state_manager.set_status_idle()
                        self.logger.warning(
                            "execute_new_rag_pipeline: Received cancel signal"
                        )
                        return
                    if self.query_state_manager.get_status() == "Analyzing Context":
                        self.query_state_manager.set_status("Generating")
                    self.query_state_manager.append_msg_text(token)
                    _msg = f"{_msg}{token}"
                    response_len = len(_msg)
            if response_len > 16:
                break
            self.query_state_manager.append_reasoner_header("Query Restart")
        self.query_state_manager.set_status_idle()
        self.query_state_manager.append_reasoner_header("Query Finished")
        self.query_state_manager.append_msg_text(" ")
        return

    def generate_rag_query(self, query_list):
        """
        Generates a RAG query from a given list of queries.

        This function processes each query in the provided list, expanding and formatting it as needed. It checks for cancellation status at various stages to allow early exit if required. The function generates conditions and context events based on the expanded query string and appends them back into the query list. If no events are found or if the process is cancelled, appropriate messages are logged, and an empty list is returned.

        Args:
            query_list (list): A list of queries to be processed. Each query should be a tuple where the second element is the query string.

        Returns:
            list: The updated query list with expanded context events appended for each query. If no events are found or if the process is cancelled, an empty list is returned.
        """
        self.query_state_manager.set_status("Interpreting")
        query_string = query_list.pop()[1]
        expanded_query_string = self.expand_ctx_query_string(query_string, query_list)
        if self.query_state_manager.is_status_cancelled() is True:
            return []
        meta_dict = self.generate_time_range_conditions(query_string)
        if self.query_state_manager.is_status_cancelled() is True:
            return []
        condition_dict = self.generate_query_conditions(expanded_query_string)
        if self.query_state_manager.is_status_cancelled() is True:
            return []
        query_dict = {
            "query_string": expanded_query_string,
            "condition_dict": condition_dict,
            "doc_multi_hit": False,
            "max_shard_ctx": 3,
            "n_results": 250,
        }
        if meta_dict:
            query_dict["meta_dict"] = meta_dict
        if self.verbose_reasoner is True:
            self.query_state_manager.append_reasoner_header("Generated Search Query")
            self.query_state_manager.append_reasoner_text(
                json.dumps(query_dict, indent=2)
            )
            self.query_state_manager.append_reasoner_header(
                "Searching Forensic Artifacts"
            )
        else:
            self.query_state_manager.append_reasoner_header(
                "Searching Forensic Artifacts"
            )
        expanded_query_string_context_events = self.generate_context_query(query_dict)
        if expanded_query_string_context_events is None:
            self.query_state_manager.append_reasoner_header("No Events found for query")
            self.query_state_manager.append_msg_text(
                "No events retrieved from generated query."
            )
            self.query_state_manager.set_status_cancelled()
            return []
        if self.query_state_manager.is_status_cancelled() is True:
            return []
        query_list.append(
            [
                "user",
                f"""<CONTEXT EVENTS>
{expanded_query_string_context_events}
</END CONTEXT EVENTS>""",
            ]
        )
        exe_rag_query = read_prompt("exe_rag_query")
        exe_rag_query = exe_rag_query.format(
            dtg=ret_time(time.time()),
            query_string=indent_string(query_string, spaces=8),
            expanded_query_string=indent_string(expanded_query_string, spaces=8),
        )
        query_list.append(["user", exe_rag_query])
        return query_list

    def generate_context_query(self, query_dict):
        """

        Generates a context query based on the provided query dictionary.

        This method sets up the query state manager to 'Loading Context', retrieves values and
        metadata from the fragment (frag) using the given query dictionary, and constructs a
        verbose query string by appending truncated system monitor events until the token count
        exceeds the maximum allowed context. It logs the number of retrieved events and their
        context size, appends a reasoner header to the query state manager, and returns the
        constructed verbose query if it is not empty; otherwise, it returns None.

        Args:
            query_dict (dict): A dictionary containing the query parameters.

        Returns:
            str or None: The constructed verbose query string if events are retrieved, else None.
        """
        self.query_state_manager.set_status("Loading Context")
        values, meta = self.frag.query(query_dict)
        ctx_cnt = 0
        verbose_query = ""
        for value in values:
            trunc_value = trunc_sysmon_event(value)
            if (
                self.llm_api.get_token_cnt(verbose_query + str(trunc_value))
                >= self.llm_api.max_rag_context
            ):
                break
            verbose_query = f"{verbose_query}\n{trunc_value}\n"
            self.query_state_manager.append_event(value)
            ctx_cnt += 1
        self.logger.info(
            f"generate_rag_query: Retrieved {ctx_cnt:,} events with {self.llm_api.get_token_cnt(verbose_query):,} context"
        )
        self.query_state_manager.append_reasoner_header(f"Retrieved {ctx_cnt:,} events")
        if len(verbose_query) == 0:
            return None
        else:
            return verbose_query

    def expand_ctx_query_string(self, query_string, query_list):
        """
        Expands a context query string based on a chat history and user query.

        This function constructs a formatted chat history from a list of speaker-text pairs,
        integrates it into an expanded context query template, and processes the query through
        a reasoner to potentially expand the original query string. If the verbose_reasoner flag
        is set, additional headers and text are appended to the query state manager for tracking.
        The function returns the expanded query if it is longer than the original query; otherwise,
        it returns the original query.

        Args:
            query_string (str): The original user query string to be expanded.
            query_list (list of tuples): A list where each element is a tuple containing a speaker
                and their corresponding text.

        Returns:
            str: The expanded query string if it is longer than the original query; otherwise,
                 the original query string.
        """
        chat_list = []
        for [speaker, text] in query_list:
            chat_list.append(f"## {speaker.capitalize()}:")
            chat_list.append(f"{text}")
            chat_list.append("")
        chat_history = "\n".join(chat_list)
        expand_ctx_query = read_prompt("expand_ctx_query")
        expand_ctx_query = expand_ctx_query.format(
            dtg=ret_time(time.time()),
            chat_history=indent_string(chat_history, spaces=12),
            user_query=indent_string(query_string, spaces=12),
        )
        if self.verbose_reasoner is True:
            self.query_state_manager.append_reasoner_header("Expand User Query")
            self.query_state_manager.append_reasoner_text(expand_ctx_query)
        else:
            self.query_state_manager.append_reasoner_header("Expand User Query")
        expanded_query_string = self.stream_reasoner_query(expand_ctx_query)
        if len(expanded_query_string) > len(query_string):
            return expanded_query_string
        else:
            return query_string

    def generate_query_conditions(self, expanded_query_string):
        """
        Generates query conditions based on an expanded query string.

        This method sets up a state for analyzing the search and processes the query to generate
        indicators of compromise (IOC). It iteratively reads prompts and formats them, handling
        exceptions and adjusting the temperature of the language model API if necessary. The method
        builds a dictionary of unique IOC strings and generates a condition dictionary based on these
        strings up to a specified limit.

        Args:
            expanded_query_string (str): The query string that has been expanded for analysis.

        Returns:
            dict: A dictionary containing the generated query conditions.
        """
        self.query_state_manager.set_status("Analyzing Search")
        ioc = IOC()
        max_indc_limit = 100
        string_dict = {}
        q_dict = {
            "query_string": expanded_query_string,
            "doc_multi_hit": False,
            "max_shard_ctx": 10,
            "n_results": 3,
            "condition_dict": {},
        }
        _, meta = self.frag.query(q_dict, prompts=True)
        for m in meta:
            ioc_list = ioc.get_tactic_ioc(m["tactic"])
            for entry in ioc_list:
                string_dict[str(entry).casefold()] = True
        generate_indicators = read_prompt("generate_indicators")
        generate_indicators = generate_indicators.format(
            dtg=ret_time(time.time()),
            query_string=indent_string(expanded_query_string, spaces=8),
        )
        if self.verbose_reasoner is True:
            self.query_state_manager.append_reasoner_header("Building IOC Queries")
            self.query_state_manager.append_reasoner_text(generate_indicators)
        else:
            self.query_state_manager.append_reasoner_header("Building IOC Queries")
        cnt = 0
        max_cnt = 16
        while True:
            cnt += 1
            if cnt > max_cnt:
                break
            if self.query_state_manager.is_status_cancelled() is True:
                return {}
            generate_indicators = read_prompt("generate_indicators")
            generate_indicators = generate_indicators.format(
                dtg=ret_time(time.time()),
                query_string=indent_string(expanded_query_string, spaces=8),
            )
            indicators = self.stream_reasoner_query(generate_indicators)
            try:
                lines = json.loads(indicators.strip())
                if isinstance(lines, list):
                    if isinstance(lines[0], str):
                        pass
                    else:
                        raise ValueError("item is not string")
                else:
                    raise ValueError("lines is not list")
            except Exception as e:
                self.llm_api.increase_temperature()
                self.logger.debug(f"generate_query_conditions: raised {e}")
                continue
            lines_added = 0
            for line in lines:
                _line = str(line).casefold()
                if len(_line) < 4:
                    continue
                if (_line in string_dict) is False:
                    lines_added += 1
                    string_dict[_line] = True
            if lines_added == 0:
                self.llm_api.increase_temperature()
            if len(string_dict) >= max_indc_limit:
                break
        self.llm_api.reset_temperature()
        condition_dict = self.generate_cond_dict(
            list(string_dict.keys())[:max_indc_limit]
        )
        return condition_dict

    def generate_time_range_conditions(self, query_string):
        """
        Generates time range conditions based on a query string.

        This method appends a reasoner header and sets the status to 'Analyzing Time Ranges'. It then
        iteratively extracts time ranges from the query string until valid start and end times are found,
        or until a maximum count is reached or the operation is cancelled. If successful, it returns a
        dictionary with the extracted time range conditions; otherwise, it raises an exception or
        returns an empty dictionary if the operation is cancelled.

        Args:
            query_string (str): The query string from which to extract time ranges.

        Returns:
            dict: A dictionary containing the extracted time range conditions, or an empty dictionary
                  if the operation was cancelled.

        Raises:
            ValueError: If the extracted time range dictionary is not a valid dictionary.
        """
        self.query_state_manager.append_reasoner_header("Extract Time Range")
        self.query_state_manager.set_status("Analyzing Time Ranges")
        cnt = 0
        max_cnt = 16
        meta_dict = None
        while True:
            cnt += 1
            if cnt > max_cnt:
                break
            if self.query_state_manager.is_status_cancelled() is True:
                return {}
            extract_timerange = read_prompt("extract_timerange")
            extract_timerange = extract_timerange.format(
                dtg=ret_time(time.time()),
                query_string=indent_string(query_string, spaces=8),
            )
            _tr = self.stream_reasoner_query(extract_timerange, dot_chars=4)
            try:
                tr = self.carve_dict(_tr)
                tr_dict = json.loads(tr.strip())
                if isinstance(tr_dict, dict):
                    if len(tr_dict.keys()) == 0:
                        break
                    start = ts_to_utc(tr_dict["start"])
                    end = ts_to_utc(tr_dict["end"])
                    if start > 0 and end > 0:
                        meta_dict = tr_dict
                        meta_dict = {
                            "$and": [{"utc": {"$gt": start}}, {"utc": {"$lt": end}}]
                        }
                        break
                else:
                    raise ValueError("tr_dict is not dict")
            except Exception as e:
                self.llm_api.increase_temperature()
                self.logger.debug(f"generate_time_range_conditions: raised {e}")
                continue
        self.llm_api.reset_temperature()
        return meta_dict

    def carve_dict(self, text):
        """
        Removes lines containing backticks from a given text and returns the modified text.

        This function splits the input text into lines, skips any line that contains a backtick
        (`), and then joins the remaining lines back together to form the output text.

        Args:
            text (str): The original text from which lines containing backticks should be removed.

        Returns:
            str: The modified text with lines containing backticks removed.
        """
        lines = []
        for line in text.split("\n"):
            if "`" in line:
                continue
            lines.append(line)
        return "\n".join(lines)

    def stream_reasoner_query(self, prompt, dot_chars=10):
        """
        Streams a reasoner query with specified parameters and handles the response.

        This function attempts to stream a query to an LLM API up to a maximum number of tries.
        It appends generated tokens to the response string, managing the state through a
        query state manager. If verbose mode is enabled, it directly appends tokens; otherwise,
        it adds dots at specified intervals. The function handles cancellation requests and
        restarts queries if necessary.

        Args:
            prompt (str): The input prompt for the LLM API query.
            dot_chars (int): The interval at which to append a dot character when not in verbose
                mode, default is 10.

        Returns:
            str: The generated response from the LLM API query.
        """
        cnt = 0
        max_tries = 10
        ret_val = ""
        while True:
            cnt += 1
            if cnt > max_tries:
                break
            if self.verbose_reasoner is False:
                self.query_state_manager.append_reasoner_text("- .")
            ret_val = ""
            response_len = 0
            for token in self.llm_api.query(
                None, [["user", prompt]], self.query_state_manager
            ):
                if self.query_state_manager.is_status_cancelled() is True:
                    return ""
                if token:
                    if self.query_state_manager.get_status() != "Generating":
                        self.query_state_manager.set_status("Generating")
                    ret_val = f"{ret_val}{token}"
                    response_len = len(ret_val)
                    if self.verbose_reasoner is True:
                        self.query_state_manager.append_reasoner_text(token)
                    elif response_len and response_len % dot_chars == 0:
                        self.query_state_manager.append_reasoner_text(".")
            if response_len >= 1:
                break
            self.query_state_manager.append_reasoner_header("Query Restart")
            continue
        self.query_state_manager.append_reasoner_text("\n")
        return ret_val

    @classmethod
    def generate_cond_dict(cls, text, min_len=4, max_condition=256):
        """
        Generates a condition dictionary from given text or list of words.

        This method processes input text or list to create a condition dictionary with
        specified constraints on word length and maximum conditions. It sorts the words by
        length in descending order, removes duplicates, and constructs a dictionary based on
        the '$contains' key for single conditions or '$or' for multiple conditions.

        Args:
            text (str or list): The input text or list of words to process. If it is a string,
                newlines are replaced with spaces and split into words.
            min_len (int, optional): The minimum length of words to include in the condition
                dictionary. Defaults to 4.
            max_condition (int, optional): The maximum number of conditions allowed in the
                dictionary. Defaults to 256.

        Returns:
            dict: A dictionary representing the generated conditions based on the input text or
                list. If no valid words are found, an empty dictionary is returned.
        """
        if isinstance(text, str):
            text = text.replace("\n", " ")
            words = text.split(" ")
        elif isinstance(text, list):
            words = text
        else:
            return {}
        words.sort(key=len, reverse=True)
        condition_list = []
        condition_dict = {}
        u_strings = {}
        for _word in words:
            word = _word.strip(" \t.'\"\\`")
            if word and len(word) >= min_len and (word in u_strings) is False:
                condition_list.append({"$contains": word})
                u_strings[word] = True
            if len(condition_list) >= max_condition:
                break
        if len(condition_list) == 1:
            condition_dict = {"$contains": condition_list[0]["$contains"]}
        elif len(condition_list) > 1:
            condition_dict = {"$or": condition_list}
        return condition_dict
