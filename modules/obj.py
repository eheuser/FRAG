import time
import threading
from utils.utils import obj_cp


class QueryStateManager(object):
    _instance = None

    def __new__(cls, *args, **kwargs):
        """
        Creates a new instance of QueryStateManager if one does not already exist.

        This method ensures that only one instance of QueryStateManager is created by checking
        the existence of cls._instance. If no instance exists, it creates a new one using
        the superclass's __new__ method and assigns it to cls._instance. It then returns
        this instance.

        Args:
            cls (type): The class itself.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            QueryStateManager: The singleton instance of the class.
        """
        if not cls._instance:
            cls._instance = super(QueryStateManager, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        self.status = "Idle"
        self.msg = ""
        self.reasoner = ""
        self.events = []
        self.last_update = time.time()
        self.query_id = None
        self.cancel_flag = False
        self.lock = threading.RLock()

    def reset_query(self):
        """
        Resets the query state to its initial idle condition.

            This method sets various attributes of the object to their default values, indicating
            that no query is currently being processed. It locks the object using a mutex to ensure
            thread safety during the reset operation. The status is set to 'Idle', and other relevant
            attributes such as message, reasoner, events list, last update time, query ID, and cancel
            flag are reset or cleared.

            Raises:
                None explicitly raised within this method. However, any exceptions that occur during
                the execution of this method will propagate upwards.
        """
        with self.lock:
            self.status = "Idle"
            self.msg = ""
            self.reasoner = ""
            self.events = []
            self.last_update = time.time()
            self.query_id = None
            self.cancel_flag = False

    def is_status_cancelled(self):
        """
        Checks whether the status is cancelled by acquiring a lock and inspecting the cancel flag.

        Args:
            self (object): The instance of the class containing the method.

        Returns:
            bool: True if the status is cancelled, False otherwise.
        """
        with self.lock:
            return self.cancel_flag

    def is_status_idle(self):
        """
        Checks if the status is idle.

        This function acquires a lock and checks whether the current status is 'Idle'. It
        returns True if the status is 'Idle', otherwise it returns False.

        Returns:
            bool: True if the status is 'Idle', otherwise False.
        """
        with self.lock:
            return self.status == "Idle"

    def get_status(self):
        """
        Returns the status of the object while ensuring thread safety.

        This method acquires a lock to safely access and return the current status of the
        object. The lock ensures that only one thread can read the status at a time,
        preventing any race conditions.

        Returns:
            Any: The current status of the object.
        """
        with self.lock:
            return self.status

    def set_status_cancelled(self):
        """
        Sets the status of an object to 'Cancelled'.

        This method updates the last update time, sets a cancel flag to True, and changes the
        status to 'Idle' while ensuring thread safety using a lock.

        Args:
            self (object): The instance of the class containing this method.
        """
        with self.lock:
            self.last_update = time.time()
            self.cancel_flag = True
            self.status = "Idle"

    def set_status_idle(self):
        """
        Sets the status of an object to 'Idle' and updates the last update time.

        This method acquires a lock to ensure thread safety while updating the status and
        last update time. The self.lock is used to synchronize access to shared resources,
        ensuring that only one thread can modify the object's state at a given time.

        Args:
            self (object): The instance of the class containing this method.

        Raises:
            None
        """
        with self.lock:
            self.last_update = time.time()
            self.status = "Idle"

    def set_status_active(self):
        """
        Sets the status of an object to 'Active' and updates the last update time.

        This method acquires a lock to ensure thread safety while updating the status and
        last update time. The self.lock is used to synchronize access, ensuring that only one
        thread can modify these attributes at a given time. After acquiring the lock, it sets
        the self.status attribute to 'Active' and updates self.last_update with the current
        time using time.time().

        Args:
            self (object): The instance of the class containing this method.

        Raises:
            None
        """
        with self.lock:
            self.last_update = time.time()
            self.status = "Active"

    def set_status(self, status):
        """
        Sets the status of an object and updates the last update time.

        This method acquires a lock to ensure thread safety while updating the status and
        last update time of the object. The status is set to the provided string value, and
        the last update time is set to the current time.

        Args:
            self (object): The instance of the class containing this method.
            status (str): The new status to be set for the object.

        Raises:
            None
        """
        with self.lock:
            self.last_update = time.time()
            self.status = f"{status}"

    def get_query_id(self):
        """
        Returns the query ID associated with the object.

        This method acquires a lock to ensure thread safety and returns the current query ID.

        Returns:
            The query ID as an integer or other appropriate type.
        """
        with self.lock:
            return self.query_id

    def append_reasoner_header(self, text):
        """
        Appends a header to the reasoner text with the specified message.

        This method acquires a lock to ensure thread safety while updating the last update time
        and appending a formatted header to the existing reasoner text. The header includes the
        provided text enclosed in markdown-style bold and newline characters.

        Args:
            text (str): The message to be included in the header.

        Returns:
            None
        """
        with self.lock:
            self.last_update = time.time()
            self.reasoner = f"{self.reasoner}\n###### **{text}**\n"

    def append_msg_header(self, text):
        """
        Appends a message header to the existing message with a timestamp update.

        This method acquires a lock to ensure thread safety while updating the last_update time
        and appending text to the current message. The new text is added as a new line to the
        existing message.

        Args:
            text (str): The text to be appended to the existing message.
        """
        with self.lock:
            self.last_update = time.time()
            self.msg = f"{self.msg}\n{text}"

    def append_reasoner_text(self, text):
        """
        Appends additional text to the reasoner's output while ensuring thread safety.

        This method updates the last update time and appends the given text to the existing
        reasoner text in a thread-safe manner by using a lock. The resulting reasoner text is
        a concatenation of the current reasoner text and the provided text.

        Args:
            self (object): The instance of the class containing this method.
            text (str): The additional text to be appended to the reasoner's output.
        """
        with self.lock:
            self.last_update = time.time()
            self.reasoner = f"{self.reasoner}{text}"

    def append_msg_text(self, text):
        """
        Appends a message text to an existing message while ensuring thread safety.

        This method updates the last update time and appends the given text to the current
        message in a thread-safe manner by acquiring a lock before making any changes.

        Args:
            self (object): The instance of the class containing this method.
            text (str): The text to be appended to the existing message.

        Returns:
            None
        """
        with self.lock:
            self.last_update = time.time()
            self.msg = f"{self.msg}{text}"

    def append_event(self, event):
        """
        Appends an event to the events list and updates the last update time.

        This method acquires a lock before appending the event to ensure thread safety. It also
        updates the last_update attribute with the current time using time.time().

        Args:
            self (object): The instance of the class containing this method.
            event (object): The event object to be appended to the events list.
        """
        with self.lock:
            self.last_update = time.time()
            self.events.append(event)

    def get_query_slice(self):
        """
        Retrieves a query slice from the current state of the object.

        This method acquires a lock to ensure thread safety while accessing and modifying
        shared resources. It constructs a dictionary representing the current query state,
        including status, message, reasoner, events, last update, query ID, and cancel flag.
        The method then creates a copy of this dictionary and resets certain attributes (events,
        reasoner, msg) to their default values before returning the copied dictionary.

        Returns:
            dict: A dictionary containing the current state of the query.
        """
        with self.lock:
            query_state_dict = {
                "status": self.status,
                "msg": self.msg,
                "reasoner": self.reasoner,
                "events": self.events,
                "last_update": self.last_update,
                "query_id": self.query_id,
                "cancel_flag": self.cancel_flag,
            }
            ret_val = obj_cp(query_state_dict)
            self.events = []
            self.reasoner = ""
            self.msg = ""
            return ret_val


class ArtifactStateManager(object):
    _instance = None

    def __new__(cls, *args, **kwargs):
        """
        Creates a new instance of the class if one does not already exist.

        This method ensures that only one instance of the class is created by checking if an
        instance already exists before creating a new one. If no instance exists, it calls
        the superclass's __new__ method to create and return a new instance. Otherwise, it
        returns the existing instance.

        Args:
            cls (type): The class itself.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            An instance of the class.
        """
        if not cls._instance:
            cls._instance = super(ArtifactStateManager, cls).__new__(
                cls, *args, **kwargs
            )
        return cls._instance

    def __init__(self):
        self.lock = threading.RLock()
        self.status = {}

    def get_status(self):
        """
        Returns the status of the object while ensuring thread safety.

        This method acquires a lock to safely access and return the current status of the
        object. The lock ensures that only one thread can read the status at a time,
        preventing race conditions.

        Returns:
            The current status of the object.
        """
        with self.lock:
            return self.status

    def add_file(self, filepath):
        """
        Adds a file to the processing queue with an initial status of 'queued'.

        This method updates the internal state to reflect that a new file has been added for
        processing. It uses a lock to ensure thread safety when modifying shared resources.

        Args:
            self (object): The instance of the class containing this method.
            filepath (str): The path to the file being added to the queue.
        """
        with self.lock:
            self.status[filepath] = {"status": "queued"}

    def mark_file_in_progress(self, filepath):
        """
        Marks a file as being in progress by updating its status in the internal dictionary.

        This method acquires a lock to ensure thread safety while updating the status of
        the specified file. The status is set to 'in-progress' for the given filepath.

        Args:
            filepath (str): The path of the file to be marked as in progress.

        Returns:
            None
        """
        with self.lock:
            self.status[filepath] = {"status": "in-progress"}

    def mark_file_done(self, filepath):
        """
        Marks a file as done by updating its status.
        
        This function updates the status of a specified file to 'done' in a thread-safe manner
        using a lock. It modifies the internal dictionary self.status to reflect that the
        file has been processed successfully.

        Args:
            filepath (str): The path of the file to be marked as done.

        Raises:
            None
        """
        with self.lock:
            self.status[filepath] = {"status": "done"}

    def mark_file_deleted(self, filepath):
        """
        Marks a file as deleted by removing its entry from the status dictionary and resetting
        the dictionary if it becomes empty.

        This method acquires a lock to ensure thread safety while modifying the shared state.
        It removes the specified filepath from the status dictionary, and if the dictionary
        becomes empty after removal, it resets the dictionary to None and then reinitializes it
        as an empty dictionary.

        Args:
            filepath (str): The path of the file to be marked as deleted.

        Raises:
            KeyError: If the specified filepath is not found in the status dictionary.
        """
        with self.lock:
            del self.status[filepath]
            if len(self.status) == 0:
                self.status = None
                del self.status
                self.status = {}
