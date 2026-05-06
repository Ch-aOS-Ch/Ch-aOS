from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Generic, Literal, Self, TypeVar

if TYPE_CHECKING:
    from pulumi.automation import Stack
    from pulumi.automation._workspace import PulumiFn
    from pyinfra.api.state import State

T = TypeVar("T", covariant=True)

"""
Custom made dataclasses implementation, optimized for CLI startup and import time performance.

Notes:
    All classes in this module inherit from BasePayload, which provides the following methods:
"""


def _serialize(value: Any) -> Any:
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


class PelagoPayload(BasePayload):
    """
    Payload for executing a Pulumi program via the Pelago interface.
    Attributes:
        stack_name (str): The name of the Pulumi stack to create or select.
        project_name (str): The name of the Pulumi project to use.
        pulumi_program (PulumiFn): The Pulumi program function to execute, which should return a dictionary of outputs.
        stack (Stack): The Pulumi Stack object that is created or selected based on the stack_name and project_name.
        secrets_used (list[str]): A list of secrets that were used during the execution to be tear down later in the finally block.
        pelago (list[dict[str, Any]]): A list of Pelago programs to be executed.
        secrets (bool): A boolean indicating whether secrets are allowed to be used in this pelago run.
        provided_secrets (dict[str, Any]): A dict of secrets that are needed by the pelago programs, which are provided by the user.
        update_plugins (bool): If True, forces a refresh of the plugin cache.
        i_know_what_im_doing (bool): If True, bypasses all interactive confirmation prompts.
        dry (bool): If True, runs in dry-run mode (Pulumi preview).
        verbose (int): The verbosity level for output.
        v (int): An alias for the verbosity level.
        chobolo (str | None): Optional path to explicitly override the Ch-obolo configuration file to use.
        secrets_context (SecretsContext | dict[str, Any]): The context containing secret file paths and provider configurations.
        global_config (dict[str, Any] | None): Internal state caching the global `~/.config/chaos/config.yml` data.
    """

    __slots__ = (
        "stack_name",
        "project_name",
        "pulumi_program",
        "stack",
        "secrets_used",
        "pelago",
        "secrets",
        "provided_secrets",
        "update_plugins",
        "i_know_what_im_doing",
        "dry",
        "verbose",
        "v",
        "chobolo",
        "secrets_context",
        "global_config",
        "needed_secrets",
    )

    def __init__(
        self,
        stack_name: str,
        project_name: str,
        pulumi_program: PulumiFn | Callable,
        stack: Stack | None = None,
        secrets_used: list[str] | None = None,
        pelago: list[dict[str, Any]] | None = None,
        secrets: bool = False,
        provided_secrets: dict[str, Any] | None = None,
        update_plugins: bool = False,
        i_know_what_im_doing: bool = False,
        dry: bool = False,
        verbose: int = 0,
        v: int = 0,
        chobolo: str | None = None,
        secrets_context: SecretsContext | dict[str, Any] | None = None,
        global_config: dict[str, Any] | None = None,
        needed_secrets: set[str] = set(),
    ):
        self.stack_name = stack_name
        self.project_name = project_name
        self.pulumi_program = pulumi_program
        self.stack = stack
        self.secrets_used = secrets_used or []
        self.pelago = pelago or []
        self.secrets = secrets
        self.provided_secrets = provided_secrets or {}
        self.update_plugins = update_plugins
        self.i_know_what_im_doing = i_know_what_im_doing
        self.dry = dry
        self.verbose = verbose
        self.v = v
        self.chobolo = chobolo
        self.secrets_context = (
            SecretsContext.from_dict_or_self(secrets_context)
            if secrets_context is not None
            else SecretsContext()
        )
        self.global_config = global_config or {}
        self.needed_secrets = needed_secrets or set()


class TeamPrunePayload(BasePayload):
    """
    Payload for pruning stale team configurations.

    Attributes:
        companies (list[str]): Optional list of specific company names to prune. If empty, all companies are checked.
        i_know_what_im_doing (bool): If True, bypasses interactive confirmation prompts.
        confirmed (bool): Internal state tracking whether the user has confirmed the pruning action.
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
    Payload for listing active team configurations.

    Attributes:
        company (str | None): Optional company name to filter the listed teams. If None, all teams from all companies are listed.
        no_pretty (bool): If True, disables rich CLI formatting for the output.
        json (bool): If True, forces the output to be in JSON format (usually combined with no_pretty).
    """

    __slots__ = ("company", "no_pretty", "json")

    def __init__(self, company: str | None, no_pretty: bool, json: bool):
        self.company = company
        self.no_pretty = no_pretty
        self.json = json


