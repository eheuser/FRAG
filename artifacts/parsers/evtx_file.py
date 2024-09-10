import json
from evtx import PyEvtxParser
from artifacts.event_filter import filter_evtx_event
from utils.utils import format_json_for_llm


def identify_evtx(fpath, logger, header=None):
    """
    Identifies whether a file is an EVTX file by checking its header.

    This function reads the first 7 bytes of the specified file to check if it starts with
    'ElfFile'. If the header matches, it returns True; otherwise, it returns False. Any
    exceptions encountered during this process are logged using the provided logger.

    Args:
        fpath (str): The path to the file to be checked.
        logger (logging.Logger): A logger object for logging debug information.
        header (bytes, optional): The pre-read header of the file. If not provided, the
            function reads the first 7 bytes from the file. Defaults to None.

    Returns:
        bool: True if the file is identified as an EVTX file, False otherwise.
    """
    try:
        if header is None:
            with open(fpath, "rb") as f:
                header = f.read(7)
        if header.startswith(b"ElfFile"):
            return True
    except Exception as e:
        logger.debug(f"identify_evtx: Raised {e}")
    return False


def parse_evtx(fpath, logger):
    """
    Parses an EVTX file and extracts relevant events.

    This function reads an EVTX file from a given path and uses PyEvtxParser to parse the
    records. It filters and formats the parsed events, appending them to a result list if they
    meet certain criteria. Exceptions during parsing are logged but do not stop the process.

    Args:
        fpath (str): The file path of the EVTX file to be parsed.
        logger (logging.Logger): A logger instance for logging errors and exceptions.

    Returns:
        list: A list of tuples, each containing a UTC timestamp and formatted event data.
    """
    result = []
    try:
        parser = PyEvtxParser(fpath)
        for record in parser.records_json():
            try:
                if "data" in record:
                    data = json.loads(record["data"])
                    event, utc = filter_evtx_event(data)
                    if event:
                        result.append((utc, format_json_for_llm(event)))
            except Exception as e:
                logger.info(f"parse_evtx: parsing {fpath} page raised {e}")
    except Exception as e:
        logger.error(f"parse_evtx: Parsing raised {e}")
    return result
