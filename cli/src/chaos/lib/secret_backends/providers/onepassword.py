from __future__ import annotations

import argparse
import json
import re
import subprocess
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, cast

from chaos.lib.args.dataclasses import (
    ProviderExportArgs,
    ProviderImportArgs,
    ResultPayload,
    SecretsExportPayload,
)
from chaos.lib.utils import checkDep

from .base import Provider


@dataclass(frozen=True)
class OnePasswordExportArgs(ProviderExportArgs):
    op_export_item_id: Optional[str] = None
    op_location: str = "notesPlain"
    op_tags: List[str] = field(default_factory=list)


class OnePasswordProvider(Provider):
    """
    1Password secret backend provider.
    Implements methods to manage secrets using 1Password CLI.
    """

    @classmethod
    def build_export_args(cls, **kwargs) -> OnePasswordExportArgs:
        return OnePasswordExportArgs(**kwargs)

    @classmethod
    def build_import_args(cls, **kwargs) -> ProviderImportArgs:
        return ProviderImportArgs()

    @staticmethod
    def get_export_arg_names() -> List[str]:
        return ["op_export_item_id", "op_location", "op_tags"]

    @staticmethod
    def get_import_arg_names():
        return []

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
            dest="op_export_item_id",
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

    def export_secrets(self, payload: SecretsExportPayload) -> ResultPayload:
        messages = []
        errors = []

        try:
            provider_args = cast(OnePasswordExportArgs, payload.provider_specific_args)

            keyType = payload.key_type
            tags = provider_args.op_tags
            save_to_config = payload.save_to_config

            config = self.config

            path = (
                config.get("secret_providers", {})
                .get("op", {})
                .get(f"{keyType}_url", "")
            )

            if provider_args.op_export_item_id:
                path = provider_args.op_export_item_id

            loc = provider_args.op_location or "notesPlain"

            if not path:
                raise ValueError(
                    "No 1Password item URL provided. Please specify it with --item-id or in the config file."
                )

            vault, title, _ = self._reg_match_op_keypath(path)
            if self._op_get_item(vault, title) is not None:
                raise ValueError(
                    f"The item '{title}' already exists in vault '{vault}'"
                )

            from chaos.lib.secret_backends.key_backends.factory import get_key_backend

            try:
                key_backend = get_key_backend(keyType)
                key_content, prep_msgs = key_backend.prepare_export_content(payload)
                messages.extend(prep_msgs)
            except ValueError as e:
                raise ValueError(f"Unsupported key type or error loading backend: {e}")

            if not all([key_content, path, loc]):
                raise ValueError(
                    "Missing required parameters for exporting keys to 1Password."
                )

            _, msg = self._op_create_item(vault, title, loc, tags, key_content)
            messages.extend(msg)

            if save_to_config:
                data_to_save = {f"{keyType}_url": path, "field": loc}
                from ..utils import _save_to_config

                _save_to_config(backend="op", data_to_save=data_to_save)

        except Exception as e:
            errors.append(str(e))
            return ResultPayload(success=False, error=errors, message=messages)

        return ResultPayload(success=True, message=messages)

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
        from chaos.lib.args.dataclasses import SecretsContext

        if isinstance(self.payload, SecretsContext) and self.payload.provider_config:
            return self.payload.provider_config.ephemeral_provider_args.get("from_op")
        return None

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
    ) -> tuple[bool, list]:
        messages = []
        try:
            item_json = {
                "title": title,
                "category": "PASSWORD",
                "tags": tags,
                "fields": [
                    {
                        "id": field,
                        "type": "CONCEALED",
                        "label": field,
                        "value": key,
                    }
                ],
            }
            json_data = json.dumps(item_json)

            subprocess.run(
                [
                    "op",
                    "item",
                    "create",
                    "--vault",
                    vault,
                    "-",
                ],
                input=json_data,
                capture_output=True,
                text=True,
                check=True,
            )
            messages.append(f"Successfully created item '{title}' in vault '{vault}'.")
            return True, messages
        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"Error creating item in 1Password: {e.stderr.strip()}"
            ) from e
