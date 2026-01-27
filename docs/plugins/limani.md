# Ch-aOS Limani Plugin

So, the Ch-aOS Logbook is great and all, but what if you want to take it a step further? What if you need to store it in a better format like a database, or maybe you want to visualize it in a fancy dashboard? That's where the Limani plugin comes in!

Limanis are the greek word for "harbors", and just like a harbor is a safe place for ships to dock, the Limani plugin provides a safe place for your logbook data to dock and be managed.

Limanis are purely optional plugins that simply add a database for your Logbook data. You can choose one Limani plugin to use in each `chaos apply --logbook --limani <limani>` command.

## Why?

Well, the default Logbook stores data in a simple SQLite database (through the Ch-rima Limani) which is great for small-scale use, but if you're running a larger operation or need more advanced features, you might want to consider using a different Limani plugin.

## How to use?

Simply install the Limani plugin of your choice, and then use the `--limani <limani>` flag when applying your logbook. For example, if you wanted to use the Ch-aOS PostgreSQL Limani, you would run `chaos apply <tags> --logbook --limani chaos-limani-postgresql`, easy as that!

## Now the juicy part: Developing your own Limani plugin

You see, a plugin system without a good interface is not a real plugin system, is it? So, to make sure that all Limani plugins play nicely together, we've defined a simple interface that all Limani plugins must implement.

Here's the base Limani abstract class that all Limani plugins must inherit from:

```python
from abc import ABC, abstractmethod

class Limani(ABC):
    """
    Abstract base class for Limani implementations.

    Limanis are responsible for connecting to, setting, getting and disconnecting
    From databases or other data sources.

    They are meant to give an endpoint-agnostic interface to the Logbook system.

    The Logbook should _require_ a Limani to be used as its data source.

    The Limanis should be easily pluggable, so that different data sources can be used.
    Also, the only abstract methods should be required to be implemented by the subclasses.

    The only abstract methods required are connect, disconnect, set, get, export, init_db.
    """

    def __init__(self, config: dict):
        """
        Initialize the Limani with the given configuration.

        :param config: A dictionary containing configuration parameters.
        """
        self.config = config or {}
        self.werehouse = config.get("werehouse", "")

    @abstractmethod
    def connect(self):
        """
        Connect to the data source.

        MUST return a connection object or similar.
        """
        raise NotImplementedError

    @abstractmethod
    def disconnect(self):
        """Disconnect from the data source."""
        raise NotImplementedError

    @abstractmethod
    def end_run_update(self, run_id: str, end_time: float, status: str, summary: dict) -> None:
        """
        This method should update a run at the end with final status, time, and summary.

        :param run_id: The ID of the run to update.
        :param end_time: The end time of the run.
        :param status: The final status of the run.
        :param summary: The summary of the run.
        """

        raise NotImplementedError

    @abstractmethod
    def start_update_run(self, run_id: str, status: str) -> None:
        """
        This method should update the status of a run in the data source.

        :param run_id: The ID of the run to update.
        :param status: The new status of the run.
        """
        raise NotImplementedError

    @abstractmethod
    def insert_fact_log(self, run_id: str, timestamp: float, log_level: str, context: str, command: str) -> None:
        """
        This method should insert a fact log into the data source.

        :param run_id: The ID of the run the fact log belongs to.
        :param timestamp: The timestamp of the fact log.
        :param log_level: The log level of the fact log.
        :param context: The context of the fact log.
        :param command: The command of the fact log.

        """
        raise NotImplementedError

    @abstractmethod
    def insert_operation(self, run_id: str, host_id: int, op_hash: str, name: str, changed: bool, success: bool, duration: float, timestamp: float, logs: dict, diff: str, arguments: dict, retry_stats: dict, command_n_facts: list) -> None:
        """
        This method should insert an operation into the data source.

        :param run_id: The ID of the run the operation belongs to.
        :param host_id: The ID of the host the operation belongs to.
        :param op_hash: The hash of the operation.
        :param name: The name of the operation.
        :param changed: Whether the operation changed anything.
        :param success: Whether the operation was successful.
        :param duration: The duration of the operation.
        :param timestamp: The timestamp of the operation.
        :param logs: The logs of the operation.
        :param diff: The diff of the operation.
        :param arguments: The arguments of the operation.
        :param retry_stats: The retry stats of the operation.
        :param command_n_facts: The command and facts associated with the operation.
        """

        raise NotImplementedError

    @abstractmethod
    def insert_snapshot(self, run_id: str, host_id: int, stage: str, timestamp: float, metrics: dict) -> None:
        """
        This method should insert a resource snapshot into the data source.

        :param run_id: The ID of the run the snapshot belongs to.
        :param host_id: The ID of the host the snapshot belongs to.
        :param stage: The stage of the snapshot.
        :param timestamp: The timestamp of the snapshot.
        :param metrics: The metrics of the snapshot.
        """

        raise NotImplementedError

    @abstractmethod
    def create_run(self, run_id: str, run_id_human: str, start_time: float, hailer_info: dict) -> str:
        """
        Creates a new run entry in the database.

        :param run_id: The ID of the run.
        :param run_id_human: The human-readable ID of the run.
        :param start_time: The start time of the run.
        :param hailer_info: The hailer information of the run.

        :return: The ID of the created run.
        """

    @abstractmethod
    def init_db(self):
        """
        Initialize the data source.

        This should create any necessary tables or structures in the data source.
        This should only create if not exists.
        """
        raise NotImplementedError

    @abstractmethod
    def get_or_create_host(self, run_id: str, host_name: str) -> int:
        """
        Specific method to get or create a host in the data source, this one does two things.

        :param run_id: The ID of the host the host belongs to.
        :param host_name: The name of the host to get or create.

        :return: The ID of the host.

        Should be idempotent.
        """

    @abstractmethod
    def get_run_data(self, run_id: str):
        """
        Get all data for a given run.
        :param run_id: The ID of the run to get data for.
        :return: A dictionary containing all data for the run.
        """
        raise NotImplementedError

    @abstractmethod
    def get_facts_for_timespan(self, run_id: str, start_time: float, end_time: float) -> list[dict]:
        """
        Get all facts for a given run within a specific time span.

        :param run_id: The ID of the run to get facts for.
        :param start_time: The start time of the time span.
        :param end_time: The end time of the time span.

        :return: A list of fact logs within the specified time span.
        """

        raise NotImplementedError

    @abstractmethod
    def get_run_summary_stats(self, run_id: str) -> dict:
        """
        Get summary statistics for a given run.

        :param run_id: The ID of the run to get summary statistics for.

        :return: A dictionary containing summary statistics for the run.
        """
        raise NotImplementedError
```

As you can see, the Limani class only defines _read_ and _write_ methods for the Logbook data. This means that you can implement your own Limani plugin to connect to any data source you want, as long as you implement the required methods.

The Logbook system automatically loads and uses the Limani plugin specified in the `--limani` flag when applying the logbook, and then uses these methods to interact with the data source.

A _complete_ Limani plugin can be seen in [here](https://github.com/Ch-aOS-Ch/Ch-aOS/blob/main/cli/src/chaos/lib/limani/chrima.py)
