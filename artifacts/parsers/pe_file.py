import pefile
import time
from utils.utils import ret_time, format_json_for_llm


def identify_pe(fpath, logger, header=None):
    """
    Identifies whether a file is a PE (Portable Executable) file.

    This function reads the header of a specified file and checks if it starts with 'MZ',
    indicating that it might be a PE file. If so, it attempts to parse the file using
    pefile.PE. It logs any exceptions encountered during this process.

    Args:
        fpath (str): The path to the file to be checked.
        logger (logging.Logger): A logger instance for logging debug information.
        header (bytes, optional): The pre-read header of the file. If not provided, the
            function reads the header from the file. Defaults to None.

    Returns:
        bool: True if the file is identified as a PE file, False otherwise.
    """
    try:
        if header is None:
            with open(fpath, "rb") as f:
                header = f.read()
        if header.startswith(b"MZ"):
            _ = pefile.PE(data=header)
            return True
    except Exception as e:
        logger.debug(f"identify_pe: Raised {e}")
    return False


def parse_pe(fpath, logger):
    """
    Parses a PE file and extracts information using the provided logger for error handling.

    This function attempts to parse the given PE file at fpath and retrieve relevant
    information. If successful, it formats the extracted data into JSON format suitable for
    LLM (Large Language Model) processing. The function handles exceptions gracefully by
    logging errors and returns a list of tuples containing UTC timestamps and formatted JSON
    data if available.

    Args:
        fpath (str): The file path to the PE file that needs to be parsed.
        logger (Logger): A logging object used for error handling and debugging purposes.

    Returns:
        list of tuples: A list containing tuples with UTC timestamps and formatted JSON data,
                         or an empty list if parsing fails.

    Raises:
        Exception: If any exception occurs during the parsing process, it is caught and logged
                   using the provided logger.
    """
    result = []
    try:
        now = round(time.time(), 3)
        pe = pefile.PE(fpath)
        pe_info = get_pe_information(pe, logger)
        if pe_info:
            utc = pe_info.get("utc", now)
            result = [(utc, format_json_for_llm(pe_info))]
    except Exception as e:
        logger.error(f"parse_pe: Parsing raised {e}")
    return result


