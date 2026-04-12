from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pulumi import ComponentResource, ResourceOptions


class Isle(ComponentResource, ABC):
    """
    Abstract base class representing an Isle in the Ch-aOS framework.
    An Isle is a modular component that can be provisioned, destroyed, and queried for status.
    """

    secrets_needed: list[str] = []
    isle_name: str = "unnamed_isle"

    def __init__(
        self,
        name: str,
        config: dict[str, Any] | None = None,
        opts: ResourceOptions | None = None,
    ) -> None:
        """
        Initializes the Isle with the given configuration.

        Args:
            name (str): The name of the Isle.
            config (dict[str, Any]): A dictionary containing configuration parameters for the Isle.
            opts (ResourceOptions | None): Optional Pulumi resource options for the Isle.
        """
        config = config or {}
        super().__init__(f"pelago:isle:{self.__class__.__name__}", name, None, opts)

        self.build_resources(config)

        self.register_outputs(
            {
                "isle_name": name,
            }
        )

    @abstractmethod
    def build_resources(self, config: dict[str, Any]) -> None:
        """
        Abstract method to be implemented by subclasses to build the resources for the Isle.

        Args:
            config (dict[str, Any]): A dictionary containing configuration parameters for the Isle.
        """
        pass
