"""Abstract base class definition for Ch-aOS execution roles."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pyinfra.api.host import Host
    from pyinfra.api.state import State

from chaos.lib.args.dataclasses import Delta, ResultPayload


class Role(ABC):
    """Abstract base class for roles in the Ch-aOS framework.

    Notes:
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
        name: str,
        needs_secrets: bool = False,
        necessary_chobolo_keys: list[str] = [],
        necessary_secret_dict_keys: list[str] = [],
    ):
        """Initializes a Role.

        Args:
            name (str): The name of the role.
            needs_secrets (bool, optional): Indicates if the role requires secrets to operate. Defaults to False.
            necessary_chobolo_keys (list[str], optional): The list of configuration keys required from the chobolo state. Defaults to [].
            necessary_secret_dict_keys (list[str], optional): The list of secret keys required from the secrets store. Defaults to [].
        """
        self.name = name
        self.needs_secrets = needs_secrets
        self.necessary_chobolo_keys = necessary_chobolo_keys
        self.necessary_secret_dict_keys = necessary_secret_dict_keys

    def get_context(
        self,
        state: State,
        host: Host,
        chobolo: dict[str, Any] = {},
        secrets: dict[str, Any] = {},
    ) -> dict[str, Any]:
        """Optional method to implement for roles that require context data from the system.

        Args:
            state: Pyinfra state object.
            host: Pyinfra host object.
            chobolo (dict, optional): The desired state of the system as represented in the Chobolo.
                It contains only the keys specified in the "necessary_chobolo_keys" attribute of the role
                merged with the secret keys specified in the "necessary_secret_dict_keys" attribute of the role. Defaults to {}.
            secrets (dict[str, Any], optional): The secrets required for the role, if any. Defaults to {}.

        Returns:
            dict[str, Any]: A dictionary containing the context for the role.

        Notes:
            This method should be implemented by subclasses to return the necessary data and
            information present in the system for the specific context of the role.
        """
        return {}

    def delta(self, context: dict[str, Any] = {}) -> Delta:
        """Optional method to implement for roles that require calculating a delta to achieve their goals.

        Args:
            context (dict[str, Any], optional): The context for the role, as returned by the get_context method. Defaults to {}.

        Returns:
            Delta: A Delta object containing the actions needed to achieve the desired state.

        Notes:
            This method should be implemented by subclasses to calculate what it needs to do to
            achieve its goals based on the current context and the desired state.
        """

        return Delta(to_add={"force_run": "this"}, to_remove={}, metadata={})

    @abstractmethod
    def plan(self, state: State, host: Host, delta: Delta = Delta()) -> ResultPayload:
        """Plan the actions needed to achieve the desired state.

        Args:
            state: Pyinfra state object.
            host: Pyinfra host object.
            delta (Delta, optional): The delta for the role, as returned by the delta method. Defaults to Delta().

        Returns:
            ResultPayload: A ResultPayload object containing the result of the operation addition process
                including relevant data.

        Notes:
            This method should be implemented by subclasses to stack the actions needed in
            pyinfra operations to achieve the desired state.
        """

        return ResultPayload(success=False, message=[], error=[], data={})
