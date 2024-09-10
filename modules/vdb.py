import warnings

warnings.filterwarnings(
    "ignore",
    category=FutureWarning,
    module="transformers\\.tokenization_utils_base",
    message="`clean_up_tokenization_spaces` was not set. It will be set to `True` by default.",
)
warnings.filterwarnings(
    "ignore", message=".*Torch was not compiled with flash attention.*"
)
from collections import defaultdict
import uuid
import math
import time
import os
import gc
import torch
from sentence_transformers import SentenceTransformer
from transformers import logging as transformers_logging

transformers_logging.set_verbosity_error()
from chromadb.config import Settings as ChromaSettings
import chromadb
from chromadb.utils.batch_utils import create_batches
from transformers import AutoTokenizer
from modules.sqlite_db import open_db, close_db, dict_factory
from utils.utils import ret_time, split_string_into_n_parts


class VectorDB:

    def __init__(
        self,
        logger,
        data_path="data/vector_db",
        collection_name="main",
        model_name="multi-qa-MiniLM-L6-cos-v1",
    ):
        self.open = False
        self.logger = logger
        self.data_path = data_path
        self.sqlite_db_path = f"{data_path}.db"
        self.collection_name = collection_name
        self.model_name = model_name
        self.connect_vdb()

    def connect_vdb(self):
        """
        Connects to a vector database and initializes necessary components.

        This method sets up a connection to a vector database using ChromaDB's PersistentClient. It
        initializes a SentenceTransformer model on either 'cuda' or 'cpu', depending on availability.
        It also creates or retrieves collections for the main collection and prompts from the vector
        database. Additionally, it sets up tokenization with AutoTokenizer and initializes lists for IDs,
        documents, and metadata. If a SQLite database file does not exist, it bootstraps an artifact
        file table and marks the database as new; otherwise, it sets the database as existing. Finally,
        it sets the 'open' attribute to True.

        Args:
            self (object): The instance of the class containing this method.

        Raises:
            None explicitly raised within the function.
        """
        self.chroma_client = chromadb.PersistentClient(
            path=self.data_path,
            settings=ChromaSettings(anonymized_telemetry=False, allow_reset=True),
        )
        
        device = "cuda" if torch.cuda.is_available() else "cpu"

        if device == "cpu":
            self.logger.warning(f"connect_vdb: Torch is running with {device}")
        else:
            self.logger.info(f"connect_vdb: Torch is running with {device}")
        
        self.model = SentenceTransformer(self.model_name, device=device)
        self.collection = self.chroma_client.get_or_create_collection(
            name=self.collection_name
        )
        self.prompt_collection = self.chroma_client.get_or_create_collection(
            name="prompts"
        )
        self.min_entry_len = 8
        self.max_chunk_len = 512
        self.tokenizer = AutoTokenizer.from_pretrained(
            f"sentence-transformers/{self.model_name}",
            clean_up_tokenization_spaces=True,
        )
        self.ids = []
        self.documents = []
        self.metadatas = []
        if os.path.isfile(self.sqlite_db_path) is False:
            self.bootstrap_artifact_file_table()
            self.new_db = True
        else:
            self.new_db = False
        self.open = True

    @property
    def artifact_file_table(self):
        """
        Retrieves and returns a list of artifact files from the database excluding those with
        'IOC' file type.

        This property opens a connection to the SQLite database specified by sqlite_db_path,
        executes a query to fetch all rows from the artifact_files table, and processes each
        row to exclude entries where the file_type is 'IOC'. It logs any exceptions that occur
        during the process.

        Returns:
            list: A list of dictionaries representing artifact files excluding those with
                'IOC' file type.
        """
        db, cur = open_db(self.sqlite_db_path)
        results = []
        try:
            sql = "SELECT * FROM artifact_files"
            cur.execute(sql)
            rows = cur.fetchall()
            for row in rows:
                if row:
                    obj = dict_factory(cur, row)
                    if obj["file_type"] == "IOC":
                        continue
                    results.append(obj)
        except Exception as e:
            self.logger.error(f"artifact_file_table: Raised {e}")
        close_db(db, cur)
        return results

    def close(self):
        """
        Closes and cleans up resources used by the object.

        This method sets various attributes to None and deletes them to free memory. It also
        calls garbage collection to clean up any remaining unused objects. Finally, it sets
        the 'open' attribute to False to indicate that the object is no longer in use.

        Returns:
            None
        """
        self.tokenizer = None
        del self.tokenizer
        self.prompt_collection = None
        del self.prompt_collection
        self.collection = None
        del self.collection
        self.model = None
        del self.model
        self.chroma_client = None
        del self.chroma_client
        gc.collect()
        self.open = False
        return

    def drop_db(self):
        """
        Drops the database by resetting the vector database and deleting the SQLite3 database file if it exists.

        Args:
            self (object): The instance of the class containing the method.

        Raises:
            Exception: If an error occurs while resetting the vector database or deleting the SQLite3 database file.
        """
        try:
            self.chroma_client.reset()
        except Exception as e:
            self.logger.critical(f"drop_db: Deleting vector db raised {e}")
        try:
            if os.path.isfile(self.sqlite_db_path) is True:
                os.remove(self.sqlite_db_path)
        except Exception as e:
            self.logger.critical(f"drop_db: Deleting Sqlite3 db raised {e}")
        return

    def is_new_db(self):
        """
        Checks if a new database is being used.

        This method returns True if the instance is using a new database, otherwise it returns
        False.

        Returns:
            bool: True if a new database is in use, False otherwise.
        """
        return self.new_db

    def bootstrap_artifact_file_table(self):
        """
        Bootstraps an artifact file table in a SQLite database.

        This method creates a table named 'artifact_files' if it does not already exist and
        sets up indexes on specific columns to optimize query performance. It connects to the
        SQLite database specified by self.sqlite_db_path, executes the necessary SQL statements,
        and handles any exceptions that may occur during execution.

        Args:
            self (object): The instance of the class containing this method.

        Raises:
            Exception: If an error occurs while executing the SQL statements or if there is a
                problem with the database connection.
        """
        sql = [
            """
            CREATE TABLE IF NOT EXISTS "artifact_files" (
                "rowid"	INTEGER NOT NULL PRIMARY KEY,
                "sha256"	TEXT NOT NULL COLLATE NOCASE,
                "sha1"	TEXT NOT NULL COLLATE NOCASE,
                "md5"	TEXT NOT NULL COLLATE NOCASE,
                "filepath"	TEXT NOT NULL COLLATE NOCASE,
                "file_sz"	INTEGER NOT NULL,
                "file_type"	TEXT NOT NULL COLLATE NOCASE,
                "enter_string"	TEXT NOT NULL COLLATE NOCASE,
                "update_string"	TEXT NOT NULL COLLATE NOCASE,
                "enter_utc"	REAL NOT NULL,
                "update_utc"	REAL NOT NULL,
                "item_count"	INTEGER NOT NULL,
                "shard_count"	INTEGER NOT NULL,
                UNIQUE("sha256","filepath")
            );
            """,
            """
            CREATE INDEX IF NOT EXISTS "sha256_af" ON "artifact_files" (
                "sha256"
            );
            """,
            """
            CREATE INDEX IF NOT EXISTS "sha1_af" ON "artifact_files" (
                "sha1"
            );
            """,
            """
            CREATE INDEX IF NOT EXISTS "md5_af" ON "artifact_files" (
                "md5"
            );
            """,
            """
            CREATE INDEX IF NOT EXISTS "filepath_af" ON "artifact_files" (
                "filepath"
            );
            """,
        ]
        db, cur = open_db(self.sqlite_db_path)
        for s in sql:
            try:
                cur.execute(s)
            except Exception as e:
                self.logger.error(
                    f"bootstrap_artifact_file_table: {e} was raised by SQL statement {s}"
                )
        close_db(db, cur)
        return

    def update_artifact_files(self, file_info, pages_added, shards_added):
        """
        Updates artifact files with new information.

        This function checks if the database is open and updates or inserts artifact file
        records based on the provided file information, pages added, and shards added. It logs
        critical errors if the database is closed and handles exceptions during SQL operations.

        Args:
            self (object): The instance of the class containing this method.
            file_info (dict): A dictionary containing file information such as SHA256, SHA1,
                MD5, filepath, file_size, and file_type.
            pages_added (int): The number of pages added to the artifact files.
            shards_added (int): The number of shards added to the artifact files.

        Raises:
            Exception: If an error occurs during SQL operations or if the database is closed.
        """
        if self.open is False:
            self.logger.critical(f"update_artifact_files: Database is CLOSED")
            return
        sha256 = file_info.get("SHA256", "")
        sha1 = file_info.get("SHA1", "")
        md5 = file_info.get("MD5", "")
        filepath = file_info.get("filepath", "")
        file_sz = file_info.get("file_size", "")
        file_type = file_info.get("file_type")
        now = time.time()
        now_str = ret_time(now)
        db, cur = open_db(self.sqlite_db_path)
        try:
            check_sql = """
                SELECT *
                    FROM artifact_files
                WHERE
                    sha256 = ? AND filepath = ?
            """
            cur.execute(check_sql, [sha256, filepath])
            row = cur.fetchone()
            if row:
                update_sql = """
                    UPDATE artifact_files
                        SET update_string = ?,
                            update_utc = ?,
                            item_count = item_count + ?,
                            shard_count = shard_count + ?
                        WHERE sha256 = ? AND filepath = ?
                """
                cur.execute(
                    update_sql,
                    [now_str, now, pages_added, shards_added, sha256, filepath],
                )
            else:
                insert_sql = """
                    INSERT INTO artifact_files
                    (
                        sha256, sha1, md5, filepath, file_sz,
                        file_type, enter_string, update_string, enter_utc, update_utc,
                        item_count, shard_count
                    )
                    VALUES
                    (
                        ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?,
                        ?, ?
                    )
                """
                cur.execute(
                    insert_sql,
                    [
                        sha256,
                        sha1,
                        md5,
                        filepath,
                        file_sz,
                        file_type,
                        now_str,
                        now_str,
                        now,
                        now,
                        pages_added,
                        shards_added,
                    ],
                )
        except Exception as e:
            self.logger.error(f"update_artifact_files: Raised {e}")
        close_db(db, cur)

    def count_tokens(self, text):
        """
        Counts tokens in a given text using a tokenizer.

        If the database is closed, logs a critical message and returns zero. Otherwise, it uses
        the tokenizer to encode the text without truncation and with special tokens added, then
        returns the number of tokens.

        Args:
            text (str): The input text to be tokenized.

        Returns:
            int: The number of tokens in the given text.
        """
        if self.open is False:
            self.logger.critical(f"update_artifact_files: Database is CLOSED")
            return 0
        tokens = self.tokenizer.encode(text, truncation=False, add_special_tokens=True)
        return len(tokens)

    def peek(self):
        """
        Peeks at the next item in the collection if the database is open.

        This method checks whether the database is open and logs a critical message if it is
        closed. If the database is open, it returns the next item from the collection by calling
        self.collection.peek().

        Returns:
            The next item in the collection or None if the database is closed.
        """
        if self.open is False:
            self.logger.critical(f"update_artifact_files: Database is CLOSED")
            return None
        return self.collection.peek()

    def count(self):
        """
        Counts the number of documents in a collection if the database is open.

        This method checks whether the database is open and logs a critical message if it is not.
        If the database is open, it returns the count of documents in the collection.

        Returns:
            int: The number of documents in the collection or 0 if the database is closed.
        """
        if self.open is False:
            self.logger.critical(f"update_artifact_files: Database is CLOSED")
            return 0
        return self.collection.count()

    def add_pages(self, pages, file_info, prompts=False):
        """

        Adds pages to a collection with optional metadata and prompts.

        This method processes each page in the provided list of pages, chunks them if they
        exceed the maximum token length, and adds them to the specified collection along
        with their embeddings and metadata. It updates artifact files after processing.

        Args:
            self (object): The instance of the class containing this method.
            pages (list): A list of tuples where each tuple contains a UTC timestamp and a page
                of text to be added.
            file_info (dict): A dictionary containing information about the file, including
                SHA256 hash, file path, file type, and optional metadata list.
            prompts (bool, optional): If True, uses the prompt collection for upserting;
                otherwise, uses the default collection. Defaults to False.

        Returns:
            int: The number of shards added.
        """
        if self.open is False:
            self.logger.critical(f"update_artifact_files: Database is CLOSED")
            return 0
        sha256 = file_info.get("SHA256", "")
        filepath = file_info.get("filepath", "")
        file_type = file_info.get("file_type", "")
        meta_list = file_info.get("meta_list", None)
        ids = []
        documents = []
        metadatas = []
        shards_added = 0
        pages_added = 0
        for idx, (utc, page) in enumerate(pages):
            if len(page) <= self.min_entry_len:
                continue
            pages_added += 1
            source_doc_id = self.generate_doc_id()
            if self.count_tokens(page) > self.max_chunk_len:
                item_chunks = self.chunk_text(page, self.max_chunk_len)
                seq_id = 1
                seq_cnt = len(item_chunks)
                for chunk in item_chunks:
                    ids.append(f"{source_doc_id}.{seq_id}")
                    documents.append(chunk)
                    if seq_id == 1:
                        metadatas.append(
                            {
                                "source_doc_id": source_doc_id,
                                "seq_id": seq_id,
                                "seq_cnt": seq_cnt,
                                "SHA256": sha256,
                                "filepath": filepath,
                                "file_type": file_type,
                                "utc": utc,
                            }
                        )
                    else:
                        metadatas.append(
                            {
                                "source_doc_id": source_doc_id,
                                "seq_id": seq_id,
                                "seq_cnt": seq_cnt,
                                "utc": utc,
                            }
                        )
                    if meta_list:
                        for key, value in meta_list[idx].items():
                            metadatas[-1][key] = str(value)
                    seq_id += 1
                    shards_added += 1
            else:
                ids.append(f"{source_doc_id}.1")
                documents.append(page)
                metadatas.append(
                    {
                        "source_doc_id": source_doc_id,
                        "seq_id": 1,
                        "seq_cnt": 1,
                        "SHA256": sha256,
                        "filepath": filepath,
                        "file_type": file_type,
                        "utc": utc,
                    }
                )
                shards_added += 1
                if meta_list:
                    for key, value in meta_list[idx].items():
                        metadatas[-1][key] = str(value)
        if ids and documents and metadatas:
            embeddings = (
                self.model.encode(documents, convert_to_tensor=True).cpu().tolist()
            )
            batches = create_batches(
                api=self.chroma_client,
                ids=ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
            )
            if prompts is True:
                collection = self.prompt_collection
            else:
                collection = self.collection
            for batch in batches:
                collection.upsert(
                    ids=batch[0],
                    documents=batch[3],
                    embeddings=batch[1],
                    metadatas=batch[2],
                )
        self.update_artifact_files(file_info, pages_added, shards_added)
        return shards_added

    def generate_doc_id(self):
        """
        Generates a unique document ID.

        This function generates and returns a unique document ID by creating a UUID and shifting it
        right by 64 bits to ensure uniqueness within the system. The resulting value is converted
        to a string for easy storage and retrieval.

        Returns:
            str: A unique document ID as a string.
        """
        return str(uuid.uuid1().int >> 64)

    def query(self, query_dict, prompts=False):
        """
        Executes a query on a collection based on provided parameters and returns sorted results.

        This function checks if the database is open before proceeding with the query. It retrieves
        query parameters from the input dictionary and constructs an argument dictionary for the
        collection's query method. The function handles optional conditions and metadata filters,
        and processes the results to ensure they are within specified limits. If prompts are enabled,
        it queries a different collection. The results are sorted by their UTC timestamp before being
        returned.

        Args:
            query_dict (dict): A dictionary containing query parameters such as 'query_string',
                'doc_multi_hit', 'max_shard_ctx', 'n_results', 'condition_dict', and 'meta_dict'.
            prompts (bool, optional): If True, queries the prompt collection instead of the default
                collection. Defaults to False.

        Returns:
            tuple: A tuple containing two lists - sorted values and their corresponding metadata.
        """
        if self.open is False:
            self.logger.critical(f"update_artifact_files: Database is CLOSED")
            return [], []
        query_string = query_dict.get("query_string", "")
        doc_multi_hit = query_dict.get("doc_multi_hit", False)
        max_shard_ctx = int(query_dict.get("max_shard_ctx", 3))
        n_results = int(query_dict.get("n_results", 500))
        condition_dict = query_dict.get("condition_dict", None)
        meta_dict = query_dict.get("meta_dict", None)

        ret_val = []
        ret_meta = []

        if isinstance(query_string, str):
            query_string = [query_string]
        
        if isinstance(n_results, int) is False:
            n_results = int(n_results)
        
        _n_results = n_results * 2
        if _n_results > self.count():
            _n_results = self.count()
            # Sanity
            if _n_results <= 0:
                _n_results = n_results
        
        args = {"query_texts": query_string, "n_results": _n_results}
        if condition_dict and isinstance(condition_dict, dict):
            args["where_document"] = condition_dict
        if meta_dict and isinstance(meta_dict, dict):
            args["where"] = meta_dict
        if prompts is True:
            collection = self.prompt_collection
        else:
            collection = self.collection

        results = collection.query(**args)
        metadatas = results.get("metadatas", [[]])[0]
        documents = results.get("documents", [[]])[0]
        if len(metadatas) == len(documents):
            source_doc_id_added = {}
            for idx, meta in enumerate(metadatas):
                if len(ret_val) >= n_results:
                    break
                doc = documents[idx]
                source_doc_id = meta.get("source_doc_id", "")
                if source_doc_id:
                    if source_doc_id in source_doc_id_added:
                        continue
                    seq_id = meta.get("seq_id", "")
                    _doc = self.get_source_doc_context(
                        source_doc_id, seq_id, max_shard_ctx, prompts
                    )
                    if _doc:
                        doc = _doc
                        if doc_multi_hit is False:
                            source_doc_id_added[source_doc_id] = True
                    else:
                        self.logger.info(f"source document {source_doc_id} not found")
                else:
                    self.logger.info(f"source document {source_doc_id} not present")
                ret_val.append(doc)
                ret_meta.append(meta)
        else:
            ret_val = documents
        values = ret_val[:n_results]
        meta = ret_meta[:n_results]
        combined = zip(meta, values)
        sorted_data = sorted(combined, key=lambda x: x[0]["utc"])
        sorted_value = []
        sorted_meta = []
        for d in sorted_data:
            sorted_meta.append(d[0])
            sorted_value.append(d[1])
        return sorted_value, sorted_meta

    def get_source_doc_context(self, doc_id, seq_id, max_shard_ctx, prompts):
        """
        Retrieves the source document context for a given document ID and sequence ID.

        This function selects the appropriate collection based on whether prompts are enabled
        or not. It then fetches documents from the selected collection that match the specified
        document ID. If matching documents are found, it reconstructs them using the provided
        sequence ID and maximum shard context. Otherwise, it returns None.

        Args:
            doc_id (str): The unique identifier of the source document to retrieve.
            seq_id (int): The sequence identifier used for reconstruction.
            max_shard_ctx (int): The maximum number of shards to consider during reconstruction.
            prompts (bool): A flag indicating whether to use the prompt collection or not.

        Returns:
            list or None: The reconstructed documents if found, otherwise None.
        """
        if prompts is True:
            collection = self.prompt_collection
        else:
            collection = self.collection
        results = collection.get(where={"source_doc_id": doc_id})
        if results and len(results.get("documents", [])) > 0:
            return self.reconstruct_documents(results, seq_id, max_shard_ctx)
        else:
            return None

    def reconstruct_documents(self, data, search_seq_id, max_shard_ctx):
        """
        Reconstructs documents from given data based on sequence ID and context range.

        This function processes metadata and document chunks to reconstruct original documents.
        It filters the chunks within a specified sequence ID range and concatenates them in order
        to form complete documents. The reconstructed documents are then returned as a single
        string.

        Args:
            data (dict): A dictionary containing 'metadatas' and 'documents'. Each metadata is
                associated with a document chunk.
            search_seq_id (int or str): The sequence ID to search for in the metadata.
            max_shard_ctx (int): The maximum context range around the search_seq_id to include
                in the reconstruction.

        Returns:
            str: A single string containing all reconstructed documents concatenated together.
        """
        docs = defaultdict(lambda: [])
        metadatas, documents = data["metadatas"], data["documents"]
        file_meta = {}
        for metadata, document in zip(metadatas, documents):
            source_doc_id = metadata["source_doc_id"]
            seq_id = metadata["seq_id"]
            if seq_id in (1, "1"):
                file_meta = metadata
                if "seq_id" in file_meta:
                    del file_meta["seq_id"]
                if "seq_cnt" in file_meta:
                    del file_meta["seq_cnt"]
            if (
                seq_id >= search_seq_id - max_shard_ctx
                and seq_id <= search_seq_id + max_shard_ctx
            ):
                docs[source_doc_id].append((seq_id, document))
        reconstructed_docs = []
        for source_doc_id, chunks in docs.items():
            sorted_chunks = sorted(chunks, key=lambda x: x[0])
            full_document = "".join(chunk[1] for chunk in sorted_chunks)
            reconstructed_docs.append(full_document)
        return "".join(reconstructed_docs)

    def chunk_text(self, text, max_length=512):
        """
        Chunks a given text into smaller parts based on a specified maximum length.

        This method iterates over possible chunk sizes and splits the input text accordingly.
        It checks if the token count of the first chunk is within the specified max_length,
        returning the chunks if true. If no suitable chunk size is found, it falls back to an
        internal method for further processing.

        Args:
            text (str): The input text to be chunked.
            max_length (int, optional): The maximum length of each chunk in tokens. Defaults
                to 512.

        Returns:
            list: A list of text chunks where the token count of each chunk is less than or
                  equal to max_length.
        """
        for i in range(2, 1024):
            chunks = split_string_into_n_parts(text, i)
            if self.count_tokens(chunks[0]) <= max_length:
                return chunks
        return self._chunk_text(text, max_length)

    def _chunk_text(self, text, max_length=512):
        """
        Splits text into chunks of specified maximum length while preserving word boundaries.

        This method takes a piece of text and splits it into smaller chunks such that each
        chunk does not exceed the given maximum length, measured in tokens. It ensures that
        words are not split across chunks unless they themselves exceed the maximum length,
        in which case they are divided into multiple parts.

        Args:
            text (str): The input text to be chunked.
            max_length (int, optional): The maximum token length for each chunk. Defaults to 512.

        Returns:
            list of str: A list of text chunks where each chunk's token count does not exceed
                the specified maximum length.
        """
        words = str(text).split(" ")
        chunks = []
        current_chunk = []
        for word in words:
            if not word:
                continue
            word_len = self.count_tokens(word)
            if (
                current_chunk
                and self.count_tokens(" ".join(current_chunk)) + word_len > max_length
            ):
                if word_len > max_length:
                    if current_chunk:
                        chunks.append(" ".join(current_chunk))
                        current_chunk = []
                    ratio = math.ceil(word_len / max_length) + 1
                    _split = split_string_into_n_parts(word, ratio)
                    for s in _split:
                        chunks.append(s)
                    continue
                chunks.append(" ".join(current_chunk))
                current_chunk = []
            current_chunk.append(word)
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        return chunks
