import time
import re
import sys
from openai import OpenAI
import tiktoken


class LLMAPI:

    def __init__(self, llm_config, logger):
        self.logger = logger
        self.api_url = llm_config.get("api_url", "")
        self.api_key = llm_config.get("api_key", "")
        self.model = llm_config.get("model", "")
        self.ctx = llm_config.get("context", 1)
        self.max_rag_context = llm_config.get("max_rag_context", int(self.ctx // 2))
        self.timeout = llm_config.get("timeout", 0.0)
        self._temperature = round(llm_config.get("temperature", 0.0), 2)
        self.temperature = round(float(self._temperature), 2)
        self.debug_llm_output = llm_config.get("debug", False)
        self.model_error_triggered = False

    def reset_temperature(self):
        """
        Resets the temperature to a rounded value of the current temperature.

        This method sets the temperature attribute by rounding the float value of
        _temperature to two decimal places. It ensures that the temperature is stored as an
        integer or float with precision up to two decimal points.

        Args:
            self (object): The instance of the class containing this method.

        Returns:
            None
        """
        self.temperature = round(float(self._temperature), 2)

    def increase_temperature(self):
        """
        Increases the temperature by a small increment without exceeding a maximum value.

        This method adjusts the temperature attribute of an object by adding 0.05 to its current
        value and rounding it to two decimal places. The temperature will not be increased beyond
        a maximum value of 2.0.

        Args:
            self (object): The instance of the class containing this method, which has a
                'temperature' attribute that is being modified.
        """
        self.temperature = round(min(self.temperature + 0.05, 2.0), 2)

    def get_token_cnt(self, text_string):
        """
        Calculates the token count of a given text string based on the model.

        This method attempts to use a specific encoding if 'gpt' is in the model name, and falls
        back to a regex-based approach if that fails or if 'gpt' is not in the model name. It logs
        critical errors when loading the tokenizer for the model raises an exception. The token count
        is calculated by splitting the text into words and punctuation marks, then summing up their
        lengths divided by 1.5, rounding to the nearest integer if necessary.

        Args:
            self (object): The instance of the class containing this method.
            text_string (str): The input text string for which token count is calculated.

        Returns:
            int: The total number of tokens in the given text string.

        Raises:
            Exception: If an error occurs during encoding or regex processing, it logs the error and
                continues with a fallback method.
        """
        if "gpt" in self.model:
            try:
                encoding = tiktoken.encoding_for_model(self.model)
                return len(encoding.encode(text_string))
            except Exception as e:
                if self.model_error_triggered is False:
                    self.model_error_triggered = True
                    self.logger.critical(
                        f"get_token_cnt: Loading tokenizer for model {self.model} raised {e}"
                    )
        try:
            tokens = re.findall(
                "\\b\\w+\\b|[\\.\\,\\!\\?\\;\\:\\-\\—\\(\\)\\[\\]\\{\\}\\\"\\'\\`]",
                text_string,
            )
        except Exception as e:
            tokens = str(text_string).split(" ")
        token_cnt = 0
        for t in tokens:
            if len(t) > 1:
                _cnt = len(t) / 1.5
                if _cnt < 1:
                    token_cnt += 1
                else:
                    token_cnt += round(_cnt)
        return token_cnt

    def prune_queries(self, query_list):
        """
        Prunes queries from a list until the total token count is within the context limit.

        This method iteratively removes entries from the query_list until the combined length
        of their content strings does not exceed the specified context limit (self.ctx). It
        calculates the token count for the concatenated content strings and pops elements
        from the list if the total token count exceeds the limit.

        Args:
            query_list (list): A list of queries, where each entry is a tuple containing at
                least two elements with the second element being a string to be concatenated.

        Returns:
            None
        """
        while True:
            content_str = ""
            for entry in query_list:
                content_str = f"{content_str}{entry[1]}"
            content_token_len = self.get_token_cnt(content_str)
            if content_token_len <= self.ctx:
                break
            else:
                _ = query_list.pop(0)

    def atomic_query(self, agent_prep, instructions, max_response_ctx=None):
        """
        Executes an atomic query with specified parameters and returns a message.

        This method resets the temperature, then repeatedly queries until it receives a valid
        response or exceeds the maximum response context. It concatenates tokens from each
        query to form a message and increases the temperature if no valid response is received.

        Args:
            agent_prep (Any): Preparation details for the agent executing the query.
            instructions (str): Instructions for the query.
            max_response_ctx (int, optional): Maximum context length for the response. Defaults to None.

        Returns:
            str: The concatenated message formed from the query tokens.
        """
        self.reset_temperature()
        msg = ""
        while True:
            for token in self.query(agent_prep, instructions, max_response_ctx):
                msg = f"{msg}{token}"
            if len(msg) > 2:
                break
            msg = ""
            self.increase_temperature()
        return msg

    def query(
        self, agent_prep, instructions, query_state_manager=None, max_response_ctx=None
    ):
        """
        Executes a query with specified parameters and manages the response.

        This method sets up an OpenAI client using the provided API key and URL, prepares
        messages based on agent preparation and instructions, and sends a chat completion
        request to the OpenAI API. It handles streaming responses, manages token counts,
        and checks for cancellation status via query_state_manager. If the response exceeds
        max_response_ctx tokens or if the query is cancelled, it closes the connection and
        increases the temperature setting. Logging of critical errors and performance metrics
        is also included.

        Args:
            agent_prep (str): Preparation instructions for the agent.
            instructions (list): A list of tuples containing role and content for messages.
            query_state_manager (object): An object managing the state of the query, including
                cancellation status.
            max_response_ctx (int, optional): The maximum number of tokens to allow in the response.
                Defaults to self.ctx if not provided.

        Raises:
            Exception: If an error occurs during the query process or if the connection cannot be
                closed properly.
        """
        if max_response_ctx is None:
            max_response_ctx = self.ctx
        t0 = time.time()
        msg = ""
        completion = None
        try:
            api_key = self.api_key
            if api_key in (None, ""):
                api_key = "none"
            client = OpenAI(
                base_url=self.api_url, api_key=api_key, timeout=self.timeout
            )
            content_str = ""
            if agent_prep:
                messages = [{"role": "user", "content": agent_prep.strip()}]
                content_str = f"{agent_prep.strip()}"
            else:
                agent_prep = ""
                messages = []
            for [role, content] in instructions:
                messages.append({"role": role, "content": f"{content}\n "})
                content_str = f"{content_str}{content}"
            total_tokens = self.get_token_cnt(content_str)
            args = {
                "model": self.model,
                "messages": messages,
                "temperature": round(self.temperature, 2),
                "timeout": self.timeout,
                "stream": True,
            }
            if self.debug_llm_output is True:
                print(
                    f"\nNew Query ({total_tokens:,}/{self.ctx:,} ({max_response_ctx:,}) tokens)"
                )
                if agent_prep:
                    print(agent_prep)
                    print()
                for message in messages:
                    print(message["content"])
                    print()
                print(
                    f"Response ({total_tokens:,}/{self.ctx:,} ({max_response_ctx:,}) tokens):"
                )
            completion = client.chat.completions.create(**args)
            for chunk in completion:
                if chunk and chunk.choices and chunk.choices[0].delta.content:
                    if self.debug_llm_output is True:
                        sys.stdout.write(chunk.choices[0].delta.content)
                        sys.stdout.flush()
                    msg = f"{msg}{chunk.choices[0].delta.content}"
                    msg_len = self.get_token_cnt(msg)
                    if msg_len + total_tokens >= max_response_ctx:
                        try:
                            completion.response.close()
                        except:
                            pass
                        del completion
                        completion = None
                        self.increase_temperature()
                        return
                    if query_state_manager and query_state_manager.is_status_cancelled() is True:
                        try:
                            completion.response.close()
                        except:
                            pass
                        del completion
                        completion = None
                        return
                    yield f"{chunk.choices[0].delta.content}"
        except Exception as e:
            self.logger.critical(f"query: Query failed with {e}")
            msg = ""
            try:
                completion.response.close()
            except:
                pass
            del completion
            completion = None
        elapsed = round(time.time() - t0, 3)
        tkn_cnt = self.get_token_cnt(msg)
        if tkn_cnt > 0 and elapsed > 0:
            tk_rate = round(tkn_cnt / elapsed, 2)
            self.logger.info(
                f"query: took {elapsed:,} seconds for {tkn_cnt:,} tokens received, {tk_rate} token/s"
            )
        else:
            self.increase_temperature()
        return
