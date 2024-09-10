from mft import PyMftParser, PyMftAttributeX10, PyMftAttributeX30
import json
from artifacts.event_filter import filter_mft_path
from utils.utils import ts_to_utc, format_json_for_llm


def identify_mft(fpath, logger, header=None):
    """
    Identifies whether a file has an MFT header.

    This function reads the first five bytes of a file to check if it starts with 'FILE0',
    indicating that it is likely an MFT (Master File Table) file. If no header is provided,
    the function opens the file and reads the first five bytes itself. Any exceptions
    encountered during this process are logged as debug messages.

    Args:
        fpath (str): The path to the file that needs to be checked for an MFT header.
        logger (logging.Logger): A logger object used to log debug messages if any exception
            occurs.
        header (bytes, optional): The first five bytes of the file. If not provided, the
            function reads these bytes from the file specified by fpath. Defaults to None.

    Returns:
        bool: True if the file starts with 'FILE0', indicating it is likely an MFT file;
                False otherwise.
    """
    try:
        if header is None:
            with open(fpath, "rb") as f:
                header = f.read(5)
        if header.startswith(b"FILE0"):
            return True
    except Exception as e:
        logger.debug(f"identify_mft: Raised {e}")
    return False


def parse_mft(fpath, logger):
    """
    Parses an MFT file and extracts relevant information into a list of tuples.

    This function reads an MFT file from the given path using PyMftParser, processes each entry
    to gather detailed file information, and formats this data for further analysis. It handles
    exceptions gracefully by logging errors and continues processing other entries.

    Args:
        fpath (str): The file path of the MFT file to be parsed.
        logger (logging.Logger): A logger instance used for logging errors and information during
            parsing.

    Returns:
        list: A list of tuples containing formatted JSON data extracted from the MFT entries.

    Raises:
        Exception: If an error occurs during file parsing or processing, it is logged but not
            raised to allow continued execution.
    """
    result = []
    try:
        parser = PyMftParser(fpath)
        file_info_dict = {}
        for entry_or_error in parser.entries():
            if isinstance(entry_or_error, RuntimeError):
                del entry_or_error
                continue
            file_info_dict[entry_or_error.entry_id] = get_info_dict_entry(
                entry_or_error
            )
        del parser
        parser = PyMftParser(fpath)
        for entry_or_error in parser.entries_json():
            try:
                if isinstance(entry_or_error, RuntimeError) or entry_or_error is None:
                    continue
                entry = json.loads(entry_or_error)
                total_lsz = 0
                total_psz = 0
                base_entry_id = entry["header"]["base_reference"]["entry"]
                base_entry_sequence = entry["header"]["base_reference"]["sequence"]
                entry_id = entry["header"]["record_number"]
                if entry_id in file_info_dict:
                    info_dict = json.loads(file_info_dict[entry_id])
                    del file_info_dict[entry_id]
                else:
                    info_dict = {}
                file_size = info_dict.get("file_size", "")
                flags = info_dict.get("flags", [])
                full_path = info_dict.get("full_path", "")
                if "/" in full_path:
                    full_path = full_path.replace("/", "\\")
                directory = info_dict.get("directory", "")
                extension = info_dict.get("extension", "")
                hard_link_count = entry["header"]["hard_link_count"]
                sequence = entry["header"]["sequence"]
                total_entry_size = entry["header"]["total_entry_size"]
                used_entry_size = entry["header"]["used_entry_size"]
                si_file_flags = info_dict.get("si_file_flags", [])
                si_owner_id = 0
                si_m = ""
                si_a = ""
                si_c = ""
                si_e = ""
                fn_flags = info_dict.get("fn_flags", [])
                fn_name = info_dict.get("fn_name", "")
                fn_logical_size = 0
                fn_physical_size = 0
                fn_m = ""
                fn_a = ""
                fn_c = ""
                fn_e = ""
                utc = 0.0
                for attribute in entry["attributes"]:
                    if attribute["header"]["type_code"] == "StandardInformation":
                        si_owner_id = attribute["data"]["owner_id"]
                        si_m = attribute["data"]["modified"]
                        si_a = attribute["data"]["accessed"]
                        si_c = attribute["data"]["created"]
                        si_e = attribute["data"]["mft_modified"]
                    elif attribute["header"]["type_code"] == "FileName":
                        fn_logical_size = attribute["data"]["logical_size"]
                        fn_physical_size = attribute["data"]["physical_size"]
                        fn_m = attribute["data"]["modified"]
                        fn_a = attribute["data"]["accessed"]
                        fn_c = attribute["data"]["created"]
                        fn_e = attribute["data"]["mft_modified"]
                        total_lsz += fn_logical_size
                        total_psz += fn_physical_size
                        utc = ts_to_utc(fn_c)
                if utc == 0.0:
                    continue
                if filter_mft_path(full_path) is False:
                    continue
                result.append(
                    (
                        utc,
                        format_json_for_llm(
                            {
                                "base_entry_id": base_entry_id,
                                "base_entry_sequence": base_entry_sequence,
                                "entry_id": entry_id,
                                "file_size": file_size,
                                "flags": flags,
                                "directory": directory,
                                "full_path": full_path,
                                "hard_link_count": hard_link_count,
                                "sequence": sequence,
                                "total_entry_size": total_entry_size,
                                "used_entry_size": used_entry_size,
                                "si_file_flags": si_file_flags,
                                "si_owner_id": si_owner_id,
                                "si_m": si_m,
                                "si_a": si_a,
                                "si_c": si_c,
                                "si_e": si_e,
                                "fn_flags": fn_flags,
                                "fn_name": fn_name,
                                "extension": extension,
                                "fn_logical_size": fn_logical_size,
                                "fn_physical_size": fn_physical_size,
                                "fn_m": fn_m,
                                "fn_a": fn_a,
                                "fn_c": fn_c,
                                "fn_e": fn_e,
                            }
                        ),
                    )
                )
            except Exception as e:
                logger.info(f"parse_mft: Parsing {fpath} page raised {e}")
    except Exception as e:
        logger.error(f"parse_mft: Parsing raised {e}")
    return result