class TeamClonePayload(BasePayload):
    """
    Payload for cloning a team's Git repository.

    Attributes:
        target (str): The target repository URL or identifier to clone.
        path (str | None): Optional local path where the repository should be cloned. If None, clones to the current directory or default structure.
    """

    __slots__ = ("target", "path")

    def __init__(self, target: str, path: str | None):
        self.target = target
        self.path = path


class TeamInitPayload(BasePayload):
    """
    Payload for initializing a new team repository structure.

    Attributes:
        target (str): The target team identifier, usually in the format 'company.team.person'.
        path (str | None): Optional directory path where the team should be initialized.
        i_know_what_im_doing (bool): If True, bypasses interactive confirmation prompts.
        confirmed (bool): Internal state tracking whether the user confirmed the initialization.
        init_git (bool): Internal state tracking whether a new Git repository should be initialized.
        overwrite_sops (bool): Internal state tracking whether to overwrite an existing SOPS config.
        engine (str | None): The encryption engine to use (e.g., 'age', 'gpg', or 'both').
        use_vault (bool): Internal state tracking whether HashiCorp Vault integration should be configured.
        continue_no_vault (bool): Internal state tracking whether to continue if Vault is not present.
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
    Payload for activating a team configuration repository.

    Attributes:
        path (str | None): The path to the team repository that should be symlinked and activated.
    """

    __slots__ = ("path",)

    def __init__(self, path: str | None):
        self.path = path


class TeamDeactivatePayload(BasePayload):
    """
    Payload for deactivating active team configurations.

    Attributes:
        company (str): The company name under which the teams reside.
        teams (list[str]): The specific teams to deactivate. If empty, all teams for the company are deactivated.
        confirmed (bool): Internal state tracking whether the deactivation action was confirmed by the user.
    """

    __slots__ = ("company", "teams", "confirmed")

    def __init__(self, company: str, teams: list[str], confirmed: bool = False):
        self.company = company
        self.teams = teams
        self.confirmed = confirmed


class ExplainPayload(BasePayload):
    """
    Payload for retrieving explanatory documentation about Ch-aOS concepts and roles.

    Attributes:
        topics (list[str]): A list of topics or sub-topics to explain (e.g., 'apply', 'secrets.edit').
        no_pretty (bool): If True, disables rich CLI formatting for the output.
        json (bool): If True, formats the raw explanation output as JSON.
        details (str): The level of detail requested ('basic', 'intermediate', or 'advanced').
        complexity (str): The complexity level of the explanation.
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
    Payload for setting default paths in the global chaos configuration.

    Attributes:
        chobolo_file (str | None): Path to the default Ch-obolo file.
        sops_file (str | None): Path to the default .sops.yaml configuration file.
        secrets_file (str | None): Path to the default secrets file.
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
    Payload for checking and listing available Ch-aOS components.

    Attributes:
        checks (Literal): The specific type of component to check (e.g., 'roles', 'aliases', 'secrets').
        chobolo (str | None): Optional override for the Ch-obolo file path to read from.
        json (bool): If True, forces the output of the check to be in JSON format.
        team (str | None): Optional team context string to resolve paths when checking team-specific components.
        sops_file_override (str | None): Optional override for the .sops.yaml configuration file path.
        secrets_file_override (str | None): Optional override for the secrets file path.
        update_plugins (bool): If True, forces a refresh of the plugin cache before performing the check.
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
    Payload for interacting with the Styx plugin registry.

    Attributes:
        styx_commands (Literal): The Styx action to perform ('invoke' for install, 'list', or 'destroy' for uninstall).
        entries (list[str]): The names of the plugins to install, list, or uninstall.
        no_pretty (bool): If True, disables rich CLI formatting for the output.
        json (bool): If True, forces the output of the command to be in JSON format.
        force (bool): If True, forces the action without confirmation (applicable for 'invoke' command).
        registry_url (str | None): Optional custom URL for the Styx plugin registry, if not using the default registry.
    """

    __slots__ = (
        "styx_commands",
        "entries",
        "no_pretty",
        "json",
        "force",
        "registry_url",
    )

    def __init__(
        self,
        styx_commands: Literal["invoke", "list", "destroy"],
        entries: list[str],
        no_pretty: bool,
        json: bool,
        force: bool = False,
        registry_url: str | None = None,
    ):
        self.styx_commands = styx_commands
        self.entries = entries
        self.no_pretty = no_pretty
        self.json = json
        self.force = force
        self.registry_url = registry_url