def get_pe_information(pe, logger):
    """
    Extracts and logs information from a PE (Portable Executable) file.

    This function attempts to extract various pieces of information from the given PE
    object and stores them in a dictionary. If any exception occurs during the extraction,
    it is logged using the provided logger. The function collects details such as compile
    time, machine type, number of sections, entry point address, image base, image size,
    whether the file is 64-bit or stripped, executable classification, major and minor OS
    versions, imports, exports, section information, and hashes.

    Args:
        pe (PE): The PE object from which to extract information.
        logger (Logger): A logging object used for debugging purposes.

    Returns:
        dict: A dictionary containing the extracted PE information.
    """
    pe_info = {}
    try:
        pe_info["compile_time"] = ret_time(pe.FILE_HEADER.TimeDateStamp)
    except Exception as e:
        logger.debug(f"get_pe_information: PE module caused {e}")
    try:
        pe_info["utc"] = round(pe.FILE_HEADER.TimeDateStamp, 3)
    except Exception as e:
        logger.debug(f"get_pe_information: PE module caused {e}")
    try:
        pe_info["machine_type"] = get_machine_type(pe.FILE_HEADER.Machine)
    except Exception as e:
        logger.debug(f"get_pe_information: PE module caused {e}")
    try:
        pe_info["number_of_sections"] = pe.FILE_HEADER.NumberOfSections
    except Exception as e:
        logger.debug(f"get_pe_information: PE module caused {e}")
    try:
        pe_info["entry_point_address"] = hex(pe.OPTIONAL_HEADER.AddressOfEntryPoint)
    except Exception as e:
        logger.debug(f"get_pe_information: PE module caused {e}")
    try:
        pe_info["image_base"] = hex(pe.OPTIONAL_HEADER.ImageBase)
    except Exception as e:
        logger.debug(f"get_pe_information: PE module caused {e}")
    try:
        pe_info["image_size"] = pe.OPTIONAL_HEADER.SizeOfImage
    except Exception as e:
        logger.debug(f"get_pe_information: PE module caused {e}")
    try:
        pe_info["is_64bit"] = pe.FILE_HEADER.Machine == 34404
    except Exception as e:
        logger.debug(f"get_pe_information: PE module caused {e}")
    try:
        pe_info["is_stripped"] = bool(pe.FILE_HEADER.Characteristics & 8192)
    except Exception as e:
        logger.debug(f"get_pe_information: PE module caused {e}")
    try:
        pe_info["executable_classification"] = get_executable_classification(pe, logger)
    except Exception as e:
        logger.debug(f"get_pe_information: PE module caused {e}")
    try:
        pe_info["major_os"] = pe.OPTIONAL_HEADER.MajorOperatingSystemVersion
    except Exception as e:
        logger.debug(f"get_pe_information: PE module caused {e}")
    try:
        pe_info["minor_os"] = pe.OPTIONAL_HEADER.MinorOperatingSystemVersion
    except Exception as e:
        logger.debug(f"get_pe_information: PE module caused {e}")
    pe_info["imports"] = []
    try:
        for entry in pe.DIRECTORY_ENTRY_IMPORT:
            try:
                library = entry.dll.decode("utf8")
                for imp in entry.imports:
                    try:
                        pe_info["imports"].append(
                            f"{library}.{imp.name.decode('utf8')}"
                        )
                    except Exception as e:
                        logger.debug(f"get_pe_information: PE module caused {e}")
            except Exception as e:
                logger.debug(f"get_pe_information: PE module caused {e}")
    except Exception as e:
        logger.debug(f"get_pe_information: PE module caused {e}")
    pe_info["number_of_imports"] = len(pe_info["imports"])
    try:
        pe_info["number_of_exports"] = len(pe.DIRECTORY_ENTRY_EXPORT)
    except Exception as e:
        logger.debug(f"get_pe_information: PE module caused {e}")
    pe_info["exports"] = []
    try:
        for exp in pe.DIRECTORY_ENTRY_EXPORT.symbols:
            try:
                if not exp.name:
                    name = f"ord{exp.ordinal}"
                else:
                    name = exp.name.decode("utf8")
                pe_info["exports"].append(name)
            except Exception as e:
                logger.debug(f"get_pe_information: PE module caused {e}")
    except Exception as e:
        logger.debug(f"get_pe_information: PE module caused {e}")
    pe_info["number_of_exports"] = len(pe_info["exports"])
    try:
        pass
    except Exception as e:
        logger.debug(f"get_pe_information: PE module caused {e}")
    try:
        pe_info["size_mismatch"] = (
            pe.sections[-1].VirtualAddress + pe.sections[-1].Misc_VirtualSize
            != pe.OPTIONAL_HEADER.SizeOfImage
        )
    except Exception as e:
        logger.debug(f"get_pe_information: PE module caused {e}")
    pe_info["sections"] = []
    try:
        for section in pe.sections:
            try:
                section_info = {}
                try:
                    section_info["name"] = section.Name.decode().rstrip("\x00")
                except Exception as e:
                    logger.debug(f"get_pe_information: PE module caused {e}")
                try:
                    section_info["virtual_address"] = section.VirtualAddress
                except Exception as e:
                    logger.debug(f"get_pe_information: PE module caused {e}")
                try:
                    section_info["virtual_size"] = section.Misc_VirtualSize
                except Exception as e:
                    logger.debug(f"get_pe_information: PE module caused {e}")
                try:
                    section_info["raw_size"] = section.SizeOfRawData
                except Exception as e:
                    logger.debug(f"get_pe_information: PE module caused {e}")
                try:
                    section_info["entropy"] = section.get_entropy()
                except Exception as e:
                    logger.debug(f"get_pe_information: PE module caused {e}")
                try:
                    section_info["md5_hash"] = section.get_hash_md5()
                except Exception as e:
                    logger.debug(f"get_pe_information: PE module caused {e}")
                try:
                    section_info["sha1_hash"] = section.get_hash_sha1()
                except Exception as e:
                    logger.debug(f"get_pe_information: PE module caused {e}")
                try:
                    section_info["sha256_hash"] = section.get_hash_sha256()
                except Exception as e:
                    logger.debug(f"get_pe_information: PE module caused {e}")
                try:
                    section_info["characteristics"] = section.Characteristics
                except Exception as e:
                    logger.debug(f"get_pe_information: PE module caused {e}")
                try:
                    section_info["section_characteristics"] = (
                        get_section_characteristics(section.Characteristics, logger)
                    )
                except Exception as e:
                    logger.debug(f"get_pe_information: PE module caused {e}")
                try:
                    section_info["is_executable"] = bool(
                        section.Characteristics & 536870912
                    )
                except Exception as e:
                    logger.debug(f"get_pe_information: PE module caused {e}")
                try:
                    section_info["is_readable"] = bool(
                        section.Characteristics & 1073741824
                    )
                except Exception as e:
                    logger.debug(f"get_pe_information: PE module caused {e}")
                try:
                    section_info["is_writable"] = bool(
                        section.Characteristics & 2147483648
                    )
                except Exception as e:
                    logger.debug(f"get_pe_information: PE module caused {e}")
                pe_info["sections"].append(section_info)
            except Exception as e:
                logger.debug(f"get_pe_information: Parsing section caused {e}")
    except Exception as e:
        logger.debug(f"get_pe_information: Section iterator caused {e}")
    return pe_info


