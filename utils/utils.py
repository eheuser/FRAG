import datetime
import os
import json
import re
import ciso8601

EPOCH = datetime.datetime.utcfromtimestamp(0)


def ret_time(t):
    """
    Converts a Unix timestamp to a formatted date and time string.

    This function takes an integer representing a Unix timestamp and converts it to a
    UTC datetime object. It then formats the datetime object into a string with the format
    '%m/%d/%Y %H:%M:%S'.

    Args:
        t (int): The Unix timestamp to convert.

    Returns:
        str: A formatted date and time string in the format 'MM/DD/YYYY HH:MM:SS'.
    """
    return datetime.datetime.utcfromtimestamp(int(t)).strftime("%m/%d/%Y %H:%M:%S")


def chunk_list(long_list, _max_chunk):
    """
    Splits a list into chunks of specified size.

        This function takes a long list and splits it into smaller lists (chunks) of a given
        maximum size. It raises an exception if the input is not a list. The function uses a
        generator to yield each chunk, allowing for efficient iteration over large lists without
        consuming excessive memory.

        Args:
            long_list (list): The list to be split into chunks.
            _max_chunk (int or str): The maximum size of each chunk. This value is converted to an
                integer before processing.

        Yields:
            list: A chunk of the original list with a length up to max_chunk.

        Raises:
            ValueError: If long_list is not a list.
    """
    max_chunk = int(_max_chunk)
    if not (long_list, list):
        raise ValueError
    for i in range(0, len(long_list), max_chunk):
        yield long_list[i : i + max_chunk]


def split_string_into_n_parts(s, n):
    """
    Splits a given string into n parts of approximately equal size.

        This function divides the input string s into n parts such that each part has an
        approximately equal number of characters. It handles cases where the length of the
        string is not evenly divisible by n, distributing extra characters among the first
        few parts.

        Args:
            s (str): The input string to be split.
            n (int): The number of parts into which the string should be divided.

        Returns:
            list: A list containing n substrings, each being a part of the original string.
    """
    length = len(s)
    part_size = length // n
    remainder = length % n
    parts = []
    start = 0
    for i in range(n):
        end = start + part_size + (1 if i < remainder else 0)
        parts.append(s[start:end])
        start = end
    return parts


def read_llm_config(logger):
    """
    Reads and returns the LLM configuration from a JSON file.

    This function attempts to read the configuration settings for an LLM (Large Language
    Model) from a specified JSON file. If the file exists, it reads and parses the
    contents into a dictionary. In case of any exceptions during reading or parsing, it
    logs the error using the provided logger and returns a default configuration.

    Args:
        logger (logging.Logger): The logger to use for logging errors.

    Returns:
        dict: A dictionary containing the LLM configuration settings.

    Raises:
        None
    """
    config = {
        "api_url": "",
        "api_key": "",
        "model": "",
        "context": 0,
        "timeout": 0.0,
        "temperature": 0.0,
        "debug": False,
    }
    config_path = "config/config.json"
    if os.path.isfile(config_path) is True:
        try:
            with open(config_path, "r") as f:
                config = json.loads(f.read())
        except Exception as e:
            logger.error(f"read_llm_config: Raised {e}, loading default config")
    return config


def write_llm_config(config, logger):
    """
    Writes LLM configuration to a file.

    This function writes the given configuration to a JSON file at the specified path. It
    handles exceptions and logs any errors that occur during the writing process.

    Args:
        config (dict): The configuration data to be written to the file.
        logger (logging.Logger): A logger object for logging error messages.

    Raises:
        Exception: If an exception occurs while opening or writing to the file.
    """
    config_path = "config/config.json"
    try:
        with open(config_path, "w") as f:
            f.write(json.dumps(config, indent=2))
    except Exception as e:
        logger.error(f"write_llm_config: Raised {e}")
    return