class InitPayload(BasePayload):
    """
    Payload for generating boilerplate configuration files via the initialization wizard.

    Attributes:
        init_command (Literal): The type of initialization to perform ('chobolo' or 'secrets').
        update_plugins (bool): If True, forces a refresh of the plugin cache before initialization.
        targets (list[str]): Optional list of target plugins to base the chobolo template on.
        template (bool): If True, prints the generated template to stdout instead of saving it to a file.
        human (bool): If True, formats the output of a templated chobolo as human-readable YAML instead of raw Python dict.
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
    Payload containing configuration for secret providers, usually governing ephemeral decryption keys.

    Attributes:
        provider (str | None): The name of the provider backend mapped in the global config (e.g., 'bw.age').
        ephemeral_provider_args (dict[str, Any] | None): A dictionary mapping specific provider CLI flags to their arguments (e.g., {'from_bw': ('item_id', 'age')}).
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
    Payload representing the environment context when interacting with secrets.

    Attributes:
        team (str | None): The team string (e.g., 'company.team.person') used to resolve secrets and sops file paths.
        sops_file_override (str | None): Optional explicit path overriding the default .sops.yaml location.
        secrets_file_override (str | None): Optional explicit path overriding the default secrets.yml location.
        provider_config (ProviderConfigPayload | dict[str, Any] | None): The ephemeral secret provider configuration to use for operations.
        i_know_what_im_doing (bool): If True, suppresses interactive confirmation prompts.
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
    Base payload representing provider-specific export arguments.

    This class is intended to be subclassed by specific providers (e.g., Bitwarden, 1Password) to define their unique export options.
    """

    __slots__ = ()

    def __init__(self) -> None:
        pass


class ProviderImportArgs(BasePayload):
    """
    Base payload representing provider-specific import arguments.

    This class is intended to be subclassed by specific providers to define their unique import options.
    """

    __slots__ = ()

    def __init__(self) -> None:
        pass


class SecretsExportPayload(BasePayload):
    """
    Payload for exporting a master secret key (age, gpg, vault) to an external secret provider.

    Attributes:
        provider_name (str): The CLI name of the provider to use for the export (e.g., 'bw').
        key_type (Literal): The type of key being exported ('age', 'gpg', 'vault').
        no_import (bool): If True, adds a `# NO-IMPORT` flag to the secret to prevent it from being re-imported later.
        save_to_config (bool): If True, saves the resulting item ID/URL to the global chaos configuration.
        item_name (str | None): The name or title of the item to be created in the provider's vault.
        keys (str | None): The path to the local file containing the keys to export (e.g., age or vault key files).
        vault_addr (str | None): The address of the HashiCorp Vault server, if exporting a vault token.
        fingerprints (list[str] | None): A list of GPG fingerprints to export.
        provider_specific_args (ProviderExportArgs | None): A subclass of ProviderExportArgs containing provider-specific options.
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
            else ProviderExportArgs
        )


class SecretsImportPayload(BasePayload):
    """
    Payload for importing a master secret key (age, gpg, vault) from an external secret provider to the local machine.

    Attributes:
        provider_name (str): The CLI name of the provider to use for the import (e.g., 'bw').
        key_type (Literal): The type of key being imported ('age', 'gpg', 'vault').
        item_id (str | None): The provider's unique identifier or URL for the item containing the key.
        provider_specific_args (ProviderImportArgs | None): A subclass of ProviderImportArgs containing provider-specific options.
        confirmed (bool): Internal state tracking whether the user confirmed overriding an existing local key.
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
            else ProviderImportArgs
        )


