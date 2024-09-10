import threading
from utils.utils import read_llm_config, write_llm_config


def update_config(new_config, logger):
    """
    Updates the configuration with new settings and logs any exceptions that occur during
    the process.

    This function reads the current LLM configuration, updates it with the provided new
    configuration, writes the updated configuration back, and returns a response indicating
    success or failure. If an exception occurs, it is logged as critical and returned in
    the response.

    Args:
        new_config (dict): A dictionary containing the new configuration settings to be
            applied.
        logger (logging.Logger): The logger object used for logging messages and exceptions.

    Returns:
        dict: A dictionary with a 'response' key indicating the result of the operation,
             either 'OK' or an exception message.
    """
    try:
        old_config = read_llm_config(logger)
        for key, value in new_config.items():
            old_config[key] = value
        write_llm_config(old_config, logger)
        return {"response": "OK"}
    except Exception as e:
        logger.critical(f"update_config: Raised {e}")
        return {"response": f"{e}"}


def get_artifact_files(frag, logger):
    """
    Retrieves artifact files from a fragment and handles exceptions.

    This function attempts to retrieve artifact files by calling the method
    get_artifact_files on the provided fragment object. If an exception occurs, it logs
    the error at a critical level using the provided logger and returns a response with
    the exception message.

    Args:
        frag (object): The fragment object from which to retrieve artifact files.
        logger (logging.Logger): A logger instance for logging critical errors.

    Returns:
        dict: A dictionary containing the response, either the result of get_artifact_files
              or an error message if an exception occurred.
    """
    try:
        return {"response": frag.get_artifact_files()}
    except Exception as e:
        logger.critical(f"get_artifact_files: Raised {e}")
        return {"response": f"{e}"}


def monitor_parse_progress(artifact_state_manager, logger):
    """
    Monitors and parses progress of an artifact state manager.

    This function attempts to retrieve the status from the provided artifact state manager
    and returns it as a response dictionary. If any exception occurs during the process,
    it logs the error at a critical level and returns the exception message in the response
    dictionary.

    Args:
        artifact_state_manager (object): The object managing the state of the artifacts.
        logger (logging.Logger): A logger instance for logging critical errors.

    Returns:
        dict: A dictionary containing the status or error message under the key 'response'.
    """
    try:
        return {"response": artifact_state_manager.get_status()}
    except Exception as e:
        logger.critical(f"monitor_parse_progress: Raised {e}")
        return {"response": f"{e}"}


def delete_vector_db(frag, logger):
    """
    Deletes and reconnects to a vector database.

    This function attempts to drop the existing database connection and then re-establish it.
    If an exception occurs during these operations, it logs the error as critical and returns
    a response containing the exception message. Otherwise, it returns a success response.

    Args:
        frag (object): An object with methods for managing the vector database.
        logger (logging.Logger): A logger instance to record critical errors.

    Returns:
        dict: A dictionary containing either an error message or 'OK' indicating successful
              operation.
    """
    try:
        frag.drop_db()
        frag.connect_db()
    except Exception as e:
        logger.critical(f"delete_vector_db: raised {e}")
        return {"response": f"{e}"}
    return {"response": "OK"}


def parse_upload_folder(frag, artifact_state_manager, logger):
    """
    Parses an upload folder using a separate thread.

    This function starts a new thread to parse the upload folder with the given fragment,
    artifact state manager, and logger. The parsing process is handled by the target
    function _parse_upload_folder.

    Args:
        frag (Any): The fragment to be parsed.
        artifact_state_manager (Any): The manager responsible for handling the state of
            artifacts during the parsing process.
        logger (logging.Logger): A logger instance used for logging messages and errors
            during the parsing process.
    """
    _ = threading.Thread(
        target=_parse_upload_folder, args=(frag, artifact_state_manager, logger)
    ).start()


def _parse_upload_folder(frag, artifact_state_manager, logger):
    """
    Parses files from an upload folder and updates their status in the artifact state manager.

    This function retrieves the current status of files from the artifact state manager,
    processes each file that is queued by adding it to a fragment (frag), logs the number
    of events parsed, marks the file as done, and then deletes the processed files.

    Args:
        frag (object): The object responsible for handling file additions.
        artifact_state_manager (object): Manages the status of artifacts and their processing.
        logger (logging.Logger): A logger instance to log information during processing.

    Returns:
        None
    """
    work_q = artifact_state_manager.get_status()
    processed_files = []
    for filepath, status in work_q.items():
        if status["status"] == "queued":
            artifact_state_manager.mark_file_in_progress(filepath)
            pages_added = frag.add_file(filepath)
            logger.info(
                f"_parse_upload_folder: Parsed {pages_added:,} events from {filepath}"
            )
            artifact_state_manager.mark_file_done(filepath)
            processed_files.append(filepath)
    for f in processed_files:
        artifact_state_manager.mark_file_deleted(f)
    return