def get_info_dict_entry(entry_or_error):
    """
    Extracts and formats information from an entry or error object into a JSON dictionary.

    This function processes the given entry_or_error object to extract various attributes
    such as file size, flags, full path, directory, filename, and extension. It handles
    different types of attribute content and constructs a JSON string with the extracted
    information. The function also ensures that paths are formatted correctly for Windows
    environments by replacing forward slashes with backslashes.

    Args:
        entry_or_error (object): An object containing attributes to be processed, such as
            file size, flags, full path, and other resident content.

    Returns:
        str: A JSON string representing a dictionary of extracted information including
            file size, flags, directory, full path, si_file_flags, fn_flags, fn_name, and
            extension.
    """
    file_size = entry_or_error.file_size
    flags = str(entry_or_error.flags).split(" | ")
    full_path = str(entry_or_error.full_path)
    if "/" in full_path:
        full_path = full_path.replace("/", "\\")
    si_file_flags = []
    fn_flags = []
    fn_name = ""
    for attribute_or_error in entry_or_error.attributes():
        if isinstance(attribute_or_error, RuntimeError):
            continue
        resident_content = attribute_or_error.attribute_content
        if resident_content:
            if isinstance(resident_content, PyMftAttributeX10):
                si_file_flags = str(resident_content.file_flags).split(" | ")
            if isinstance(resident_content, PyMftAttributeX30):
                fn_flags = str(resident_content.flags).split(" | ")
                fn_name = resident_content.name
        del resident_content
        del attribute_or_error
    if "\\" in full_path:
        directory = full_path.rsplit("\\", 1)[0]
    else:
        directory = ""
    if "." in fn_name:
        extension = fn_name.rsplit(".", 1)[-1]
    else:
        extension = ""
    return json.dumps(
        {
            "file_size": file_size,
            "flags": flags,
            "directory": directory,
            "full_path": full_path,
            "si_file_flags": si_file_flags,
            "fn_flags": fn_flags,
            "fn_name": fn_name,
            "extension": extension,
        }
    )