def read_prompt(query_name):
    """
    Reads a prompt from a file based on the given query name.

    This function constructs a path to a prompt file using the provided query name and
    checks if the file exists. If it does, the function opens the file, reads its content,
    and returns it as a string. If the file does not exist, an empty string is returned.

    Args:
        query_name (str): The name of the query used to construct the path to the prompt
            file.

    Returns:
        str: The content of the prompt file if it exists, otherwise an empty string.
    """
    card_path = f"prompts/{query_name}.prompt"
    if os.path.isfile(card_path):
        with open(card_path, "r") as f:
            return f.read()
    return ""


def indent_string(text, spaces=4):
    """
    Indents a given string by adding spaces to each line.

    This function takes a multi-line string and indents each line by a specified number of
    spaces. It splits the input text into lines, prepends the specified number of spaces to
    each line, and then joins them back together with newline characters.

    Args:
        text (str): The original multi-line string to be indented.
        spaces (int, optional): The number of spaces to indent each line. Default is 4.

    Returns:
        str: The indented string with the specified number of spaces added to each line.
    """
    delim = " " * spaces
    ret_list = []
    string_list = text.split("\n")
    for s in string_list:
        ret_list.append(f"{delim}{s}")
    return "\n".join(ret_list)


def remove_markdown(_text):
    """
    Removes markdown formatting from a given text.

    This function takes a string with markdown formatting and removes various markdown elements
    such as code blocks, images, links, strikethroughs, inline code, headers, horizontal rules,
    blockquotes, unordered lists, ordered lists, and bold/italic emphasis. The cleaned text is
    then returned without any leading or trailing whitespace.

    Args:
        _text (str): The input text containing markdown formatting to be removed.

    Returns:
        str: The cleaned text with all specified markdown elements removed.
    """
    text = f"{_text}"
    text = text.replace("```\n", "")
    text = text.replace("```", "")
    text = re.sub("!\\[.*?\\]\\(.*?\\)", "", text)
    text = re.sub("\\[([^\\[]+)\\]\\((.*?)\\)", "\\1", text)
    text = re.sub("~~(.*?)~~", "\\1", text)
    text = re.sub("`{1,3}(.+?)`{1,3}", "\\1", text)
    text = re.sub("```[\\s\\S]*?```", "", text)
    text = re.sub("#{1,6}\\s*(.*)", "\\1", text)
    text = re.sub("([-*_]){3,}", "", text)
    text = re.sub("^>\\s?", "", text, flags=re.MULTILINE)
    text = re.sub("^\\s*[-+*]\\s+", "", text, flags=re.MULTILINE)
    text = re.sub("^\\s*\\d+\\.\\s+", "", text, flags=re.MULTILINE)
    return text.strip()


def format_json_for_llm(data, indent=0):
    """
    Formats JSON data into a human-readable string with specified indentation.

    This function takes a JSON object and recursively formats it into a string with the
    given indentation level. It handles dictionaries, lists, and other types of values,
    ensuring that each key-value pair is properly indented and formatted for readability.

    Args:
        data (dict or list): The JSON data to be formatted. This can be a dictionary or a
            list containing nested dictionaries or lists.
        indent (int, optional): The number of spaces used for indentation. Defaults to 0.

    Returns:
        str: A human-readable string representation of the JSON data with the specified
            indentation level.
    """

    def format_item(key, value, indent):
        """
        Formats a key-value pair into a formatted string with specified indentation.

            This function takes a key and its corresponding value, along with an indent level,
            and formats them into a string. If the value is a dictionary or list, it recursively
            formats each item with additional indentation. Otherwise, it simply converts the value
            to a string.

            Args:
                key (str): The key for the formatted string.
                value (dict, list, str): The value corresponding to the key. It can be a dictionary,
                    list, or any other type that can be converted to a string.
                indent (int): The level of indentation for the formatted string.

            Returns:
                str: A formatted string representing the key-value pair with specified indentation.
        """
        formatted_str = " " * indent + f"{key}: "
        if isinstance(value, dict):
            formatted_str += "\n" + format_json_for_llm(value, indent + 2)
        elif isinstance(value, list):
            formatted_str += "\n" + "\n".join(
                [format_json_for_llm(item, indent + 2) for item in value]
            )
        else:
            formatted_str += str(value)
        return formatted_str

    if isinstance(data, dict):
        return "\n".join([format_item(k, v, indent) for k, v in data.items()])
    elif isinstance(data, list):
        return "\n".join([format_json_for_llm(item, indent) for item in data])
    else:
        return " " * indent + str(data)


