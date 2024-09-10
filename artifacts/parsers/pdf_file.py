import time
from pypdf import PdfReader


def identify_pdf(fpath, logger, header=None):
    """
    Identifies whether a file is a PDF by checking its header.

    This function reads the first five bytes of the specified file to check if it starts
    with '%PDF-'. If the header matches, it returns True; otherwise, it returns False.
    Any exceptions encountered during this process are logged using the provided logger.

    Args:
        fpath (str): The path to the file to be checked.
        logger (logging.Logger): A logger instance for logging debug information.
        header (bytes, optional): The pre-read header of the file. If not provided, the
            function reads the first five bytes from the file. Defaults to None.

    Returns:
        bool: True if the file is identified as a PDF, False otherwise.
    """
    try:
        if header is None:
            with open(fpath, "rb") as f:
                header = f.read(5)
        if header.startswith(b"%PDF-"):
            return True
    except Exception as e:
        logger.debug(f"identify_pdf: Raised {e}")
    return False


def parse_pdf(fpath, logger):
    """
    Parses a PDF file and extracts text from its pages.

    This function reads a PDF file from the given path and attempts to extract text from each page.
    It logs any exceptions encountered during the extraction process and returns a list of tuples
    containing the current timestamp and extracted text for each page.

    Args:
        fpath (str): The file path of the PDF to be parsed.
        logger (logging.Logger): A logger object used to log information and errors.

    Returns:
        list: A list of tuples, where each tuple contains a timestamp and the extracted text from a page.

    Raises:
        Exception: If an error occurs during PDF parsing or text extraction.
    """
    result = []
    now = round(time.time(), 3)
    try:
        reader = PdfReader(fpath)
        for page in reader.pages:
            try:
                result.append((now, page.extract_text()))
            except Exception as e:
                logger.info(f"parse_pdf: parsing {fpath} page raised {e}")
    except Exception as e:
        logger.error(f"parse_pdf: Parsing raised {e}")
    return result
