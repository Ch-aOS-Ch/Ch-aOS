from __future__ import annotations

from abc import ABC, abstractmethod


class Isle(ABC):
    """
    Abstract base class representing an Isle in the Ch-aOS framework.
    An Isle is a modular component that can be provisioned, destroyed, and queried for status.
    """

    @abstractmethod
    def provision(self) -> None:
        """
        Provisions the Isle, setting up necessary resources and configurations.
        """
        pass

    @abstractmethod
    def destroy(self) -> None:
        """
        Destroys the Isle, cleaning up any resources that were provisioned.
        """
        pass

    @abstractmethod
    def status(self) -> str:
        """
        Returns the current status of the Isle.
        """
        pass