class SecretsRotatePayload(BasePayload):
    """
    Payload for adding or removing an encryption key from a `.sops.yaml` configuration file.

    Attributes:
        type (Literal): The type of key being rotated ('age', 'pgp', 'vault').
        keys (list[str]): The list of keys (e.g., public age keys, GPG fingerprints, Vault URIs) to add or remove.
        context (SecretsContext | dict[str, Any]): The context resolving the target `.sops.yaml` file and team.
        index (int | None): The specific rule index in the `.sops.yaml` file to modify. If None, affects all applicable rules.
        pgp_server (str | None): Optional PGP keyserver to download missing public keys from.
        create (bool): If True, creates a new key group if it doesn't already exist.
        update_confirmed (bool): Internal state tracking whether the user confirmed applying `sops updatekeys` after the rotation.
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
    Payload for listing all active encryption keys of a specific type within a `.sops.yaml` configuration file.

    Attributes:
        type (Literal): The type of key to search for and list ('age', 'pgp', 'vault').
        context (SecretsContext | dict[str, Any]): The context resolving the target `.sops.yaml` file.
        no_pretty (bool): If True, disables rich CLI formatting for the output.
        json (bool): If True, formats the output as a JSON array.
        value (bool): If True, prints only the raw key values, one per line (useful for shell piping).
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
    Payload for securely editing a secrets file using `sops`.

    Attributes:
        context (SecretsContext | dict[str, Any]): The context containing the paths to the secrets file, SOPS config, and the provider used for decryption.
        edit_sops_file (bool): If True, opens the `.sops.yaml` configuration file for editing instead of the encrypted secrets file.
    """

    __slots__ = ("context", "edit_sops_file")

    def __init__(
        self, context: SecretsContext | dict[str, Any], edit_sops_file: bool = False
    ):
        self.edit_sops_file = edit_sops_file

        self.context = SecretsContext.from_dict_or_self(context)


class SecretsPrintPayload(BasePayload):
    """
    Payload for decrypting and printing an entire secrets file to standard output.

    Attributes:
        context (SecretsContext | dict[str, Any]): The context containing the file paths and provider for decryption.
        print_sops_file (bool): If True, prints the unencrypted `.sops.yaml` configuration file instead.
        as_json (bool): If True, parses the decrypted secrets and outputs them as a JSON string.
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
    Payload for decrypting a secrets file and querying specific keys from it.

    Attributes:
        keys (list[str]): A list of keys (using dot notation) to extract from the decrypted secrets file.
        context (SecretsContext | dict[str, Any]): The context containing the file paths and provider for decryption.
        cat_sops_file (bool): If True, queries the `.sops.yaml` configuration file instead.
        as_json (bool): If True, formats the queried output as JSON.
        value_only (bool): If True, prints only the raw value of the keys without keys names or formatting (useful for piping).
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
    Payload for configuring Shamir's Secret Sharing threshold for a specific rule in a `.sops.yaml` configuration file.

    Attributes:
        index (int): The index of the creation rule to modify in the `.sops.yaml` file.
        share (int): The required number of key shares (threshold) to decrypt the secret. Setting this to 0 removes the threshold.
        context (SecretsContext | dict[str, Any]): The context resolving the target `.sops.yaml` file.
        confirmed (bool): Internal state tracking whether the user confirmed the removal of a threshold.
        update_confirmed (bool): Internal state tracking whether the user confirmed updating existing secrets to apply the new threshold.
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
    Payload for creating a new encrypted or unencrypted ramble (journal note).

    Attributes:
        target (str): The target journal and page name in dot notation (e.g., 'journal.page').
        context (SecretsContext | dict[str, Any]): The context resolving the team directory and potential `.sops.yaml` configuration.
        encrypt (bool): If True, encrypts the ramble immediately after creation using SOPS.
        keys (list[str] | None): Optional list of specific YAML keys within the ramble to encrypt (instead of encrypting all values).
        confirmed (bool): Internal state tracking whether the user confirmed overwriting or editing an existing ramble.
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
    Payload for editing an existing ramble file.

    Attributes:
        target (str): The target journal and page name in dot notation (e.g., 'journal.page').
        context (SecretsContext | dict[str, Any]): The context resolving the team directory and `.sops.yaml` location.
        edit_sops_file (bool): If True, opens the `.sops.yaml` configuration file for the ramble namespace instead of the ramble itself.
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
    Payload for encrypting an existing, unencrypted ramble file.

    Attributes:
        target (str): The target journal and page name to encrypt.
        context (SecretsContext | dict[str, Any]): The context resolving the `.sops.yaml` configuration.
        keys (list[str] | None): Optional list of specific YAML keys within the ramble to encrypt. If None, encrypts all values except base metadata.
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
    Payload for reading and displaying the content of one or more ramble files.

    Attributes:
        targets (list[str]): A list of target rambles to read (e.g., 'journal.page' or 'journal.list').
        context (SecretsContext | dict[str, Any]): The context containing decryption provider configurations if the rambles are encrypted.
        no_pretty (bool): If True, disables rich CLI rendering for the output.
        json (bool): If True, formats the raw read output as JSON.
        values (list[str] | None): Optional list of specific YAML keys to extract and print from the read ramble (useful for piping).
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
    Payload for searching through all ramble files for specific terms or tags.

    Attributes:
        context (SecretsContext | dict[str, Any]): The context containing decryption configurations for searching encrypted rambles.
        find_term (str | None): The keyword or phrase to search for within the ramble content.
        tag (str | None): Optional tag to filter the search results.
        no_pretty (bool): If True, disables rich CLI formatting for the search results list.
        json (bool): If True, formats the search results list as JSON.
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
    Payload for renaming or moving a ramble journal or page.

    Attributes:
        old (str): The current target path of the journal or page.
        new (str): The new target path for the journal or page.
        context (SecretsContext | dict[str, Any]): The context used to resolve the team directories.
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
    Payload for deleting a ramble journal or page.

    Attributes:
        ramble (str): The target journal or page to delete.
        context (SecretsContext | dict[str, Any]): The context used to resolve the team directories.
        confirmed (bool): Internal state tracking whether the user confirmed the deletion.
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
    Payload for triggering a re-encryption (`sops updatekeys`) on all encrypted ramble files.

    Attributes:
        context (SecretsContext | dict[str, Any]): The context containing the paths to the `.sops.yaml` configuration and the decryption providers.
    """

    __slots__ = ("context",)

    # ye, only context
    def __init__(self, context: SecretsContext | dict[str, Any]):
        self.context = SecretsContext.from_dict_or_self(context)


