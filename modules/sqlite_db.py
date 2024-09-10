import sqlite3


class SQLiteDB:

    def __init__(self):
        self.pragmas = [
            f"PRAGMA busy_timeout = {30000}",
            "PRAGMA journal_mode = WAL",
            f"PRAGMA wal_autocheckpoint = {10000}",
            "PRAGMA case_sensitive_like = FALSE",
            "PRAGMA automatic_index = FALSE",
            "PRAGMA temp_store = 1",
            "PRAGMA synchronous = NORMAL",
            "PRAGMA foreign_keys = OFF",
            f"PRAGMA mmap_size = {64 * 1024 * 1024}",
            f"PRAGMA cache_size = {-32768}",
        ]
        self.mem_pragmas = [
            "PRAGMA journal_mode = OFF",
            "PRAGMA synchronous = OFF",
            "PRAGMA temp_store = MEMORY",
            "PRAGMA case_sensitive_like = FALSE",
            "PRAGMA locking_mode = EXCLUSIVE",
        ]

    def backup(self, db, backup_path, pragmas=None):
        """
        Performs a backup of the given database to the specified path with optional pragmas.

        This function connects to an SQLite database at the specified backup path and executes
        any provided PRAGMA statements before performing the backup operation. If no pragmas
        are provided, it defaults to using a set of predefined pragmas including setting the
        locking mode to EXCLUSIVE. The function then closes the cursor and database connection
        after completing the backup process.

        Args:
            db (sqlite3.Connection): The source database connection to back up.
            backup_path (str): The file path where the backup database will be created.
            pragmas (list of str, optional): A list of PRAGMA statements to execute on the
                backup database before performing the backup. If not provided, default pragmas
                are used.

        Raises:
            sqlite3.Error: If an error occurs during the connection or execution of SQL
                statements.
        """
        bkup_db = sqlite3.connect(backup_path)
        bkup_cur = bkup_db.cursor()
        if pragmas is None:
            for pragma in self.pragmas:
                bkup_cur.execute(pragma)
            bkup_cur.execute("PRAGMA locking_mode = EXCLUSIVE")
        else:
            for pragma in pragmas:
                bkup_cur.execute(pragma)
        db.backup(bkup_db)
        bkup_cur.close()
        bkup_db.close()

    def connect(self, filepath, pragmas=None):
        """
        Connects to a SQLite database and applies specified pragmas.

        This function establishes a connection to a SQLite database at the given filepath and
        applies any provided pragmas or default pragmas if none are specified. It returns the
        database connection and cursor objects. If the filepath is ':memory:', it uses memory-
        specific pragmas.

        Args:
            filepath (str): The path to the SQLite database file.
            pragmas (list of str, optional): A list of PRAGMA statements to execute on the
                database connection. If not provided, default pragmas are used.

        Returns:
            tuple: A tuple containing the database connection and cursor objects.
        """
        db = sqlite3.connect(filepath)
        cur = db.cursor()
        if filepath == ":memory:":
            pragmas = self.mem_pragmas
        if pragmas is None:
            for pragma in self.pragmas:
                cur.execute(pragma)
        else:
            for pragma in pragmas:
                cur.execute(pragma)
        return db, cur


def open_db(db_path):
    """
    Opens a database connection to an SQLite database at the specified path.

    This function creates an instance of SQLiteDB and connects to the database at the given
    path. It returns the database object and cursor for further operations.

    Args:
        db_path (str): The file path to the SQLite database.

    Returns:
        tuple: A tuple containing the database connection object and the cursor.
    """
    dbf = SQLiteDB()
    db, cur = dbf.connect(db_path)
    return db, cur


def close_db(db, cur):
    """
    Closes a database connection and its cursor, committing any pending transactions beforehand.

    Args:
        db (object): The database object to be closed.
        cur (object): The cursor associated with the database that needs to be closed.

    Raises:
        Exception: If an error occurs during the closing process or if there are issues committing
            transactions.
    """
    cur.close()
    if db.in_transaction:
        db.commit()
    db.close()


def dict_factory(cursor, row):
    """
    Converts a database row into a dictionary using cursor description.

    This function iterates over the cursor's description and maps each column name to its
    corresponding value in the row, returning a dictionary with these mappings.

    Args:
        cursor (object): The database cursor object containing the query result metadata.
        row (tuple): A tuple representing a single row of data from the query result.

    Returns:
        dict: A dictionary where keys are column names and values are the corresponding row
            values.
    """
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d
