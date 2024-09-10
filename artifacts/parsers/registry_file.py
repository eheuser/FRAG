import calendar
from Registry import Registry
import logging

logger = logging.getLogger("regipy.registry")
logger.addHandler(logging.NullHandler())
import regipy.plugins.system.shimcache

logger = logging.getLogger("regipy.plugins.system.shimcache")
logger.addHandler(logging.NullHandler())
import regipy.plugins.system.bam

logger = logging.getLogger("regipy.plugins.system.bam")
logger.addHandler(logging.NullHandler())
import regipy.plugins.amcache.amcache

logger = logging.getLogger("regipy.plugins.amcache.amcache")
logger.addHandler(logging.NullHandler())
import regipy.plugins.ntuser.user_assist

logger = logging.getLogger("regipy.plugins.ntuser.user_assist")
logger.addHandler(logging.NullHandler())
import regipy.plugins.ntuser.shellbags_ntuser

logger = logging.getLogger("regipy.plugins.ntuser.shellbags_ntuser")
logger.addHandler(logging.NullHandler())
from regipy.registry import RegistryHive
from regipy.plugins.system.shimcache import ShimCachePlugin
from regipy.plugins.system.bam import BAMPlugin
from regipy.plugins.amcache.amcache import AmCachePlugin
from regipy.plugins.ntuser.user_assist import UserAssistPlugin
from regipy.plugins.ntuser.shellbags_ntuser import ShellBagNtuserPlugin
from artifacts.event_filter import is_windows_autorun, references_lol_bin
from utils.utils import format_json_for_llm

RegSZ = Registry.RegSZ
RegExpandSZ = Registry.RegExpandSZ


def identify_reg(fpath, logger, header=None):
    """
    Identifies whether a file is a registry file based on its header.

    This function reads the first four bytes of the specified file to determine if it
    starts with 'regf', indicating that it is a registry file. If the header parameter
    is provided, it uses this instead of reading from the file. The function logs any
    exceptions that occur during the process and returns False if an exception is raised.

    Args:
        fpath (str): The path to the file to be identified.
        logger (logging.Logger): A logger object for logging debug information.
        header (bytes, optional): The first four bytes of the file. If not provided, the
            function reads these bytes from the specified file. Defaults to None.

    Returns:
        bool: True if the file is identified as a registry file, False otherwise.
    """
    try:
        if header is None:
            with open(fpath, "rb") as f:
                header = f.read(4)
        if header.startswith(b"regf"):
            return True
    except Exception as e:
        logger.debug(f"identify_reg: Raised {e}")
    return False


def parse_reg(fpath, logger):
    """
    Parses a registry file and extracts artifacts from an executable file at the given path.

    Args:
        fpath (str): The file path to the registry or executable file.
        logger (logging.Logger): A logger object for logging errors during parsing.

    Returns:
        list: A list of parsed results containing artifacts from the registry and executable.
    """
    result = []
    try:
        reg = Registry.Registry(fpath)
        walk_reg_tree(reg.root(), logger, result)
    except Exception as e:
        logger.error(f"parse_reg: Parsing raised {e}")
    try:
        parse_exe_artifacts(fpath, logger, result)
    except Exception as e:
        logger.error(f"parse_reg: Parsing execution artifacts raised {e}")
    return result


