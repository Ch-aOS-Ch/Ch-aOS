import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Tuple

from chaos.lib.utils import checkDep

from ..utils import extract_gpg_keys, get_sops_files, setup_vault_keys
from .base import Provider


class OnePasswordProvider(Provider):
    """
    1Password secret backend provider.
    Implements methods to manage secrets using 1Password CLI.
    """

    @staticmethod
    def get_cli_name() -> Tuple[str, str]:
        return "from_op", "op"

    @staticmethod
    def register_flags(parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--from-op",
            "-o",
            nargs=2,
            metavar=("ITEM_ID", "FIELD"),
            help="Read ephemeral key from 1Password item and field.",
        )

    @staticmethod
    def register_export_subcommands(
        subparser: argparse._SubParsersAction,
    ) -> argparse.ArgumentParser:
        secOpExport = subparser.add_parser("op", help="1Password CLI export options")
        secOpExport.add_argument(
            "-i",
            "--item-id",
            help="1Password item URL where to export the key (format: op://vault/item).",
        )
        secOpExport.add_argument(
            "-l",
            "--op-location",
            dest="op_location",
            default="notesPlain",
            help="Field name in 1Password item where the key will be stored (default: notesPlain).",
        )
        secOpExport.add_argument(
            "-g",
            "--tags",
            dest="op_tags",
            nargs="*",
            default=[],
            help="Tags to add to the 1Password item.",
        )

        return secOpExport

    @staticmethod
    def register_import_subcommands(
        subparser: argparse._SubParsersAction,
    ) -> argparse.ArgumentParser:
        secOpImport = subparser.add_parser("op", help="1Password CLI import options")
        return secOpImport

    def export_secrets(self) -> None:
        from rich.console import Console

        console = Console()
        args = self.args

        keyType = args.key_type
        keyPath = args.keys
        fingerprints = args.fingerprints
        tags = args.op_tags
        save_to_config = args.save_to_config
        no_import = args.no_import

        _, _, config = get_sops_files(None, None, None)
        path = (
            config.get("secret_providers", {}).get("op", {}).get(f"{keyType}_url", "")
        )

        if args.item_id:
            path = args.item_id

        loc = args.op_location

        vault, title, _ = self._reg_match_op_keypath(path)
        if self._op_get_item(vault, title) is not None:
            raise ValueError(f"The item '{title}' already exists in vault '{vault}'")

        if keyType == "age":
            if not keyPath:
                raise ValueError("No age key path passed via --keys.")

            keyPath = Path(keyPath).expanduser()
            if not keyPath.exists():
                raise FileNotFoundError(f"Path {keyPath} does not exist.")
            if not keyPath.is_file():
                raise ValueError(f"Path {keyPath} is not a file.")

            with open(keyPath, "r") as f:
                key = f.read()

            if no_import:
                key = f"# NO-IMPORT\n{key}"

            if not all([key, path, loc]):
                raise ValueError(
                    "Missing required parameters for exporting keys to 1Password."
                )

            self._op_create_item(vault, title, loc, tags, key)

            pubkey = ""
            for line in key.splitlines():
                if line.strip().startswith("# public key:"):
                    pubkey = line.split("# public key:", 1)[1].strip()
                    break
            if pubkey:
                console.print(
                    f"[green]INFO:[/] Successfully exported {keyType} public key to 1Password: {pubkey}"
                )

        elif keyType == "gpg":
            if not fingerprints:
                raise ValueError(
                    "At least one GPG fingerprint is required. Please provide it with --fingerprints."
                )

            if not checkDep("gpg"):
                raise EnvironmentError(
                    "The 'gpg' CLI tool is required but not found in PATH."
                )

            key_content = extract_gpg_keys(fingerprints)
            if no_import:
                key_content = f"# NO-IMPORT\n{key_content}"

            if not all([key_content, path, loc]):
                raise ValueError(
                    "Missing required parameters for exporting keys to 1Password."
                )

            self._op_create_item(vault, title, loc, tags, key_content)

            console.print(
                f"[green]INFO:[/] Successfully exported GPG keys for to 1Password: '{', '.join(fingerprints)}'"
            )

        elif keyType == "vault":
            vaultAddr = args.vault_addr
            if not keyPath:
                raise ValueError("No Vault key path passed via --keys.")
            if not vaultAddr:
                raise ValueError("No Vault address passed via --vault-addr.")
            keyPath = Path(keyPath).expanduser()

            key_content = setup_vault_keys(vaultAddr, keyPath)
            if no_import:
                key_content = f"# NO-IMPORT\n{key_content}"

            if not all([key_content, path, loc]):
                raise ValueError(
                    "Missing required parameters for exporting keys to 1Password."
                )

            self._op_create_item(vault, title, loc, tags, key_content)
            console.print(
                "[green]INFO:[/] Successfully exported vault token to 1Password."
            )
        else:
            raise ValueError(f"Unsupported key type: {keyType}")

        if save_to_config:
            data_to_save = {f"{keyType}_url": path, "field": loc}
            from ..utils import _save_to_config

            _save_to_config(backend="op", data_to_save=data_to_save)

    def readKeys(self, item_id: str) -> str:
        if not checkDep("op"):
            raise EnvironmentError(
                "The 'op' CLI tool is required but not found in PATH."
            )

        if not item_id:
            raise ValueError("The provided 1Password path is invalid.")

        try:
            result = subprocess.run(
                ["op", "read", item_id], capture_output=True, text=True, check=True
            )

            if not result.stdout.strip():
                raise ValueError("No output received from 'op read' command.")
            return result.stdout.strip()

        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"Error reading secret from 1Password: {e.stderr.strip()}"
            ) from e

    def get_ephemeral_key_args(self) -> tuple[str, str] | None:
        return self.args.from_op

    def check_status(self):
        try:
            subprocess.run(
                ["op", "account", "get"], capture_output=True, text=True, check=True
            )
            return True, "1Password CLI is installed and configured."
        except subprocess.CalledProcessError:
            raise EnvironmentError(
                "1Password CLI is not installed or not configured properly."
            )

    def _build_op_keypath(self, key: str, loc: str) -> str:
        match = re.match(r"op://([^/]+)/([^/]+)(?:/([^/]+))?", key)
        if not match:
            raise ValueError(
                f"Invalid 1Password key format: {key}. Expected format like 'op://vault/item'."
            )

        vault, item, field_in_key = match.groups()

        if field_in_key:
            if loc and field_in_key != loc:
                raise ValueError(
                    f"Path '{key}' already specifies a field ('{field_in_key}'), "
                    f"which conflicts with the provided location ('{loc}')."
                )
            return key

        if not loc:
            raise ValueError(
                "A field location must be provided when the key path does not contain one."
            )

        return f"op://{vault}/{item}/{loc}"

    def _reg_match_op_keypath(self, path: str) -> tuple[str, str, str | None]:
        regMatch = re.match(r"op://([^/]+)/([^/]+)(?:/(.+))?", path)
        if not regMatch:
            raise ValueError(f"Invalid 1Password path format: {path}")
        vault, title, field = regMatch.group(1), regMatch.group(2), regMatch.group(3)
        return vault, title, field

    def _op_get_item(self, vault: str, title: str) -> dict | None:
        try:
            result = subprocess.run(
                ["op", "item", "get", title, "--vault", vault, "--format", "json"],
                capture_output=True,
                text=True,
                check=True,
            )
            item_data = result.stdout.strip()
            if not item_data:
                return None
            return json.loads(item_data)

        except subprocess.CalledProcessError as e:
            if "isn't in vault" in e.stderr or "no item found" in e.stderr:
                return None
            raise RuntimeError(
                f"Error retrieving item from 1Password: {e.stderr.strip()}"
            ) from e

    def _op_create_item(
        self, vault: str, title: str, field: str, tags: list[str], key: str
    ) -> bool:
        from rich.console import Console

        console = Console()
        try:
            field_args = []
            for tag in tags:
                field_args.extend(["--tag", tag])

            field_args.extend(["--field", f"{field}={key}"])
            subprocess.run(
                [
                    "op",
                    "item",
                    "create",
                    "--title",
                    title,
                    "--vault",
                    vault,
                    "--category=password",
                ]
                + field_args,
                capture_output=True,
                text=True,
                check=True,
            )
            console.print(
                f"[green]INFO:[/] Successfully created item '{title}' in vault '{vault}'."
            )
            return True
        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"Error creating item in 1Password: {e.stderr.strip()}"
            ) from e