def ts_to_utc(dtg):
    """
    Converts a timestamp to UTC and returns it as a float representing seconds since epoch.

    This function attempts to clean up the input datetime string by removing any timezone
    information or offsets, then parses it using ciso8601. If parsing fails, it appends 'Z'
    to indicate UTC and retries parsing. The resulting naive datetime is converted to a
    float representing seconds since epoch. If any exception occurs during the process,
    it returns 0.0.

    Args:
        dtg (str): A string representing the datetime to be converted.

    Returns:
        float: The number of seconds since epoch for the given datetime, or 0.0 if an error
            occurs.
    """
    try:
        try:
            idx = dtg.index(" +")
            dtg = dtg[0:idx]
        except ValueError:
            pass
        try:
            idx = dtg.index(" UTC")
            dtg = dtg[0:idx]
        except ValueError:
            pass
        try:
            idx = dtg.index("+00:00")
            dtg = dtg[0:idx]
        except ValueError:
            pass
        try:
            _dtg = ciso8601.parse_datetime_as_naive(dtg)
        except ValueError:
            dtg = f"{dtg}Z"
            _dtg = ciso8601.parse_datetime_as_naive(dtg)
        return round((_dtg - EPOCH).total_seconds(), 6)
    except Exception as e:
        return 0.0


def trunc_sysmon_event(text):
    """
    Truncates a system monitoring event text based on specific keys.

    This function checks if the input text contains 'Microsoft-Windows-Sysmon/Operational'.
    If it does, it extracts lines that start with any of the specified keys and joins them
    into a new truncated event text. Otherwise, it returns the original text unchanged.

    Args:
        text (str): The input text containing system monitoring events.

    Returns:
        str: The truncated event text if the input contains 'Microsoft-Windows-Sysmon/Operational',
             otherwise the original text.
    """
    if "Microsoft-Windows-Sysmon/Operational" in text:
        keys = (
            "Channel",
            "EventID",
            "SystemTime",
            "User",
            "UtcTime",
            "CommandLine",
            "Image",
            "IntegrityLevel",
            "LogonId",
            "OriginalFileName",
            "ParentCommandLine",
            "ParentImage",
            "SourceIp",
            "SourcePort",
            "DestinationIp",
            "DestinationPort",
            "DestinationHostname",
            "SourceImage",
            "TargetImage",
            "StartModule",
            "StartFunction",
            "GrantedAccess",
            "CallTrace",
            "TargetObject",
            "EventType",
            "Details",
            "EventNamespace",
            "Name",
            "Query",
            "Type",
            "Destination",
            "Consumer",
            "Filter",
        )
        new_event = []
        lines = text.split("\n")
        for _line in lines:
            line = _line.strip(" \t")
            if line.startswith(keys):
                new_event.append(line)
        return "\n".join(new_event)
    else:
        return text


def obj_cp(obj):
    """
    Serializes and deserializes an object using JSON.

    This function takes an object as input, serializes it to a JSON formatted string,
    and then immediately deserializes it back into a Python object. The purpose of this
    operation is typically to create a deep copy of the original object.

    Args:
        obj (object): The object to be serialized and deserialized.

    Returns:
        object: A new object that is a deep copy of the input object.
    """
    return json.loads(json.dumps(obj))
