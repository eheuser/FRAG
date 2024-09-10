import hashlib
import re
import os

from artifacts.parsers.pdf_file import identify_pdf, parse_pdf
from artifacts.parsers.pe_file import identify_pe, parse_pe
from artifacts.parsers.mft_file import identify_mft, parse_mft
from artifacts.parsers.registry_file import identify_reg, parse_reg
from artifacts.parsers.evtx_file import identify_evtx, parse_evtx


class ArtifactParser:
    def __init__(self, logger):
        self.logger = logger
        self.artifact_parsers = {
            "PDF File": (identify_pdf, parse_pdf),
            "Windows PE File": (identify_pe, parse_pe),
            "Windows Master File Table": (identify_mft, parse_mft),
            "Windows Registry File": (identify_reg, parse_reg),
            "Windows EVTX File": (identify_evtx, parse_evtx),
        }

    def parse_file(self, fpath, original_fpath=None):
        """
        Parses a file and extracts its contents based on identified artifact parsers.

        This method attempts to parse a given file using various artifact parsers, logging any
        exceptions that occur during the process. It updates the file information with the
        detected file type and returns the parsed content along with other relevant data.

        Args:
            fpath (str): The path of the file to be parsed.
            original_fpath (str, optional): The original path of the file if different from fpath.

        Returns:
            tuple: A tuple containing the updated file information, strings, and contents. If an
                   exception occurs during parsing, it returns None for all three elements.
        """
        contents = []
        try:
            file_info, strings, header = self.get_file_info(fpath, original_fpath)
        except Exception as e:
            self.logger.critical(f"parse_file: Parsing file info raised {e}, skipping")
            return None, None, None
        file_type_string = "Binary File"
        for file_type, (identifier, parser) in self.artifact_parsers.items():
            try:
                if identifier(fpath, self.logger, header=header) is True:
                    try:
                        contents = parser(fpath, self.logger)
                        file_type_string = file_type
                        break
                    except Exception as e:
                        self.logger.error(f"parse_file: Parser {parser} raised {e}")
            except Exception as e:
                self.logger.error(f"parse_file: Identifier {identifier} raised {e}")
        # Remove uploaded file
        try:
            os.remove(fpath)
        except Exception as e:
            self.logger.error(f"parse_file: Deleting {fpath} raised {e}")
        file_info["file_type"] = file_type_string
        return file_info, strings, contents

    def get_file_info(self, fpath, original_fpath=None):
        """

        Retrieves information about a file including its size and hash values.

        This method reads the specified file in chunks to calculate MD5, SHA1, and SHA256
        hashes, as well as the total file size. It also extracts strings from the initial
        portion of the file header.

        Args:
            fpath (str): The path to the file for which information is to be retrieved.
            original_fpath (str, optional): The original file path if different from fpath.
                Defaults to None.

        Returns:
            tuple: A tuple containing a dictionary with file information (file path, size, MD5,
                   SHA1, and SHA256 hashes), extracted strings from the header, and the
                   header itself.
        """
        if original_fpath is None:
            original_fpath = fpath
        blocksize = 1024 * 1024
        with open(fpath, "rb") as f:
            header = f.read(blocksize * 4)
            f.seek(0)
            md5 = hashlib.md5()
            sha1 = hashlib.sha1()
            sha256 = hashlib.sha256()
            file_sz = 0
            while True:
                buf = f.read(blocksize)
                if not buf:
                    break
                md5.update(buf)
                sha1.update(buf)
                sha256.update(buf)
                file_sz += len(buf)
        file_info = {
            "filepath": original_fpath,
            "file_size": file_sz,
            "MD5": str(md5.hexdigest()),
            "SHA1": str(sha1.hexdigest()),
            "SHA256": str(sha256.hexdigest()),
        }
        strings = "\n".join(self.get_file_strings(header))
        return file_info, strings, header

    def get_file_strings(self, bin, max_bytes=65536):
        """
        Retrieves strings from a binary file up to a specified maximum number of bytes.

        This function attempts to decode the binary data as UTF-8 text and splits it into lines.
        If decoding fails due to UnicodeDecodeError, it searches for non-control character sequences
        in the binary data using a regular expression pattern and returns those sequences up to the
        specified maximum number of bytes. Any exceptions encountered during this process are logged,
        and an empty list is returned if any error occurs.

        Args:
            bin (bytes): The binary data from which to extract strings.
            max_bytes (int, optional): The maximum number of bytes to consider for string extraction.
                Defaults to 65536.

        Returns:
            list: A list of strings extracted from the binary data or an empty list if any error occurs.
        """
        try:
            try:
                text = bin.decode("utf-8")
                if len(text.encode("utf-8")) > max_bytes:
                    cut_text = text[:max_bytes].encode("utf-8")
                    text = cut_text.decode("utf-8", errors="ignore")
                return text.split("\n")
            except UnicodeDecodeError:
                pattern = re.compile(b"[^\x00-\x1f\x7f-\xff]{8,}")
                max_mb = 4 * 1024 * 1024
                strings = pattern.findall(bin[:max_mb])
                result = []
                total_length = 0
                for s in strings:
                    s_length = len(s)
                    if total_length + s_length > max_bytes:
                        s = s[: max_bytes - total_length]
                        result.append(s.decode("utf-8", errors="ignore"))
                        break
                    result.append(s.decode("utf-8", errors="ignore"))
                    total_length += s_length
                return result
        except Exception as e:
            self.logger.info(f"get_file_strings: Failed with {e}")
            return []
