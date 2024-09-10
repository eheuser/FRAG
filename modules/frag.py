import time
import threading
import shutil
from ioc.ioc import IOC
from modules.vdb import VectorDB
from artifacts.file_parser import ArtifactParser
from utils.utils import chunk_list


class FRAG(object):

    def __init__(self, logger, instance_name="default"):
        self.logger = logger
        self.instance_name = instance_name
        self.data_path = f"data/FRAG_INDEX_{self.instance_name}"
        self.lock = threading.RLock()
        self.connect_db()

    def connect_db(self):
        """
        Connects to a VectorDB and initializes it if it is new.

        This method sets up a connection to a VectorDB using the provided logger and data path. If
        the database is newly created, it calls the add_iocs method to populate it with initial
        data.

        Args:
            self (object): The instance of the class containing this method.

        Raises:
            Exception: If an error occurs during the connection or initialization process.
        """
        self.vdb = VectorDB(self.logger, data_path=self.data_path)
        if self.vdb.is_new_db() is True:
            self.add_iocs()
        return True

    def drop_db(self):
        """
        Drops the database and closes the connection.

        This method acquires a lock to ensure thread safety while dropping the database. It then
        closes the database connection and deletes the reference to the virtual database (vdb).
        """
        with self.lock:
            self.vdb.drop_db()
            self.vdb.close()
            del self.vdb
        return True

    def query(self, query_dict, prompts=False):
        """
        Executes a query on the database with the given parameters and optional prompts.

        This method acquires a lock to ensure thread safety while executing the query. It
        delegates the actual query execution to the vdb object's query method, passing
        along the provided dictionary and prompt flag.

        Args:
            query_dict (dict): The dictionary containing the query parameters.
            prompts (bool, optional): A flag indicating whether to include prompts in the
                query execution. Default is False.

        Returns:
            The result of the query executed by the vdb object's query method.
        """
        with self.lock:
            return self.vdb.query(query_dict, prompts)

    def count_tokens(self, text):
        """
        Counts tokens in a given text while ensuring thread safety.

        This method acquires a lock to ensure that only one thread can count the tokens at a time.
        It then delegates the token counting task to an internal method or object self.vdb.

        Args:
            text (str): The input text whose tokens are to be counted.

        Returns:
            int: The number of tokens in the given text.
        """
        with self.lock:
            return self.vdb.count_tokens(text)

    def add_iocs(self):
        """
        Adds Indicators of Compromise (IOC) to a database.

        This method retrieves IOC data and formats it into pages, which are then added to a
        database with associated metadata. The number of pages added is returned as the result.

        Returns:
            int: The number of pages added to the database.
        """
        now = round(time.time(), 3)
        obj = IOC()
        ioc = obj.get_ioc_dict()
        ioc_list = []
        meta_list = []
        for tid, tobj in ioc.items():
            name = tobj.get("name")
            description = tobj.get("description")
            ioc_string_list = tobj.get("ioc_strings")
            ioc_string = "\n".join(ioc_string_list)
            page = f"{tid} - {name}:\n{description}\n\n{ioc_string}"
            ioc_list.append((now, page))
            meta_list.append({"tactic": tid})
        file_info = {
            "file_type": "IOC",
            "filepath": "",
            "file_size": len(ioc_list),
            "MD5": "",
            "SHA1": "",
            "SHA256": "",
            "meta_list": meta_list,
        }
        pages_added = len(ioc_list)
        with self.lock:
            shards_added = self.vdb.add_pages(ioc_list, file_info, prompts=True)
        return pages_added

    def add_file(self, fpath):
        """
        Adds a file to the database and logs relevant information.

        This method parses the specified file using an ArtifactParser instance, measures the
        time taken for parsing, and logs debug information about the process. It then adds
        the parsed contents to the database in chunks of 10,000 entries, logging progress
        and performance metrics such as elapsed time and events per second (eps). The method
        returns the total number of pages added.

        Args:
            fpath (str): The file path of the artifact to be parsed and added.

        Returns:
            int: The total number of pages added to the database.
        """
        ap = ArtifactParser(self.logger)
        t0 = time.time()
        file_info, strings, contents = ap.parse_file(fpath)
        parse_elapsed = round(time.time() - t0, 1)
        self.logger.debug(
            f"Parsing file {fpath} took {parse_elapsed:,} seconds for {len(contents):,} events"
        )
        pages = []
        if contents:
            pages = contents
        t0 = time.time()
        self.logger.debug(f"Adding a total of {len(pages):,} for artifact file {fpath}")
        pages_added = 0
        shards_added = 0
        for chunk in chunk_list(pages, 10000):
            self.logger.debug(
                f"Adding chunk with {len(chunk):,} entries for artifact file {fpath}"
            )
            with self.lock:
                shards_added += self.vdb.add_pages(chunk, file_info)
            pages_added += len(chunk)
            elapsed = time.time() - t0
            eps = round(pages_added / elapsed)
            self.logger.debug(
                f"Added {shards_added:,} shards and {pages_added:,} pages in {round(elapsed)} seconds @ {eps:,} ep/s"
            )
        return pages_added

    def get_artifact_files(self):
        """
        Retrieves artifact files from a database table.

        This method acquires a lock to ensure thread safety and returns the artifact file
        table from the database.

        Returns:
            The artifact file table from the database.
        """
        with self.lock:
            return self.vdb.artifact_file_table
