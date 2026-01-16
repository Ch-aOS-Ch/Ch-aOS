from abc import ABC, abstractmethod
from omegaconf import DictConfig, OmegaConf

class Boat(ABC):
    """
    Abstract base class representing a generic boat.

    A boat represents a dynamic provider for the fleet management system.
    This means that each boat has to implement methods to manage its lifecycle
    which include:
    connecting to an external inventory provider (e.g., ec2)
    getting the current state of the fleet
    creating new instances
    returning instances to the pool to list of fleets.

    A boat is configured in a Ch-obolo file like so:
    fleet:
      parallelism: x<=5
      boats:
        - provider: {name of this boat}
          config:
            {config parameters specific to this boat}

      hosts:
        - host1:
            ssh_user: user1
            ssh_key: /path/to/key1.pem

    The 'provider' name is used to find the corresponding Boat class, and the
    'config' block is passed to its constructor.
    """
    name: str = "override_me"  # Subclasses MUST override this class attribute
    config: DictConfig

    def __init__(self, config: DictConfig):
        """
        Initializes the Boat with its specific configuration block from the Ch-obolo file.
        param config: A DictConfig object containing the configuration for this boat.
        """
        self.config = config

    @abstractmethod
    def connect(self) -> None:
        """Connect to the external inventory provider."""
        raise NotImplementedError

    @abstractmethod
    def check_connection(self) -> bool:
        """Check if the connection to the external provider is active."""
        raise NotImplementedError

    @abstractmethod
    def get_fleet_config(self) -> dict:
        """
        Handles the retrieval of the fleet configuration from the external provider.
        This method should return a dictionary representing the fleet configuration.
        """
        raise NotImplementedError

    @abstractmethod
    def handle_boat_logic(self, fleet_config: dict) -> dict:
        """
        Handle any boat-specific logic for managing the fleet.
        This method should take the current fleet configuration as input,
        perform any necessary operations, and return the hosts to be added.
        """
        raise NotImplementedError

    def get_fleet(self, old_state: DictConfig) -> DictConfig:
        """
        Orchestrates the process of fetching and merging dynamic fleet configuration.
        :param old_state: The existing OmegaConf configuration state.
        :return: A new state with the dynamic hosts merged in.
        :raises ConnectionError: If the boat fails to connect to its provider.
        """
        if not self.check_connection():
            raise ConnectionError(
                f"Boat provider '{self.__class__.name}' failed to establish a connection."
            )

        this_fleet_config = self.get_fleet_config()
        hosts_to_add = self.handle_boat_logic(this_fleet_config)

        configured_hosts = OmegaConf.create({"fleet": {"hosts": hosts_to_add}})
        merged_hosts = DictConfig(OmegaConf.merge(old_state, configured_hosts))

        return merged_hosts