def parse_exe_artifacts(fpath, logger, result):
    """
    Parses executable artifacts from a registry hive file and appends them to a result list.

    This function processes various plugins (AmCachePlugin, BAMPlugin, ShimCachePlugin,
    UserAssistPlugin, ShellBagNtuserPlugin) to extract execution evidence entries from the
    provided registry hive file. Each entry is processed and appended to the result list with a
    timestamp and formatted JSON data. Exceptions are logged at various levels of processing.

    Args:
        fpath (str): The file path to the registry hive.
        logger (logging.Logger): A logger object for logging critical errors.
        result (list): A list to which parsed artifacts will be appended.
    """
    try:
        reg = RegistryHive(fpath)
        try:
            am = AmCachePlugin(reg, as_json=False)
            am.run()
            for entry in am.entries:
                try:
                    utc = entry["timestamp"].timestamp()
                    entry["type"] = "AmCache Evidence of Execution"
                    result.append((utc, format_json_for_llm(entry)))
                except Exception as e:
                    logger.critical(
                        f"parse_exe_artifacts(AmCachePlugin).inner: {e} for {entry}"
                    )
        except Exception as e:
            logger.critical(f"parse_exe_artifacts(AmCachePlugin).outer: {e}")
        try:
            bam = BAMPlugin(reg, as_json=False)
            bam.run()
            for entry in bam.entries:
                try:
                    utc = entry["timestamp"].timestamp()
                    entry["type"] = "Background Activity Monitor Evidence of Execution"
                    result.append((utc, format_json_for_llm(entry)))
                except Exception as e:
                    logger.critical(
                        f"parse_exe_artifacts(BAMPlugin).inner: {e} for {entry}"
                    )
        except Exception as e:
            logger.critical(f"parse_exe_artifacts(BAMPlugin).outer: {e}")
        try:
            sc = ShimCachePlugin(reg, as_json=False)
            sc.run()
            for entry in sc.entries:
                try:
                    utc = entry["last_mod_date"].timestamp()
                    entry["type"] = "ShimCache Evidence of Execution"
                    result.append((utc, format_json_for_llm(entry)))
                except Exception as e:
                    logger.critical(
                        f"parse_exe_artifacts(ShimCachePlugin).inner: {e} for {entry}"
                    )
        except Exception as e:
            logger.critical(f"parse_exe_artifacts(ShimCachePlugin).outer: {e}")
        try:
            ua = UserAssistPlugin(reg, as_json=False)
            ua.run()
            for entry in ua.entries:
                try:
                    utc = entry["timestamp"].timestamp()
                    entry["type"] = "User Assist Evidence of Execution"
                    result.append((utc, format_json_for_llm(entry)))
                except Exception as e:
                    logger.critical(
                        f"parse_exe_artifacts(UserAssistPlugin).inner: {e} for {entry}"
                    )
        except Exception as e:
            logger.critical(f"parse_exe_artifacts(UserAssistPlugin).outer: {e}")
        try:
            sb = ShellBagNtuserPlugin(reg, as_json=False)
            sb.run()
            for entry in sb.entries:
                try:
                    utc = entry["timestamp"].timestamp()
                    entry["type"] = "Shellbags Evidence of Access"
                    result.append((utc, format_json_for_llm(entry)))
                except Exception as e:
                    logger.critical(
                        f"parse_exe_artifacts(ShellBagNtuserPlugin).inner: {e} for {entry}"
                    )
        except Exception as e:
            logger.critical(f"parse_exe_artifacts(ShellBagNtuserPlugin).outer: {e}")
    except Exception as e:
        logger.critical(f"parse_exe_artifacts(outer): {e}")
    return


def walk_reg_tree(key, logger, result):
    """
    Recursively walks a registry tree and processes its values.

    This function traverses the given registry key, processing each value based on its type.
    It checks if any value references 'lol_bin' and appends relevant information to the result
    list if found. The function handles exceptions at multiple levels and logs critical errors.

    Args:
        key (object): The registry key object to process.
        logger (logging.Logger): A logger instance for logging critical errors.
        result (list): A list to store processed registry information as tuples.

    Raises:
        None explicitly raised, but logs critical errors during value processing and recursion.
    """
    if key.values():
        try:
            key_str = str(key.path())
            if is_windows_autorun(key_str):
                key_ts = str(key.timestamp())
                utc = round(float(calendar.timegm(key.timestamp().timetuple())), 3)
                val_tup = []
                lol_bin_seen = False
                for value in key.values():
                    try:
                        value_type_str = value.value_type_str()
                        if value_type_str == "RegSZ" or value_type_str == "RegExpandSZ":
                            value_name = value.name()
                            value_type = value_type_str
                            value_value = value.value()
                            if references_lol_bin(value_value):
                                lol_bin_seen = True
                            val_tup.append(
                                {
                                    "name": value_name,
                                    "type": value_type,
                                    "value": value_value,
                                }
                            )
                        else:
                            value_name = value.name()
                            value_type = value_type_str
                            value_value = value.raw_data().hex()
                            val_tup.append(
                                {
                                    "name": value_name,
                                    "type": value_type,
                                    "value": value_value,
                                }
                            )
                    except Exception as e:
                        logger.critical(f"walk_reg_tree(inner): {e}")
                if lol_bin_seen is True:
                    result.append(
                        (
                            utc,
                            format_json_for_llm(
                                {
                                    "registry_key": key_str,
                                    "last_modified_timestamp": key_ts,
                                    "values": val_tup,
                                }
                            ),
                        )
                    )
        except Exception as e:
            logger.critical(f"walk_reg_tree(outer): {e}")
    for subkey in key.subkeys():
        walk_reg_tree(subkey, logger, result)
