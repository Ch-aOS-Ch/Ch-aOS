"""Abstract base class for external secret provider integrations (e.g., password managers)."""

import argparse
import os
import shlex
import subprocess
from abc import ABC, abstractmethod
from collections.abc import Iterator
from contextlib import contextmanager
from typing import TYPE_CHECKING, List, Tuple, Union

from chaos.lib.args.dataclasses import (
    ProviderExportArgs,
    ProviderImportArgs,
    ResultPayload,
    SecretsContext,
    SecretsExportPayload,
    SecretsImportPayload,
)

from ..crypto import (
    _import_age_keys,
    _import_gpg_keys,
    _import_vault_keys,
    decompress,
    extract_age_keys,
)
from .ephemeral import ephemeralAgeKey, ephemeralGpgKey, ephemeralVaultKeys

if TYPE_CHECKING:
    from typing import TypedDict

    class EphemeralEnvReturn(TypedDict):
        env: dict[str, str]
        prefix: str
        pass_fds: List[int]


class Provider(ABC):
    """Abstract base class for secret backends.

    Notes:
        Base operations for managing secrets.
    """

    def __init__(
        self,
        payload: Union[SecretsContext, SecretsExportPayload, SecretsImportPayload],
        global_config: dict,
    ):
        """Initializes the Provider class.

        Args:
            payload (Union[SecretsContext, SecretsExportPayload, SecretsImportPayload]): The contextual data governing operation constraints.
            global_config (dict): Global environment configurations.
        """
        self.payload = payload
        self.config = global_config

    @classmethod
    @abstractmethod
    def build_export_args(cls, **kwargs) -> "ProviderExportArgs":
        """Builds the provider-specific export arguments dataclass from a dictionary.

        Returns:
            ProviderExportArgs: An instance representing explicit export targets mapped from kwargs.
        """
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def build_import_args(cls, **kwargs) -> "ProviderImportArgs":
        """Builds the provider-specific import arguments dataclass from a dictionary.

        Returns:
            ProviderImportArgs: An instance representing explicit import configurations derived from kwargs.
        """
        raise NotImplementedError

    @staticmethod
    def get_export_arg_names() -> List[str]:
        """Gets the list of provider-specific export argument names.

        Returns:
            List[str]: String array mappings pointing toward target command options.
        """
        return []

    @staticmethod
    def get_import_arg_names() -> List[str]:
        """Gets the list of provider-specific import argument names.

        Returns:
            List[str]: String mapped definition flags identifying expected argument inputs.
        """
        return []

    @staticmethod
    @abstractmethod
    def register_flags(parser: argparse.ArgumentParser) -> None:
        """Register provider-specific command-line arguments.

        Args:
            parser (argparse.ArgumentParser): Parsed parent hierarchy requiring parameter expansions.
        """
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def register_export_subcommands(
        subparser: argparse._SubParsersAction,
    ) -> argparse.ArgumentParser:
        """Register provider-specific subcommands for export.

        Args:
            subparser (argparse._SubParsersAction): A subparser generator to initialize target nested commands.

        Returns:
            argparse.ArgumentParser: The built parser containing all specified hooks.
        """
        pass

    @staticmethod
    @abstractmethod
    def register_import_subcommands(
        subparser: argparse._SubParsersAction,
    ) -> argparse.ArgumentParser:
        """Register provider-specific subcommands for import.

        Args:
            subparser (argparse._SubParsersAction): A subparser object responsible for branching tree creation.

        Returns:
            argparse.ArgumentParser: The populated parser component logic branch.
        """
        raise NotImplementedError

    @staticmethod
    def get_cli_name() -> Tuple[str, str]:
        """Returns the name of the attribute in the args object that corresponds
        to this provider's ephemeral key flag and name for config.

        Returns:
            Tuple[str, str]: The flag prefix alongside the configuration dictionary mapping.

        Notes:
            Returns None if the provider doesn't have a direct flag.
            e.g., ('from_bw', 'bw')
        """
        raise NotImplementedError

    @property
    def name(self) -> str:
        """Returns a clean name for the provider.

        Returns:
            str: Identifier string denoting class function.

        Notes:
            e.g. BitwardenPasswordProvider -> Bitwarden
        """
        return self.__class__.__name__.replace("PasswordProvider", "").replace(
            "SecretProvider", ""
        )

    @abstractmethod
    def get_ephemeral_key_args(self) -> tuple[str, str] | None:
        """Gets the provider-specific arguments for creating an ephemeral environment.

        Returns:
            tuple[str, str] | None: Yields the internal key references mapping to specific operations, or None.
        """
        raise NotImplementedError

    @contextmanager
    def setupEphemeralEnv(self) -> Iterator[EphemeralEnvReturn]:
        """Context manager to set up an ephemeral environment for SOPS.

        Yields:
            dict: Ephemeral OS mapping structure overriding default parameters with explicit execution mappings.
        """
        key_args = self.get_ephemeral_key_args()
        if not key_args:
            yield {"env": os.environ.copy(), "prefix": "", "pass_fds": []}
            return

        item_id, key_type = key_args

        context = {"env": os.environ.copy(), "prefix": "", "pass_fds": []}

        match key_type:
            case "age":
                _, _, key_content = self.getAgeKeys(item_id)
                with ephemeralAgeKey(key_content) as (prefix, fds):
                    context["prefix"] = prefix
                    context["pass_fds"] = fds
                    yield {"env": context["env"], "prefix": prefix, "pass_fds": fds}

            case "gpg":
                _, secKey, _ = self.getGpgKeys(item_id)
                actualKey = decompress(secKey)
                with ephemeralGpgKey(actualKey) as gpg_env:
                    context["env"].update(gpg_env)
                    yield {"env": context["env"], "prefix": "", "pass_fds": []}

            case "vault":
                vault_addr, vault_token, _ = self.getVaultKeys(item_id)
                with ephemeralVaultKeys(vault_token, vault_addr) as (prefix, fds):
                    context["prefix"] = prefix
                    context["pass_fds"] = fds
                    yield {"env": context["env"], "prefix": prefix, "pass_fds": fds}
            case _:
                raise ValueError(f"Unsupported key type '{key_type}'.")

    @abstractmethod
    def readKeys(self, item_id: str) -> str:
        """Reads keys from the provider.

        Args:
            item_id (str): Reference ID identifying the external vault entry.

        Returns:
            str: Acquired unencrypted raw value representing the query string.
        """
        raise NotImplementedError

    @abstractmethod
    def check_status(self) -> None | Tuple[bool, str]:
        """Checks the status of the provider.

        Returns:
            None | Tuple[bool, str]: None, or a boolean status indicator alongside error strings defining backend failure cases.
        """
        raise NotImplementedError

    @abstractmethod
    def export_secrets(self, payload: SecretsExportPayload) -> ResultPayload:
        """Exports local keys to the provider.

        Args:
            payload (SecretsExportPayload): Export payload structure.

        Returns:
            ResultPayload: Export execution final state.
        """
        return ResultPayload(
            success=False,
            message=["Export not implemented for this provider."],
        )

    def getAgeKeys(self, item_id: str) -> tuple[str, str, str]:
        """Retrieves Age keys from the provider.

        Args:
            item_id (str): The ID of the item to retrieve.

        Returns:
            tuple[str, str, str]: Public key, Secret key, Key content.

        Raises:
            ValueError: If the key format is incompatible or no public/private pairs are discovered within payload bounds.
        """
        key_content = self.readKeys(item_id)
        if not key_content:
            raise ValueError(f"Retrieved key from {self.name} is empty.")

        sanitized_key_content = ""
        for line in key_content.splitlines():
            if line.startswith(" ") or line.startswith("\t"):
                line = line.lstrip()
            sanitized_key_content += line + "\n"

        pubKey, secKey = extract_age_keys(key_content)

        if not pubKey:
            raise ValueError(
                f"Could not find a public key in the secret from {self.name}. Expected a line starting with '# public key:'."
            )
        if not secKey:
            raise ValueError(
                f"Could not find a secret key in the secret from {self.name}. Expected a line starting with 'AGE-SECRET-KEY-'."
            )

        return pubKey, secKey, sanitized_key_content

    def getGpgKeys(self, item_id: str) -> tuple[str, str, str]:
        """Retrieves GPG keys from the provider.

        Args:
            item_id (str): The ID of the item to retrieve.

        Returns:
            tuple[str, str, str]: Fingerprints, Secret key, Raw key Content.

        Raises:
            ValueError: On content empty evaluation or if the returned text doesn't evaluate as PGP syntax structures.
        """
        key_content = self.readKeys(item_id)
        if not key_content:
            raise ValueError(f"Retrieved GPG key from {self.name} is empty.")

        fingerprints = ""
        for line in key_content.splitlines():
            if line.strip().startswith("# fingerprints:"):
                fingerprints = line.split(":", 1)[1].strip()
                break

        if "-----BEGIN PGP PRIVATE KEY BLOCK-----" not in key_content:
            raise ValueError(
                f"The secret read from {self.name} does not appear to be a GPG private key block."
            )

        noHeadersSecKey = key_content.split("-----BEGIN PGP PRIVATE KEY BLOCK-----", 1)[
            1
        ].rsplit("-----END PGP PRIVATE KEY BLOCK-----", 1)[0]
        secKey = noHeadersSecKey.strip()

        return fingerprints, secKey, key_content

    def getVaultKeys(self, item_id: str) -> tuple[str, str, str]:
        """Retrieves Vault keys from the provider.

        Args:
            item_id (str): The ID of the item to retrieve.

        Returns:
            tuple[str, str, str]: Vault address, Vault token, Raw key Content.

        Raises:
            ValueError: When extracted content defaults out as null sets missing essential variables.
        """
        key_content = self.readKeys(item_id)
        if not key_content:
            raise ValueError(f"Retrieved key from {self.name} is empty.")

        vault_addr, vault_token = None, None
        for line in key_content.splitlines():
            if line.strip().startswith("# Vault Address:"):
                vault_addr = line.split("::", 1)[1].strip()
            if line.strip().startswith("Vault Key:"):
                vault_token = line.split(":", 1)[1].strip()

        if not vault_addr or not vault_token:
            raise ValueError(
                f"Could not extract both Vault address and token from {self.name} item."
            )

        return vault_addr, vault_token, key_content

    def import_secrets(self, payload: SecretsImportPayload) -> ResultPayload:
        """Imports remote keys from the provider to local.

        Args:
            payload (SecretsImportPayload): Identifies targets alongside their key schemas (gpg, age, vault).

        Returns:
            ResultPayload: Successful imports logging details and public metadata elements on successful pass constraints.
        """
        messages = []
        errors = []

        try:
            self.check_status()

            keyType = payload.key_type
            item_id = payload.item_id
            if not keyType:
                raise ValueError("Key type must be specified for import.")
            if not item_id:
                raise ValueError("Item ID must be specified for import.")

            match keyType:
                case "age":
                    pubKey, secKey, key_content = self.getAgeKeys(item_id)
                    if "# NO-IMPORT" in key_content:
                        raise ValueError(
                            f"The age key from {self.name} contains a NO-IMPORT marker and will not be imported."
                        )

                    import_result = _import_age_keys(
                        key_content, confirmed=payload.confirmed
                    )
                    if not import_result.success:
                        return import_result

                    messages.append(f"Successfully imported age key from {self.name}.")
                    messages.append(f"Public Key: {pubKey}")
                    messages.append(f"Secret Key: {secKey}")
                    messages.extend(import_result.message)

                case "gpg":
                    fingerprints, secKey, key_content = self.getGpgKeys(item_id)
                    if "# NO-IMPORT" in key_content:
                        raise ValueError(
                            f"The GPG key from {self.name} contains a NO-IMPORT marker and will not be imported."
                        )

                    import_result = _import_gpg_keys(secKey)
                    if not import_result.success:
                        return import_result

                    messages.append(f"Successfully imported GPG key from {self.name}.")
                    if fingerprints:
                        messages.append(f"Fingerprints: {fingerprints}")
                    messages.extend(import_result.message)

                case "vault":
                    vault_addr, vault_token, key_content = self.getVaultKeys(item_id)
                    if "# NO-IMPORT" in key_content:
                        raise ValueError(
                            f"The Vault key from {self.name} contains a NO-IMPORT marker and will not be imported."
                        )

                    import_result = _import_vault_keys(key_content)
                    if not import_result.success:
                        return import_result

                    messages.append(
                        f"Successfully imported Vault key from {self.name}."
                    )
                    messages.append(f"Vault Address: {vault_addr}")
                    messages.append(f"Vault Token: {vault_token}")
                    messages.extend(import_result.message)

                case _:
                    raise ValueError(f"Unsupported key type '{keyType}'.")

        except Exception as e:
            errors.append(str(e))
            return ResultPayload(success=False, error=errors, message=messages)

        return ResultPayload(success=True, message=messages)

    @contextmanager
    def edit(
        self, secrets_file: str, sops_file: str
    ) -> Iterator[Tuple[str, dict, List[int]]]:
        """Context manager to prepare the SOPS edit command and its environment.

        Args:
            secrets_file (str): Defined context point locating editable YAML sets.
            sops_file (str): The configuration constraint establishing encryptions metrics.

        Yields:
            tuple[str, dict, List[int]]: (command_string, environment_dict, pass_fds_list)
        """
        sops_command = ["sops", "--config", sops_file, secrets_file]
        with self.setupEphemeralEnv() as ctx:
            prefix = ctx.get("prefix", "")
            pass_fds = ctx.get("pass_fds", [])
            env = ctx.get("env", os.environ.copy())
            cmd = shlex.join(sops_command)

            if prefix:
                cmd = f"{prefix} {cmd}"

            yield cmd, env, pass_fds

    def decrypt(self, secrets_file: str, sops_file: str) -> str:
        """Decrypt secrets using SOPS.

        Args:
            secrets_file (str): Path to the secrets file.
            sops_file (str): Path to the SOPS file.

        Returns:
            str: Decrypted secrets content.
        """
        sops_command = ["sops", "--config", sops_file, "-d", secrets_file]
        result = self._run_sops_command(sops_command).stdout
        return result

    def updatekeys(self, secrets_file: str, sops_file: str) -> None:
        """Update keys on a SOPS encrypted file.

        Args:
            secrets_file (str): Path to the secrets file.
            sops_file (str): Path to the SOPS file.
        """
        sops_command = ["sops", "--config", sops_file, "updatekeys", "-y", secrets_file]
        self._run_sops_command(sops_command)

    def _run_sops_command(self, command: list[str]) -> subprocess.CompletedProcess:
        """Run a SOPS command in a subprocess.

        Args:
            command (list[str]): List of command arguments to run.

        Returns:
            subprocess.CompletedProcess: The result of the subprocess execution.

        Raises:
            RuntimeError: Exception thrown conveying underlying CLI interaction failures with sops execution metrics.
        """
        try:
            with self.setupEphemeralEnv() as ctx:
                prefix = ctx.get("prefix", "")
                pass_fds = ctx.get("pass_fds", [])
                env = ctx.get("env", os.environ.copy())

                cmd = shlex.join(command)
                if prefix:
                    cmd = f"{prefix} {cmd}"

                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=True,
                    env=env,
                    pass_fds=pass_fds,
                    shell=True,
                )
                return result
        except subprocess.CalledProcessError as e:
            err = e.stderr.strip() if e.stderr else "No additional error information."
            raise RuntimeError(f"Error running SOPS command: {err}") from e