class ApplyPayload(BasePayload):
    """
    Payload for orchestrating the `apply` lifecycle of Ch-aOS.

    This represents the core orchestration data structure required to resolve roles, configurations, secrets, and execute them on hosts.

    Attributes:
        update_plugins (bool): If True, forces a refresh of the plugin cache before starting orchestration.
        i_know_what_im_doing (bool): If True, bypasses all interactive confirmation prompts before execution.
        dry (bool): If True, runs pyinfra in dry-run mode, calculating but not executing operations.
        verbose (int): The verbosity level for Pyinfra output (1=Warning, 2=Info, 3=Debug).
        v (int): An alias for the verbosity level.
        tags (list[str]): The list of role tags or aliases to apply to the target hosts.
        chobolo (str | None): Optional path to explicitly override the Ch-obolo configuration file to use.
        limani (str | None): Optional Limani plugin name to use for the Logbook database.
        logbook (bool): If True, enables telemetry and execution recording into the Logbook.
        fleet (bool): If True, parses the fleet configuration and orchestrates changes across all remote hosts defined.
        sudo_password_file (str | None): Optional path to a file containing the sudo password.
        password (str | None): Optional string containing the sudo password.
        secrets (bool): If True, signals that the operations require secrets and that they must be decrypted.
        serial (bool): If True, executes pyinfra operations serially across the fleet instead of in parallel.
        no_wait (bool): If True, executes pyinfra operations concurrently without waiting for slow hosts.
        export_logs (bool): If True, exports the telemetry logbook to a JSON file after the run finishes.
        secrets_context (SecretsContext | dict[str, Any]): The context containing secret file paths and provider configurations.
        confirmed_password (str): Internal state holding the verified sudo password if gathered interactively.
        pyinfra_state (State | None): Internal state storing the initialized pyinfra State object after setup.
        target_hosts (list | None): Internal state containing the parsed list of hosts to apply the roles to.
        is_fleet_active (bool): Internal state tracking whether a remote fleet is actively being targeted.
        parallelism (int): Internal state tracking the maximum number of concurrent hosts to apply changes to.
        fallback_to_local (bool): Internal state tracking if fleet failed to resolve and fallback to local was permitted.
        decrypted_secrets (dict[str, Any] | None): Internal state caching the decrypted YAML/JSON secrets dictionary for role consumption.
        global_config (dict[str, Any] | None): Internal state caching the global `~/.config/chaos/config.yml` data.
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
