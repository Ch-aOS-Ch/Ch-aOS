from abc import ABC, abstractmethod
import argparse
from collections.abc import Iterator
from contextlib import contextmanager
import os
import shlex
import subprocess
from rich.console import Console
from .ephemeral import ephemeralAgeKey, ephemeralGpgKey, ephemeralVaultKeys
from .utils import (
    _import_age_keys,
    _import_gpg_keys,
    _import_vault_keys,
    extract_age_keys,
    decompress,
)
from typing import Tuple

console = Console()

class Provider(ABC):
    """
    Abstract base class for secret backends.

    Base operations for managing secrets.
    """

    def __init__(self, args, global_config: dict):
        self.args = args
        self.config = global_config

    @staticmethod
    @abstractmethod
    def register_flags(parser: argparse.ArgumentParser) -> None:
        """
        Register provider-specific command-line arguments.
        """
        raise NotImplementedError

    @abstractmethod
    @staticmethod
    def register_export_subcommands(subparser: argparse._SubParsersAction) -> None:
        """
        Register provider-specific subcommands.
        """
        pass

    @abstractmethod
    @staticmethod
    def register_import_subcommands(subparser: argparse._SubParsersAction) -> None:
        """
        Register provider-specific subcommands.
        """
        raise NotImplementedError

    @staticmethod
    def get_cli_flag_name() -> str | None:
        """
        Returns the name of the attribute in the args object that corresponds
        to this provider's ephemeral key flag (e.g., 'from_bw').
        Returns None if the provider doesn't have a direct flag.
        """
        return None

    @property
    def name(self) -> str:
        """
        Returns a clean name for the provider.
        e.g. BitwardenPasswordProvider -> BitwardenPassword
        """
        return self.__class__.__name__.replace("PasswordProvider", "").replace("SecretProvider", "")

    @abstractmethod
    def get_ephemeral_key_args(self) -> tuple[str, str] | None:
        """Gets the provider-specific arguments for creating an ephemeral environment."""
        raise NotImplementedError

    @contextmanager
    def setupEphemeralEnv(self) -> Iterator[dict]:
        """
        Context manager to set up an ephemeral environment for SOPS.
        """
        key_args = self.get_ephemeral_key_args()
        if not key_args:
            yield {"env": os.environ.copy(), "prefix": "", "pass_fds": []}
            return

        item_id, key_type = key_args

        context = {
            "env": os.environ.copy(),
            "prefix": "",
            "pass_fds": []
        }

        match key_type:
            case 'age':
                _, _, key_content = self.getAgeKeys(item_id)
                with ephemeralAgeKey(key_content) as age_env:
                    context["env"].update(age_env)
                    yield context
            case 'gpg':
                _, secKey = self.getGpgKeys(item_id)
                actualKey = decompress(secKey)
                with ephemeralGpgKey(actualKey) as gpg_env:
                    context["env"].update(gpg_env)
                    yield context
            case 'vault':
                vault_addr, vault_token = self.getVaultKeys(item_id)
                with ephemeralVaultKeys(vault_token, vault_addr) as (prefix, fds):
                    context["prefix"] = prefix
                    context["pass_fds"] = fds
                    yield context
            case _:
                raise ValueError(f"Unsupported key type '{key_type}'.")

    @abstractmethod
    def readKeys(self, item_id: str) -> str:
        """
        Reads keys from the provider.
        """
        raise NotImplementedError

    @abstractmethod
    def check_status(self) -> None | Tuple[bool, str]:
        """
        Checks the status of the provider.
        """
        raise NotImplementedError

    @abstractmethod
    def export_secrets(self) -> None:
        """
        Exports local keys to the provider.
        """
        raise NotImplementedError

    def getAgeKeys(self, item_id: str) -> tuple[str, str, str]:
        """
        Retrieves Age keys from the provider.
        Args:
            item_id (str): The ID of the item to retrieve.
        Returns:
            tuple[str, str, str]: Public key, Secret key, Key content.
        """
        key_content = self.readKeys(item_id)
        if not key_content: raise ValueError(f"Retrieved key from {self.name} is empty.")

        pubKey, secKey = extract_age_keys(key_content)

        if not pubKey:
            raise ValueError(f"Could not find a public key in the secret from {self.name}. Expected a line starting with '# public key:'.")
        if not secKey:
            raise ValueError(f"Could not find a secret key in the secret from {self.name}. Expected a line starting with 'AGE-SECRET-KEY-'.")

        return pubKey, secKey, key_content

    def getGpgKeys(self, item_id: str) -> tuple[str, str]:
        """
        Retrieves GPG keys from the provider.
        Args:
            item_id (str): The ID of the item to retrieve.
        Returns:
            tuple[str, str]: Fingerprints, Secret key.
        """
        key_content = self.readKeys(item_id)
        if not key_content:
            raise ValueError(f"Retrieved GPG key from {self.name} is empty.")

        fingerprints = ""
        for line in key_content.splitlines():
            if line.startswith("# fingerprints:"):
                fingerprints = line.split(":", 1)[1].strip()
                break

        if "-----BEGIN PGP PRIVATE KEY BLOCK-----" not in key_content:
            raise ValueError(f"The secret read from {self.name} does not appear to be a GPG private key block.")

        noHeadersSecKey = key_content.split('-----BEGIN PGP PRIVATE KEY BLOCK-----', 1)[1].rsplit('-----END PGP PRIVATE KEY BLOCK-----', 1)[0]
        secKey = noHeadersSecKey.strip()

        return fingerprints, secKey

    def getVaultKeys(self, item_id: str) -> tuple[str, str]:
        """
        Retrieves Vault keys from the provider.
        Args:
            item_id (str): The ID of the item to retrieve.
        Returns:
            tuple[str, str]: Vault address, Vault token.
        """
        key_content = self.readKeys(item_id)
        if not key_content: raise ValueError(f"Retrieved key from {self.name} is empty.")

        vault_addr, vault_token = None, None
        for line in key_content.splitlines():
            if line.startswith("# Vault Address:"):
                vault_addr = line.split("::", 1)[1].strip()
            if line.startswith("Vault Key:"):
                vault_token = line.split(":", 1)[1].strip()

        if not vault_addr or not vault_token:
            raise ValueError(f"Could not extract both Vault address and token from {self.name} item.")

        return vault_addr, vault_token

    def import_secrets(self) -> None:
        """
        Imports remote keys from the provider to local.
        """
        self.check_status()

        args = self.args

        keyType = args.key_type
        item_id = args.item_id
        if not keyType:
            raise ValueError("Key type must be specified for import.")
        if not item_id:
            raise ValueError("Item ID must be specified for import.")
        match keyType:
            case 'age':
                pubKey, secKey, key_content = self.getAgeKeys(item_id)
                console.print(f"[green]Successfully imported age key from {self.name}.[/green]")
                console.print(f"Public Key: [bold]{pubKey}[/bold]")
                console.print(f"Secret Key: [bold]{secKey}[/bold]")

                _import_age_keys(key_content)

            case 'gpg':
                fingerprints, secKey = self.getGpgKeys(item_id)
                console.print(f"[green]Successfully imported GPG key from {self.name}.[/green]")
                if fingerprints:
                    console.print(f"Fingerprints: [bold]{fingerprints}[/bold]")

                _import_gpg_keys(secKey)

            case 'vault':
                vault_addr, vault_token = self.getVaultKeys(item_id)
                console.print(f"[green]Successfully imported Vault key from {self.name}.[/green]")
                console.print(f"Vault Address: [bold]{vault_addr}[/bold]")
                console.print(f"Vault Token: [bold]{vault_token}[/bold]")

                key_content = f"# Vault Address:: {vault_addr}\nVault Key: {vault_token}\n"

                _import_vault_keys(key_content)

            case _:
                raise ValueError(f"Unsupported key type: {keyType}")

    def edit(self, secrets_file: str, sops_file: str) -> None:
        """
        Edit secrets using SOPS.
        Args:
            secrets_file (str): Path to the secrets file.
            sops_file (str): Path to the SOPS file.
        """
        sops_command = ['sops', '--config', sops_file, secrets_file]
        with self.setupEphemeralEnv() as ctx:
            prefix = ctx.get("prefix", "")
            pass_fds = ctx.get("pass_fds", [])
            env = ctx.get("env", os.environ.copy())
            cmd = shlex.join(sops_command)

            if prefix:
                cmd = f"{prefix} {cmd}"

            try:
                subprocess.run(
                    cmd,
                    check=True,
                    env=env,
                    pass_fds=pass_fds,
                    shell=True,
                    stderr=subprocess.PIPE,
                    text=True
                )
            except subprocess.CalledProcessError as e:
                if e.returncode == 200:
                    return
                err = e.stderr.strip() if e.stderr else "No additional error information."
                raise RuntimeError(f"Error running SOPS edit command: {err}") from e

    def decrypt(self, secrets_file: str, sops_file: str) -> str:
        """
        Decrypt secrets using SOPS.
        Args:
            secrets_file (str): Path to the secrets file.
            sops_file (str): Path to the SOPS file.
        returns:
            str: Decrypted secrets content.
        """
        sops_command = ['sops', '--config', sops_file, '-d', secrets_file]
        result = self._run_sops_command(sops_command).stdout
        return result

    def updatekeys(self, secrets_file: str, sops_file: str) -> None:
        """
        Update keys on a SOPS encrypted file.
        Args:
            secrets_file (str): Path to the secrets file.
            sops_file (str): Path to the SOPS file.
        """
        sops_command = ['sops', '--config', sops_file, 'updatekeys', '-y', secrets_file]
        self._run_sops_command(sops_command)

    def _run_sops_command(self, command: list[str]) -> subprocess.CompletedProcess:
        """
        Run a SOPS command in a subprocess.
        Args:
            command (list): List of command arguments to run.
        returns:
            subprocess.CompletedProcess: The result of the subprocess execution.
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

