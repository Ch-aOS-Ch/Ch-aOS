from abc import ABC, abstractmethod
from typing import Any

from chaos.lib.args.dataclasses import Delta, ResultPayload


class Role(ABC):
    """
    Abstract base class for roles in the Ch-aOS framework.

    Each role must implement the "get_context", "delta" and "plan" methods to define
        its behavior and interactions for system management and orchestration.

    get_context: This method should return the necessary data and information present
        in the system for the specific context of the role.

    delta: This method should calculate what it needs to do to achieve its goals based
        on the current context and the desired state.

    plan: This method should only stack the actions needed in pyinfra operations to achieve
        the desired state.
    """

    def __init__(
        self,
        needs_secrets: bool = False,
        necessary_chobolo_keys: list[str] = [],
        necessary_secret_dict_keys: list[str] = [],
    ):
        self.necessary_chobolo_keys = necessary_chobolo_keys
        self.needs_secrets = needs_secrets
        self.necessary_secret_dict_keys = necessary_secret_dict_keys

    @abstractmethod
    def get_context(
        self, state, host, chobolo: dict = {}, secrets: dict[str, Any] = {}
    ) -> dict[str, Any]:
        """
        Get the context for the role.
        This method should be implemented by subclasses to return the necessary data and
            information present in the system for the specific context of the role.

        Args:
            chobolo (dict): The current state of the system as represented in the Chobolo.
                It contains only the keys specified in the "necessary_chobolo_keys" attribute of the role
                merged with the secret keys specified in the "necessary_secret_dict_keys" attribute of the role.
            secrets (dict): The secrets required for the role, if any.
            state: Pyinfra state object.
            host: Pyinfra host object.

        Returns:
            dict: A dictionary containing the context for the role.
        """
        return {}

    @abstractmethod
    def delta(self, context: dict[str, Any] = {}) -> Delta:
        """
        Calculate the delta for the role.

        This method should be implemented by subclasses to calculate what it needs to do to
            achieve its goals based on the current context and the desired state.

        Args:
            context (dict): The context for the role, as returned by the get_context method.

        Returns:
            Delta: A Delta object containing the actions needed to achieve the desired state.
        """

        return Delta(to_add={}, to_remove={}, metadata={})

    @abstractmethod
    def plan(self, state, host, delta: Delta = Delta()) -> ResultPayload:
        """
        Plan the actions needed to achieve the desired state.
        This method should be implemented by subclasses to stack the actions needed in
        pyinfra operations to achieve the desired state.

        Args:
            delta (Delta): The delta for the role, as returned by the delta method.
            state: Pyinfra state object.
            host: Pyinfra host object.

        Returns:
            ResultPayload: A ResultPayload object containing the result of the operation addition process
                including relevant data.
        """

        return ResultPayload(success=False, message=[], error=[], data={})
