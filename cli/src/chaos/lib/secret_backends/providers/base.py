"""Abstract base class for external secret provider integrations (e.g., password managers)."""

from __future__ import annotations

import argparse
import os
import shlex
import subprocess
from abc import ABC, abstractmethod
from collections.abc import Iterator
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any

from chaos.lib.args.dataclasses import (
    ProviderExportArgs,
    ProviderImportArgs,
    ResultPayload,
    SecretsContext,
    SecretsExportPayload,
    SecretsImportPayload,
)

from ..key_backends.factory import get_key_backend

if TYPE_CHECKING:
    from typing import TypedDict

    class EphemeralEnvReturn(TypedDict):
        env: dict[str, str]
        prefix: str
        pass_fds: list[int]


class Provider(ABC):
    """Abstract base class for secret backends.

    Notes:
        Base operations for managing secrets.
    """

    def __init__(
        self,
        payload: SecretsContext | SecretsExportPayload | SecretsImportPayload,
        global_config: dict[str, Any],
    ):
        """Initializes the Provider class.

        Args:
            payload (SecretsContext | SecretsExportPayload | SecretsImportPayload): The contextual data governing operation constraints.
            global_config (dict): Global environment configurations.
        """
        self.payload = payload  # pyright: ignore[reportUnannotatedClassAttribute]
        self.config = global_config  # pyright: ignore[reportUnannotatedClassAttribute]

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
    @abstractmethod
    def get_export_arg_names() -> list[str]:
        """Gets the list of provider-specific export argument names.

        Returns:
            List[str]: String array mappings pointing toward target command options.
        """
        return []

    @staticmethod
    @abstractmethod
    def get_import_arg_names() -> list[str]:
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
    @abstractmethod
    def get_cli_name() -> tuple[str, str]:
        """Returns the name of the attribute in the args object that corresponds
        to this provider's ephemeral key flag and name for config.

        Returns:
            Tuple[str, str]: The flag prefix alongside the configuration dictionary mapping.

        Notes:
            Returns None if the provider doesn't have a direct flag.
            e.g., ('from_bw', 'bw')
        """
        raise NotImplementedError

    @abstractmethod
    def get_ephemeral_key_args(self) -> tuple[str, str] | None:
        """Gets the provider-specific arguments for creating an ephemeral environment.

        Returns:
            tuple[str, str] | None: Yields the internal key references mapping to specific operations, or None.
        """
        raise NotImplementedError

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
    def check_status(self) -> None | tuple[bool, str]:
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

    def __init_subclass__(cls, **kwargs):
        """Ensures that all subclasses implement required abstract methods."""
        super().__init_subclass__(**kwargs)
        protected_methods = [
            "edit",
            "setupEphemeralEnv",
            "import_secrets",
            "decrypt",
            "updatekeys",
            "_run_sops_command",
            "name",
        ]

        for method in protected_methods:
            if method in cls.__dict__:
                raise TypeError(
                    f"{method} is a protected method and cannot be overridden in {cls.__name__}."
                )

    @contextmanager
    def edit(
        self, secrets_file: str, sops_file: str
    ) -> Iterator[tuple[str, dict, list[int]]]:
        """Context manager to prepare the SOPS edit command and its environment.

        Args:
            secrets_file (str): Defined context point locating editable YAML sets.
            sops_file (str): The configuration constraint establishing encryptions metrics.

        Yields:
            tuple[str, dict, List[int]]: (command_string, environment_dict, pass_fds_list)
        """
        sops_command = ["sops", "--config", sops_file, secrets_file]
        try:
            with self.setupEphemeralEnv() as ctx:
                prefix = ctx.get("prefix", "")
                pass_fds = ctx.get("pass_fds", [])
                env = ctx.get("env", os.environ.copy())
                cmd = shlex.join(sops_command)

                if prefix:
                    cmd = f"{prefix} {cmd}"

                yield cmd, env, pass_fds
        except Exception as e:
            raise RuntimeError(f"Error setting up SOPS edit environment: {e}") from e

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

        try:
            backend = get_key_backend(key_type)
        except ValueError as e:
            raise ValueError(
                f"Error initializing key backend for ephemeral environment: {e}"
            )
        except ImportError as e:
            raise ImportError(
                f"Error importing key backend for ephemeral environment: {e}"
            )
        except Exception as e:
            raise RuntimeError(
                f"Unexpected error initializing key backend for ephemeral environment: {e}"
            )

        key_content = self.readKeys(item_id)

        try:
            pub_key, sec_key, parsed_key_content = backend.parse_key_content(
                key_content, self.name
            )
        except ValueError as e:
            raise ValueError(
                f"Error parsing key content for ephemeral environment: {e}"
            )

        context: EphemeralEnvReturn = {
            "env": os.environ.copy(),
            "prefix": "",
            "pass_fds": [],
        }

        with backend.ephemeral_key_context(
            pub_key, sec_key, parsed_key_content
        ) as env_ctx:
            context["env"].update(env_ctx.get("env", {}))
            context["prefix"] = env_ctx.get("prefix", "")
            context["pass_fds"] = env_ctx.get("pass_fds", [])

            yield context

    def import_secrets(self, payload: SecretsImportPayload) -> ResultPayload[None]:
        """Imports remote keys from the provider to local.

        Args:
            payload (SecretsImportPayload): Identifies targets alongside their key schemas (gpg, age, vault).

        Returns:
            ResultPayload: Successful imports logging details and public metadata elements on successful pass constraints.
        """
        messages = []
        errors = []

        try:
            backend = get_key_backend(payload.key_type)
        except ValueError as e:
            errors.append(str(e))
            return ResultPayload(success=False, error=errors, message=messages)

        except ImportError as e:
            errors.append(f"Error importing key backend for {payload.key_type}: {e}")
            return ResultPayload(success=False, error=errors, message=messages)

        except Exception as e:
            errors.append(f"Unexpected error initializing key backend: {e}")
            return ResultPayload(success=False, error=errors, message=messages)

        try:
            self.check_status()

            keyType = payload.key_type
            item_id = payload.item_id
            if not keyType:
                raise ValueError("Key type must be specified for import.")
            if not item_id:
                raise ValueError("Item ID must be specified for import.")

            key_content = self.readKeys(item_id)
            try:
                pubKey, secKey, parsed_key_content = backend.parse_key_content(
                    key_content, self.name
                )
            except ValueError as e:
                raise ValueError(f"Error parsing key content: {e}") from e

            if "# NO-IMPORT" in parsed_key_content:
                raise ValueError(
                    f"The {keyType} key from {self.name} contains a NO-IMPORT marker and will not be imported."
                )

            import_errors, import_messages = backend.import_key(
                parsed_key_content, confirmed=payload.confirmed
            )

            if import_errors:
                errors.extend(import_errors)
                messages.extend(import_messages)
                return ResultPayload(success=False, error=errors, message=messages)

            messages.append(f"Successfully imported {keyType} key from {self.name}.")

            if pubKey:
                messages.append(f"Public Key(s): {pubKey}")

            if secKey:
                messages.append(f"Secret Key: {secKey[0:3]}... (hidden for security)")

        except Exception as e:
            errors.append(str(e))
            return ResultPayload(success=False, error=errors, message=messages)

        return ResultPayload(success=True, message=messages)

    def decrypt(self, secrets_file: str, sops_file: str) -> str:
        """Decrypt secrets using SOPS.

        Args:
            secrets_file (str): Path to the secrets file.
            sops_file (str): Path to the SOPS file.

        Returns:
            str: Decrypted secrets content.
        """
        sops_command = ["sops", "--config", sops_file, "decrypt", secrets_file]
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
        except Exception as e:
            raise RuntimeError(f"Unexpected error running SOPS command: {e}") from e
