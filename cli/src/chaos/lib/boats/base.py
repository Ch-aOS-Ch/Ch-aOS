"""Base definitions and abstrac) -> list[dict[str, str | intoat resource provisioner plugins."""

from abc import ABC, abstractmethod
from typing import Any

from omegaconf import DictConfig, OmegaConf


class Boat(ABC):
    """Abstract base class representing a generic boat.

    Notes:
        A boat represents a dynamic provider for the fleet management system.
        This means that each boat has to implement methods to manage its lifecycle
        which include:
        connecting to an external inventory provider (e.g., ec2)
        getting the current state of the fleet
        creating new instances
        returning instances to the pool to list of fleets.

        A boat is configured in a Ch-obolo file like so:
        ```yaml
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
        ```

        The 'provider' name is used to find the corresponding Boat class, and the
        'config' block is passed to its constructor.
    """

    config: DictConfig

    @property
    @abstractmethod
    def name(self) -> str:
        """The name of the boat provider, used to match against the Ch-obolo configuration."""
        raise NotImplementedError

    def __init__(self, config: DictConfig):
        """Initializes the Boat with its specific configuration block from the Ch-obolo file.

        Args:
            config (DictConfig): A DictConfig object containing the configuration for this boat.
        """
        self.config = config

    @abstractmethod
    def check_connection(self) -> bool:
        """Checks if the connection to the external provider is active.

        Returns:
            bool: True if the connection is successfully verified.
        """
        raise NotImplementedError

    @abstractmethod
    def get_fleet_config(self) -> dict[str, Any]:
        """Handles the retrieval of the fleet configuration from the external provider.

        Returns:
            dict: A dictionary representing the fleet configuration parameters.
        """
        raise NotImplementedError

    @abstractmethod
    def handle_boat_logic(self, fleet_config: dict[str, Any]) -> list[dict[str, Any]]:
        """Handles any boat-specific logic for managing the fleet.

        Args:
            fleet_config (dict): The current extracted parameters detailing external fleet state representation.

        Returns:
            dict | list: Processed structured mapped objects (like hosts arrays) needed to inject back to original state maps.
        """
        raise NotImplementedError

    def get_fleet(self, old_state: DictConfig) -> DictConfig:
        """Orchestrates the process of fetching and merging dynamic fleet configuration.

        Args:
            old_state (DictConfig): The existing OmegaConf configuration state.

        Returns:
            DictConfig: A new state with the dynamic hosts merged in.

        Raises:
            ConnectionError: If the boat fails to connect to its provider.
            ValueError: If mapping properties returned fall out of bounds representation rules.
        """
        if not self.check_connection():
            raise ConnectionError(
                f"Boat provider '{self.__class__.name}' failed to establish a connection."
            )

        this_fleet_config = self.get_fleet_config()
        hosts_to_add = self.handle_boat_logic(this_fleet_config)

        if isinstance(hosts_to_add, dict):
            hosts_to_add = [hosts_to_add]

        if not isinstance(hosts_to_add, list):
            raise ValueError(
                f"Boat provider '{self.__class__.name}' returned invalid hosts format."
            )

        current_hosts = old_state.get("fleet", {}).get("hosts", [])
        merged_hosts = current_hosts + hosts_to_add

        new_state = DictConfig(
            OmegaConf.create(OmegaConf.to_container(old_state, resolve=True))
        )
        new_state.fleet.hosts = merged_hosts

        return new_state