def get_section_characteristics(characteristics, logger):
    """
    Determines section characteristics based on given bit flags.

    This function evaluates specific bit flags in the characteristics integer to determine
    and append corresponding section characteristics to a list. It logs any exceptions that
    occur during this process using the provided logger.

    Args:
        characteristics (int): An integer representing various bit flags for section
            characteristics.
        logger (logging.Logger): A logger instance used to log debug information in case of
            an exception.

    Returns:
        list: A list of strings representing the determined section characteristics.
    """
    section_characteristics = []
    try:
        if characteristics & 32:
            section_characteristics.append("Code")
        if characteristics & 64:
            section_characteristics.append("Initialized Data")
        if characteristics & 128:
            section_characteristics.append("Uninitialized Data")
        if characteristics & 33554432:
            section_characteristics.append("Execute")
        if characteristics & 67108864:
            section_characteristics.append("Read")
        if characteristics & 134217728:
            section_characteristics.append("Write")
    except Exception as e:
        logger.debug(f"get_section_characteristics: PE module caused {e}")
    return section_characteristics


def get_executable_classification(pe, logger):
    """
    Determines the classification of an executable based on its PE (Portable Executable)
        characteristics.

        This function attempts to classify a given PE object by checking if it is a DLL,
        driver, or EXE. If any exception occurs during this process, it logs the error and
        returns 'Unknown'.

        Args:
            pe (object): The PE object representing the executable file.
            logger (logging.Logger): A logger instance for logging debug information.

        Returns:
            str: The classification of the executable ('Windows DLL', 'Windows Driver',
                'Windows EXE', or 'Unknown').
    """
    try:
        if pe.is_dll():
            return "Windows DLL"
        if pe.is_driver():
            return "Windows Driver"
        if pe.is_exe():
            return "Windows EXE"
    except Exception as e:
        logger.debug(f"get_executable_classification: PE module caused {e}")
    return "Unknown"


def get_machine_type(machine):
    """
    Returns the machine type corresponding to a given machine code.

    This function maps machine codes to their respective machine types using a predefined
    dictionary. If the machine code is not found in the dictionary, it returns the hexadecimal
    representation of the machine code.

    Args:
        machine (int): The machine code for which to retrieve the machine type.

    Returns:
        str: The machine type corresponding to the given machine code or its hexadecimal
            representation if not found in the dictionary.
    """
    machine_types = {
        (0): "Unknown",
        (467): "Matsushita AM33",
        (34404): "x64",
        (448): "ARM little endian",
        (452): "ARMv7 (or higher) Thumb mode only",
        (43620): "ARMv8 in 64-bit mode",
        (450): "EFI byte code",
        (332): "Intel 386 or later processors",
        (512): "Intel Itanium",
        (36929): "Mitsubishi M32R little endian",
        (614): "MIPS16",
        (870): "MIPS with FPU",
        (1126): "MIPS16 with FPU",
        (496): "Power PC little endian",
        (497): "Power PC with floating point support",
        (358): "MIPS little endian",
        (20530): "RISC-V 32-bit",
        (20580): "RISC-V 64-bit",
        (20776): "RISC-V 128-bit",
        (418): "Hitachi SH3",
        (419): "Hitachi SH3 DSP",
        (422): "Hitachi SH4",
        (424): "Hitachi SH5",
        (451): "Thumb",
        (361): "MIPS little-endian WCE v2",
    }
    return machine_types.get(machine, hex(machine))


def get_os_version(major_version, minor_version):
    """
    Returns a human-readable OS version name based on major and minor version numbers.

        This function maps a tuple of (major_version, minor_version) to a corresponding OS version
        name using a predefined dictionary. If the combination is not found in the dictionary,
        it returns 'Unknown'.

        Args:
            major_version (int): The major version number of the operating system.
            minor_version (int): The minor version number of the operating system.

        Returns:
            str: A human-readable string representing the OS version name or 'Unknown' if the
                combination is not found in the dictionary.
    """
    os_versions = {
        (0, 0): "Unknown",
        (1, 0): "Windows 1.0",
        (2, 0): "Windows 2.0",
        (2, 10): "Windows 2.1x",
        (3, 0): "Windows 3.0",
        (3, 10): "Windows NT 3.1",
        (3, 50): "Windows NT 3.5",
        (3, 51): "Windows NT 3.51",
        (4, 0): "Windows 95",
        (4, 10): "Windows 98",
        (4, 90): "Windows Me",
        (5, 0): "Windows 2000",
        (5, 1): "Windows XP",
        (5, 2): "Windows Server 2003 / Windows XP 64-bit Edition",
        (6, 0): "Windows Vista / Windows Server 2008",
        (6, 1): "Windows 7 / Windows Server 2008 R2",
        (6, 2): "Windows 8 / Windows Server 2012",
        (6, 3): "Windows 8.1 / Windows Server 2012 R2",
        (10, 0): "Windows 10 / Windows Server 2016 / Windows Server 2019",
    }
    return os_versions.get((major_version, minor_version), "Unknown")
