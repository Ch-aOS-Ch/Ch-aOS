from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generic, Literal, Self, TypeVar

if TYPE_CHECKING:
    from pyinfra.api.state import State

T = TypeVar("T", covariant=True)

"""
Custom made dataclasses implementation, optimized for CLI startup and import time performance.

Notes:
    All classes in this module inherit from BasePayload, which provides the following methods:
"""


def _serialize(value: Any):
    if isinstance(value, BasePayload):
        return value.to_dict()

    if isinstance(value, list):
        return [_serialize(v) for v in value]

    if isinstance(value, dict):
        return {k: _serialize(v) for k, v in value.items()}

    return value


class BasePayload:
    """
    Base class for all payloads.

    Notes:
        These are mutable DTOs optimized for CLI startup performance.
        We use __slots__ instead of dataclasses to keep import time minimal.

    Methods:
        __repr__: A string representation of the object, useful for debugging.

        __eq__: A method to compare two payload objects for equality.

        to_dict: A method to convert the object to a dictionary recursively, useful for serialization.

        from_dict(dict[str, Any]): A class method to create a payload object from a dictionary, useful for deserialization.
            Please note that from_dict is NOT recursive, and will not convert nested dicts to payloads.
    """

    __slots__ = ()

    def __repr__(self) -> str:
        attrs = ", ".join(f"{slot}={getattr(self, slot)!r}" for slot in self.__slots__)
        return f"{self.__class__.__name__}({attrs})"

    def __eq__(self, other: Any) -> bool:
        if self.__class__ is not other.__class__:
            return NotImplemented

        return all(
            getattr(self, slot) == getattr(other, slot) for slot in self.__slots__
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert payload to dictionary, recursively converting nested payloads."""

        return {s: _serialize(getattr(self, s)) for s in self.__slots__}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        return cls(**{s: data[s] for s in cls.__slots__ if s in data})


class DataGatherRequest(BasePayload):
    """
    This payload is a data gathering request, which is meant to be used as a request to gather data BEFORE the execution of the main
        logic, and it is meant to be used in the "pre" phase of the execution.


    Attributes:
        name: The name of the data gathering request, e.g. "aws_credentials", "kubeconfig", etc.
        fields: A list of DataGatherPayload objects, each representing a piece of data that needs to be gathered for this request.


    Notes:
        I KNOW its another layer of indirection. This is necessary for the interfaces to be able to group multiple data gathering fields
            under the same request, and to be able to show them to the user in a more organized way.


        Yes, I know I could just use return[DGP(), DGP(), DGP()] instead of return[DGR("aws_credentials", [DGP(), DGP()])], but this way
            we can have a name for the group of data being gathered, which can be useful for the interfaces to show a more user-friendly message
            to the user.
    """

    __slots__ = ("name", "fields")

    def __init__(
        self,
        name: str,
        fields: list[DataGatherPayload],
    ):
        self.name = name
        self.fields = fields


class Delta(BasePayload):
    """
    Delta Payload, used as return by the Role.delta() method.

    Attributes:
        to_add(dict[str, Any]): prettified dict for showing what is being changed as an ADDITION in CLI
        to_remove(dict[str, Any]): prettified dict for showing what is being changed as an REMOVAL in CLI
        metadata(dict[str, Any]): Other data (will not be shown in CLI)
    """

    __slots__ = ("to_add", "to_remove", "metadata")

    def __init__(
        self,
        to_add: dict[str, Any] | None = None,
        to_remove: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        self.to_add = to_add or {}
        self.to_remove = to_remove or {}
        self.metadata = metadata or {}


class DataGatherPayload(BasePayload):
    """
    This payload is a data gathering payload, which is meant to gather data BEFORE the execution of the main
        logic, and it is meant to be used in the "pre" phase of the execution.


    Attributes:
        name: The name of the data being gathered, e.g. "aws_credentials", "kubeconfig", etc.
        prompt: The prompt to show to the user when asking for the data, e.g. "Please enter your AWS credentials".
        input_type: The type of input expected, should be used by the CLI to manage how to gather the data.
          e.g. if input_type is "choice", the interface should show the choices to the user and let them select one, if it's "secret",
          the interface should hide the input, etc.
        required: A boolean indicating whether the data is required or not, if it's required, the interface should keep asking for the
          data until it is provided, if it's not required, the user should be able to skip it.
        default: The default value to use if the user decides to skip providing the data, should only be used if required is False.
        choices: A list of choices to show to the user if the input_type is "choice", should be None otherwise.
        metadata: A dictionary containing any additional information that might be useful for the interface when gathering the data,
            e.g. if the input_type is "secret", the metadata might contain information about how to validate the secret, etc.
    """

    __slots__ = (
        "name",
        "prompt",
        "input_type",
        "required",
        "default",
        "choices",
        "metadata",
    )

    def __init__(
        self,
        prompt: str | None = None,
        name: str | None = None,
        input_type: Literal[
            "string", "integer", "boolean", "choice", "secret"
        ] = "string",
        required: bool = False,
        default: Any = None,
        choices: list[Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        self.name = name
        self.prompt = prompt
        self.input_type = input_type
        self.required = required
        self.default = default
        self.choices = choices
        self.metadata = metadata


class ResultPayload(BasePayload, Generic[T]):
    """
    This payload is meant to be used as a STANDARD RETURN TYPE for all API calls in the library, and it should
        be used as such in the future for all API calls.


    Attributes:
        success: A boolean indicating whether the operation was successful or not.
        message: A list of strings containing any messages that should be returned to the user.
        data: Any data that should be returned to the user, can be of any type
        error: A list of strings containing any error messages that should be returned to the user.
    """

    __slots__ = (
        "success",
        "message",
        "data",
        "error",
    )

    def __init__(
        self,
        success: bool,
        message: list[str] | None = None,
        data: T | None = None,
        error: list[str] | None = None,
    ):
        self.success = success
        self.message = message or []
        self.data = data
        self.error = error or []


class TeamPrunePayload(BasePayload):
    """
    Payload representing TeamPrunePayload.

    Attributes:
        companies (list[str]): The companies attribute.
        i_know_what_im_doing (bool): The i_know_what_im_doing attribute.
        confirmed (bool): The confirmed attribute.
    """

    __slots__ = ("companies", "i_know_what_im_doing", "confirmed")

    def __init__(
        self, companies: list[str], i_know_what_im_doing: bool, confirmed: bool = False
    ):
        self.companies = companies
        self.i_know_what_im_doing = i_know_what_im_doing
        self.confirmed = confirmed


class TeamListPayload(BasePayload):
    """
    Payload representing TeamListPayload.

    Attributes:
        company (str | None): The company attribute.
        no_pretty (bool): The no_pretty attribute.
        json (bool): The json attribute.
    """

    __slots__ = ("company", "no_pretty", "json")

    def __init__(self, company: str | None, no_pretty: bool, json: bool):
        self.company = company
        self.no_pretty = no_pretty
        self.json = json


class TeamClonePayload(BasePayload):
    """
    Payload representing TeamClonePayload.

    Attributes:
        target (str): The target attribute.
        path (str | None): The path attribute.
    """

    __slots__ = ("target", "path")

    def __init__(self, target: str, path: str | None):
        self.target = target
        self.path = path


class TeamInitPayload(BasePayload):
    """
    Payload representing TeamInitPayload.

    Attributes:
        target (str): The target attribute.
        path (str | None): The path attribute.
        i_know_what_im_doing (bool): The i_know_what_im_doing attribute.
        confirmed (bool): The confirmed attribute.
        init_git (bool): The init_git attribute.
        overwrite_sops (bool): The overwrite_sops attribute.
        engine (str | None): The engine attribute.
        use_vault (bool): The use_vault attribute.
        continue_no_vault (bool): The continue_no_vault attribute.
    """

    __slots__ = (
        "target",
        "path",
        "i_know_what_im_doing",
        "confirmed",
        "init_git",
        "overwrite_sops",
        "engine",
        "use_vault",
        "continue_no_vault",
    )

    def __init__(
        self,
        target: str,
        path: str | None,
        i_know_what_im_doing: bool,
        confirmed: bool = False,
        init_git: bool = False,
        overwrite_sops: bool = False,
        engine: str | None = None,
        use_vault: bool = False,
        continue_no_vault: bool = False,
    ):
        self.target = target
        self.path = path
        self.i_know_what_im_doing = i_know_what_im_doing
        self.confirmed = confirmed
        self.init_git = init_git
        self.overwrite_sops = overwrite_sops
        self.engine = engine
        self.use_vault = use_vault
        self.continue_no_vault = continue_no_vault


class TeamActivatePayload(BasePayload):
    """
    Payload representing TeamActivatePayload.

    Attributes:
        path (str | None): The path attribute.
    """

    __slots__ = ("path",)

    def __init__(self, path: str | None):
        self.path = path


class TeamDeactivatePayload(BasePayload):
    """
    Payload representing TeamDeactivatePayload.

    Attributes:
        company (str): The company attribute.
        teams (list[str]): The teams attribute.
        confirmed (bool): The confirmed attribute.
    """

    __slots__ = ("company", "teams", "confirmed")

    def __init__(self, company: str, teams: list[str], confirmed: bool = False):
        self.company = company
        self.teams = teams
        self.confirmed = confirmed


class ExplainPayload(BasePayload):
    """
    Payload representing ExplainPayload.

    Attributes:
        topics (list[str]): The topics attribute.
        no_pretty (bool): The no_pretty attribute.
        json (bool): The json attribute.
        details (str): The details attribute.
        complexity (str): The complexity attribute.
    """

    __slots__ = ("topics", "no_pretty", "json", "details", "complexity")

    def __init__(
        self,
        topics: list[str],
        no_pretty: bool,
        json: bool,
        details: str = "basic",
        complexity: str = "basic",
    ):
        self.topics = topics
        self.no_pretty = no_pretty
        self.json = json
        self.details = details
        self.complexity = complexity


class SetPayload(BasePayload):
    """
    Payload representing SetPayload.

    Attributes:
        chobolo_file (str | None): The chobolo_file attribute.
        sops_file (str | None): The sops_file attribute.
        secrets_file (str | None): The secrets_file attribute.
    """

    __slots__ = ("chobolo_file", "sops_file", "secrets_file")

    def __init__(
        self,
        chobolo_file: str | None,
        sops_file: str | None,
        secrets_file: str | None,
    ):
        self.chobolo_file = chobolo_file
        self.sops_file = sops_file
        self.secrets_file = secrets_file


class CheckPayload(BasePayload):
    """
    Payload representing CheckPayload.

    Attributes:
        checks (Literal[explanations, roles, aliases, providers, boats, secrets, limanis, templates]): The checks attribute.
        chobolo (str | None): The chobolo attribute.
        json (bool): The json attribute.
        team (str | None): The team attribute.
        sops_file_override (str | None): The sops_file_override attribute.
        secrets_file_override (str | None): The secrets_file_override attribute.
        update_plugins (bool): The update_plugins attribute.
    """

    __slots__ = (
        "checks",
        "chobolo",
        "json",
        "team",
        "sops_file_override",
        "secrets_file_override",
        "update_plugins",
    )

    def __init__(
        self,
        checks: Literal[
            "explanations",
            "roles",
            "aliases",
            "providers",
            "boats",
            "secrets",
            "limanis",
            "templates",
        ],
        chobolo: str | None,
        json: bool,
        team: str | None,
        sops_file_override: str | None,
        secrets_file_override: str | None,
        update_plugins: bool,
    ):
        self.checks = checks
        self.chobolo = chobolo
        self.json = json
        self.team = team
        self.sops_file_override = sops_file_override
        self.secrets_file_override = secrets_file_override
        self.update_plugins = update_plugins


class StyxPayload(BasePayload):
    """
    Payload representing StyxPayload.

    Attributes:
        styx_commands (Literal[invoke, list, destroy]): The styx_commands attribute.
        entries (list[str]): The entries attribute.
        no_pretty (bool): The no_pretty attribute.
        json (bool): The json attribute.
    """

    __slots__ = ("styx_commands", "entries", "no_pretty", "json")

    def __init__(
        self,
        styx_commands: Literal["invoke", "list", "destroy"],
        entries: list[str],
        no_pretty: bool,
        json: bool,
    ):
        self.styx_commands = styx_commands
        self.entries = entries
        self.no_pretty = no_pretty
        self.json = json


class InitPayload(BasePayload):
    """
    Payload representing InitPayload.

    Attributes:
        init_command (Literal[chobolo, secrets]): The init_command attribute.
        update_plugins (bool): The update_plugins attribute.
        targets (list[str]): The targets attribute.
        template (bool): The template attribute.
        human (bool): The human attribute.
    """

    __slots__ = ("init_command", "update_plugins", "targets", "template", "human")

    def __init__(
        self,
        init_command: Literal["chobolo", "secrets"],
        update_plugins: bool,
        targets: list[str],
        template: bool,
        human: bool,
    ):
        self.init_command = init_command
        self.update_plugins = update_plugins
        self.targets = targets
        self.template = template
        self.human = human


class ProviderConfigPayload(BasePayload):
    """
    Payload representing ProviderConfigPayload.

    Attributes:
        provider (str | None): The provider attribute.
        ephemeral_provider_args (dict[str, Any] | None): The ephemeral_provider_args attribute.
    """

    __slots__ = ("provider", "ephemeral_provider_args")

    @classmethod
    def from_dict_or_self(
        cls, value: ProviderConfigPayload | dict[str, Any]
    ) -> ProviderConfigPayload:
        if isinstance(value, cls):
            return value

        elif isinstance(value, dict):
            if "provider_config" in value and isinstance(
                value["provider_config"], dict
            ):
                value["provider_config"] = ProviderConfigPayload.from_dict(
                    value["provider_config"]
                )

            return cls.from_dict(value)

        raise TypeError(f"Expected {cls.__name__} or dict, got {type(value)}")

    def __init__(
        self,
        provider: str | None = None,
        ephemeral_provider_args: dict[str, Any] | None = None,
    ):
        self.provider = provider
        self.ephemeral_provider_args = (
            ephemeral_provider_args if ephemeral_provider_args is not None else {}
        )


class SecretsContext(BasePayload):
    """
    Payload representing SecretsContext.

    Attributes:
        team (str | None): The team attribute.
        sops_file_override (str | None): The sops_file_override attribute.
        secrets_file_override (str | None): The secrets_file_override attribute.
        provider_config (ProviderConfigPayload | dict[str, Any] | None): The provider_config attribute.
        i_know_what_im_doing (bool): The i_know_what_im_doing attribute.
    """

    __slots__ = (
        "team",
        "sops_file_override",
        "secrets_file_override",
        "provider_config",
        "i_know_what_im_doing",
    )

    def __init__(
        self,
        team: str | None = None,
        sops_file_override: str | None = None,
        secrets_file_override: str | None = None,
        provider_config: ProviderConfigPayload | dict[str, Any] | None = None,
        i_know_what_im_doing: bool = False,
    ):
        self.team = team
        self.sops_file_override = sops_file_override
        self.secrets_file_override = secrets_file_override
        self.provider_config = (
            ProviderConfigPayload.from_dict_or_self(provider_config)
            if provider_config is not None
            else None
        )
        self.i_know_what_im_doing = i_know_what_im_doing

    @classmethod
    def from_dict_or_self(
        cls, value: SecretsContext | dict[str, Any]
    ) -> SecretsContext:
        if isinstance(value, cls):
            return value

        elif isinstance(value, dict):
            if "provider_config" in value and isinstance(
                value["provider_config"], dict
            ):
                value["provider_config"] = ProviderConfigPayload.from_dict(
                    value["provider_config"]
                )

            return cls.from_dict(value)
        raise TypeError(f"Expected {cls.__name__} or dict, got {type(value)}")


class ProviderExportArgs(BasePayload):
    """
    Payload representing ProviderExportArgs.

    Attributes:
    """

    __slots__ = ()

    def __init__(self):
        pass


class ProviderImportArgs(BasePayload):
    """
    Payload representing ProviderImportArgs.

    Attributes:
    """

    __slots__ = ()

    def __init__(self):
        pass


class SecretsExportPayload(BasePayload):
    """
    Payload representing SecretsExportPayload.

    Attributes:
        provider_name (str): The provider_name attribute.
        key_type (Literal[age, gpg, vault]): The key_type attribute.
        no_import (bool): The no_import attribute.
        save_to_config (bool): The save_to_config attribute.
        item_name (str | None): The item_name attribute.
        keys (str | None): The keys attribute.
        vault_addr (str | None): The vault_addr attribute.
        fingerprints (list[str] | None): The fingerprints attribute.
        provider_specific_args (ProviderExportArgs | None): The provider_specific_args attribute.
    """

    __slots__ = (
        "provider_name",
        "key_type",
        "no_import",
        "save_to_config",
        "item_name",
        "keys",
        "vault_addr",
        "fingerprints",
        "provider_specific_args",
    )

    def __init__(
        self,
        provider_name: str,
        key_type: Literal["age", "gpg", "vault"],
        no_import: bool,
        save_to_config: bool,
        item_name: str | None = None,
        keys: str | None = None,
        vault_addr: str | None = None,
        fingerprints: list[str] | None = None,
        provider_specific_args: ProviderExportArgs | None = None,
    ):
        self.provider_name = provider_name
        self.key_type = key_type
        self.no_import = no_import
        self.save_to_config = save_to_config
        self.item_name = item_name
        self.keys = keys
        self.vault_addr = vault_addr
        self.fingerprints = fingerprints
        self.provider_specific_args = (
            provider_specific_args
            if provider_specific_args is not None
            else ProviderExportArgs()
        )


class SecretsImportPayload(BasePayload):
    """
    Payload representing SecretsImportPayload.

    Attributes:
        provider_name (str): The provider_name attribute.
        key_type (Literal[age, gpg, vault]): The key_type attribute.
        item_id (str | None): The item_id attribute.
        provider_specific_args (ProviderImportArgs | None): The provider_specific_args attribute.
        confirmed (bool): The confirmed attribute.
    """

    __slots__ = (
        "provider_name",
        "key_type",
        "item_id",
        "provider_specific_args",
        "confirmed",
    )

    def __init__(
        self,
        provider_name: str,
        key_type: Literal["age", "gpg", "vault"],
        item_id: str | None = None,
        provider_specific_args: ProviderImportArgs | None = None,
        confirmed: bool = False,
    ):
        self.provider_name = provider_name
        self.key_type = key_type
        self.item_id = item_id
        self.confirmed = confirmed
        self.provider_specific_args = (
            provider_specific_args
            if provider_specific_args is not None
            else ProviderImportArgs()
        )


class SecretsRotatePayload(BasePayload):
    """
    Payload representing SecretsRotatePayload.

    Attributes:
        type (Literal[age, pgp, vault]): The type attribute.
        keys (list[str]): The keys attribute.
        context (SecretsContext | dict[str, Any]): The context attribute.
        index (int | None): The index attribute.
        pgp_server (str | None): The pgp_server attribute.
        create (bool): The create attribute.
        update_confirmed (bool): The update_confirmed attribute.
    """

    __slots__ = (
        "type",
        "keys",
        "context",
        "index",
        "pgp_server",
        "create",
        "update_confirmed",
    )

    def __init__(
        self,
        type: Literal["age", "pgp", "vault"],
        keys: list[str],
        context: SecretsContext | dict[str, Any],
        index: int | None = None,
        pgp_server: str | None = None,
        create: bool = False,
        update_confirmed: bool = False,
    ):
        self.type = type
        self.keys = keys
        self.index = index
        self.pgp_server = pgp_server
        self.create = create
        self.update_confirmed = update_confirmed

        self.context = SecretsContext.from_dict_or_self(context)


class SecretsListPayload(BasePayload):
    """
    Payload representing SecretsListPayload.

    Attributes:
        type (Literal[age, pgp, vault]): The type attribute.
        context (SecretsContext | dict[str, Any]): The context attribute.
        no_pretty (bool): The no_pretty attribute.
        json (bool): The json attribute.
        value (bool): The value attribute.
    """

    __slots__ = ("type", "context", "no_pretty", "json", "value")

    def __init__(
        self,
        type: Literal["age", "pgp", "vault"],
        context: SecretsContext | dict[str, Any],
        no_pretty: bool = False,
        json: bool = False,
        value: bool = False,
    ):
        self.type = type
        self.no_pretty = no_pretty
        self.json = json
        self.value = value

        self.context = SecretsContext.from_dict_or_self(context)


class SecretsEditPayload(BasePayload):
    """
    Payload representing SecretsEditPayload.

    Attributes:
        context (SecretsContext | dict[str, Any]): The context attribute.
        edit_sops_file (bool): The edit_sops_file attribute.
    """

    __slots__ = ("context", "edit_sops_file")

    def __init__(
        self, context: SecretsContext | dict[str, Any], edit_sops_file: bool = False
    ):
        self.edit_sops_file = edit_sops_file

        self.context = SecretsContext.from_dict_or_self(context)


class SecretsPrintPayload(BasePayload):
    """
    Payload representing SecretsPrintPayload.

    Attributes:
        context (SecretsContext | dict[str, Any]): The context attribute.
        print_sops_file (bool): The print_sops_file attribute.
        as_json (bool): The as_json attribute.
    """

    __slots__ = ("context", "print_sops_file", "as_json")

    def __init__(
        self,
        context: SecretsContext | dict[str, Any],
        print_sops_file: bool = False,
        as_json: bool = False,
    ):
        self.print_sops_file = print_sops_file
        self.as_json = as_json

        self.context = SecretsContext.from_dict_or_self(context)


class SecretsCatPayload(BasePayload):
    """
    Payload representing SecretsCatPayload.

    Attributes:
        keys (list[str]): The keys attribute.
        context (SecretsContext | dict[str, Any]): The context attribute.
        cat_sops_file (bool): The cat_sops_file attribute.
        as_json (bool): The as_json attribute.
        value_only (bool): The value_only attribute.
    """

    __slots__ = ("keys", "context", "cat_sops_file", "as_json", "value_only")

    def __init__(
        self,
        keys: list[str],
        context: SecretsContext | dict[str, Any],
        cat_sops_file: bool = False,
        as_json: bool = False,
        value_only: bool = False,
    ):
        self.keys = keys
        self.cat_sops_file = cat_sops_file
        self.as_json = as_json
        self.value_only = value_only

        self.context = SecretsContext.from_dict_or_self(context)


class SecretsSetShamirPayload(BasePayload):
    """
    Payload representing SecretsSetShamirPayload.

    Attributes:
        index (int): The index attribute.
        share (int): The share attribute.
        context (SecretsContext | dict[str, Any]): The context attribute.
        confirmed (bool): The confirmed attribute.
        update_confirmed (bool): The update_confirmed attribute.
    """

    __slots__ = ("index", "share", "context", "confirmed", "update_confirmed")

    def __init__(
        self,
        index: int,
        share: int,
        context: SecretsContext | dict[str, Any],
        confirmed: bool = False,
        update_confirmed: bool = False,
    ):
        self.index = index
        self.share = share
        self.confirmed = confirmed
        self.update_confirmed = update_confirmed
        self.context = SecretsContext.from_dict_or_self(context)


class RambleCreatePayload(BasePayload):
    """
    Payload representing RambleCreatePayload.

    Attributes:
        target (str): The target attribute.
        context (SecretsContext | dict[str, Any]): The context attribute.
        encrypt (bool): The encrypt attribute.
        keys (list[str] | None): The keys attribute.
        confirmed (bool): The confirmed attribute.
    """

    __slots__ = ("target", "context", "encrypt", "keys", "confirmed")

    def __init__(
        self,
        target: str,
        context: SecretsContext | dict[str, Any],
        encrypt: bool,
        keys: list[str] | None = None,
        confirmed: bool = False,
    ):
        self.target = target
        self.encrypt = encrypt
        self.keys = keys
        self.confirmed = confirmed

        self.context = SecretsContext.from_dict_or_self(context)


class RambleEditPayload(BasePayload):
    """
    Payload representing RambleEditPayload.

    Attributes:
        target (str): The target attribute.
        context (SecretsContext | dict[str, Any]): The context attribute.
        edit_sops_file (bool): The edit_sops_file attribute.
    """

    __slots__ = ("target", "context", "edit_sops_file")

    def __init__(
        self,
        target: str,
        context: SecretsContext | dict[str, Any],
        edit_sops_file: bool = False,
    ):
        self.target = target
        self.edit_sops_file = edit_sops_file

        self.context = SecretsContext.from_dict_or_self(context)


class RambleEncryptPayload(BasePayload):
    """
    Payload representing RambleEncryptPayload.

    Attributes:
        target (str): The target attribute.
        context (SecretsContext | dict[str, Any]): The context attribute.
        keys (list[str] | None): The keys attribute.
    """

    __slots__ = ("target", "context", "keys")

    def __init__(
        self,
        target: str,
        context: SecretsContext | dict[str, Any],
        keys: list[str] | None = None,
    ):
        self.target = target
        self.keys = keys

        self.context = SecretsContext.from_dict_or_self(context)


class RambleReadPayload(BasePayload):
    """
    Payload representing RambleReadPayload.

    Attributes:
        targets (list[str]): The targets attribute.
        context (SecretsContext | dict[str, Any]): The context attribute.
        no_pretty (bool): The no_pretty attribute.
        json (bool): The json attribute.
        values (list[str] | None): The values attribute.
    """

    __slots__ = ("targets", "context", "no_pretty", "json", "values")

    def __init__(
        self,
        targets: list[str],
        context: SecretsContext | dict[str, Any],
        no_pretty: bool = False,
        json: bool = False,
        values: list[str] | None = None,
    ):
        self.targets = targets
        self.no_pretty = no_pretty
        self.json = json
        self.values = values

        self.context = SecretsContext.from_dict_or_self(context)


class RambleFindPayload(BasePayload):
    """
    Payload representing RambleFindPayload.

    Attributes:
        context (SecretsContext | dict[str, Any]): The context attribute.
        find_term (str | None): The find_term attribute.
        tag (str | None): The tag attribute.
        no_pretty (bool): The no_pretty attribute.
        json (bool): The json attribute.
    """

    __slots__ = ("context", "find_term", "tag", "no_pretty", "json")

    def __init__(
        self,
        context: SecretsContext | dict[str, Any],
        find_term: str | None = None,
        tag: str | None = None,
        no_pretty: bool = False,
        json: bool = False,
    ):
        self.find_term = find_term
        self.tag = tag
        self.no_pretty = no_pretty
        self.json = json

        self.context = SecretsContext.from_dict_or_self(context)


class RambleMovePayload(BasePayload):
    """
    Payload representing RambleMovePayload.

    Attributes:
        old (str): The old attribute.
        new (str): The new attribute.
        context (SecretsContext | dict[str, Any]): The context attribute.
    """

    __slots__ = ("old", "new", "context")

    # Since we use a singular "ramble_context" for all ramble operations,
    # we can reduce code duplication by passing the whole context instead of just the team
    # just be known that we use _only_ the team attribute of the context in the ramble move operation
    def __init__(self, old: str, new: str, context: SecretsContext | dict[str, Any]):
        self.old = old
        self.new = new

        self.context = SecretsContext.from_dict_or_self(context)


class RambleDeletePayload(BasePayload):
    """
    Payload representing RambleDeletePayload.

    Attributes:
        ramble (str): The ramble attribute.
        context (SecretsContext | dict[str, Any]): The context attribute.
        confirmed (bool): The confirmed attribute.
    """

    __slots__ = ("ramble", "context", "confirmed")

    # Same as the above
    def __init__(
        self,
        ramble: str,
        context: SecretsContext | dict[str, Any],
        confirmed: bool = False,
    ):
        self.ramble = ramble
        self.confirmed = confirmed

        self.context = SecretsContext.from_dict_or_self(context)


class RambleUpdateEncryptPayload(BasePayload):
    """
    Payload representing RambleUpdateEncryptPayload.

    Attributes:
        context (SecretsContext | dict[str, Any]): The context attribute.
    """

    __slots__ = ("context",)

    # ye, only context
    def __init__(self, context: SecretsContext | dict[str, Any]):
        self.context = SecretsContext.from_dict_or_self(context)


class ApplyPayload(BasePayload):
    """
    Payload representing ApplyPayload.

    Attributes:
        update_plugins (bool): The update_plugins attribute.
        i_know_what_im_doing (bool): The i_know_what_im_doing attribute.
        dry (bool): The dry attribute.
        verbose (int): The verbose attribute.
        v (int): The v attribute.
        tags (list[str]): The tags attribute.
        chobolo (str | None): The chobolo attribute.
        limani (str | None): The limani attribute.
        logbook (bool): The logbook attribute.
        fleet (bool): The fleet attribute.
        sudo_password_file (str | None): The sudo_password_file attribute.
        password (str | None): The password attribute.
        secrets (bool): The secrets attribute.
        serial (bool): The serial attribute.
        no_wait (bool): The no_wait attribute.
        export_logs (bool): The export_logs attribute.
        secrets_context (SecretsContext | dict[str, Any]): The secrets_context attribute.
        confirmed_password (str): The confirmed_password attribute.
        pyinfra_state (State | None): The pyinfra_state attribute.
        target_hosts (list | None): The target_hosts attribute.
        is_fleet_active (bool): The is_fleet_active attribute.
        parallelism (int): The parallelism attribute.
        fallback_to_local (bool): The fallback_to_local attribute.
        decrypted_secrets (dict[str, Any] | None): The decrypted_secrets attribute.
        global_config (dict[str, Any] | None): The global_config attribute.
    """

    __slots__ = (
        "update_plugins",
        "i_know_what_im_doing",
        "dry",
        "verbose",
        "v",
        "tags",
        "chobolo",
        "limani",
        "logbook",
        "fleet",
        "sudo_password_file",
        "password",
        "secrets",
        "serial",
        "no_wait",
        "export_logs",
        "secrets_context",
        "confirmed_password",
        "pyinfra_state",
        "target_hosts",
        "is_fleet_active",
        "parallelism",
        "fallback_to_local",
        "decrypted_secrets",
        "global_config",
    )

    def __init__(
        self,
        update_plugins: bool,
        i_know_what_im_doing: bool,
        dry: bool,
        verbose: int,
        v: int,
        tags: list[str],
        chobolo: str | None,
        limani: str | None,
        logbook: bool,
        fleet: bool,
        sudo_password_file: str | None,
        password: str | None,
        secrets: bool,
        serial: bool,
        no_wait: bool,
        export_logs: bool,
        secrets_context: SecretsContext | dict[str, Any],
        confirmed_password: str = "",
        pyinfra_state: State | None = None,
        target_hosts: list | None = None,
        is_fleet_active: bool = False,
        parallelism: int = 0,
        fallback_to_local: bool = False,
        decrypted_secrets: dict[str, Any] | None = None,
        global_config: dict[str, Any] | None = None,
    ):
        self.update_plugins = update_plugins
        self.i_know_what_im_doing = i_know_what_im_doing
        self.dry = dry
        self.verbose = verbose
        self.v = v
        self.tags = tags
        self.chobolo = chobolo
        self.limani = limani
        self.logbook = logbook
        self.fleet = fleet
        self.sudo_password_file = sudo_password_file
        self.password = password
        self.secrets = secrets
        self.serial = serial
        self.no_wait = no_wait
        self.export_logs = export_logs
        self.secrets_context = SecretsContext.from_dict_or_self(secrets_context)
        self.confirmed_password = confirmed_password
        self.pyinfra_state = pyinfra_state
        self.target_hosts = target_hosts or ["@local"]
        self.is_fleet_active = is_fleet_active
        self.parallelism = parallelism
        self.fallback_to_local = fallback_to_local
        self.decrypted_secrets = decrypted_secrets or {}
        self.global_config = global_config or {}
