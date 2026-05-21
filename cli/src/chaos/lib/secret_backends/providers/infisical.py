from __future__ import annotations

import argparse
import subprocess
from dataclasses import dataclass
from typing import cast

from chaos.lib.args.dataclasses import (
    ProviderExportArgs,
    ProviderImportArgs,
    ResultPayload,
    SecretsExportPayload,
)
from chaos.lib.secret_backends.utils import _save_to_config
from chaos.lib.utils import checkDep

from .base import Provider


@dataclass(frozen=True, slots=True)
class InfisicalExportArgs(ProviderExportArgs):
    env_name: str = "dev"
    secret_path: str = "/"
    project_id: str | None = None
    secret_type: str = "shared"


class InfisicalProvider(Provider):
    @classmethod
    def build_export_args(cls, **kwargs) -> InfisicalExportArgs:
        return InfisicalExportArgs(**kwargs)

    @classmethod
    def build_import_args(cls, **kwargs) -> ProviderImportArgs:
        return ProviderImportArgs(**kwargs)

    @staticmethod
    def get_cli_name() -> tuple[str, str]:
        return "from_in", "in"

    @staticmethod
    def get_export_arg_names() -> list[str]:
        return ["env_name", "secret_path", "project_id", "secret_type"]

    @staticmethod
    def get_import_arg_names():
        return []

    @staticmethod
    def register_flags(parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--from-in",
            "-I",
            type=str,
            nargs=2,
            metavar=("ITEM_ID", "KEY_TYPE"),
            help="Retrieve ephemeral keys from Infisical. Provide ITEM_ID and KEY_TYPE (age/gpg/vault).\n ITEM_ID format: <secret_name>:<project_id>:<env_name>:<secret_path>.\n project_id, env_name, and secret_path can also be set via config file.",
        )

    @staticmethod
    def register_export_subcommands(
        subparser: argparse._SubParsersAction,
    ) -> argparse.ArgumentParser:
        secInfExport = subparser.add_parser("in", help="Infisical CLI export options")
        secInfExport.add_argument(
            "-e",
            "--env-name",
            dest="env_name",
            type=str,
            default="dev",
            help="Environment name (default: dev)",
        )
        secInfExport.add_argument(
            "-P",
            "--secret-path",
            dest="secret_path",
            type=str,
            default="/",
            help="Secret path (default: /)",
        )
        secInfExport.add_argument(
            "--project-id",
            dest="project_id",
            type=str,
            help="Infisical Project ID",
        )
        secInfExport.add_argument(
            "-T",
            "--secret-type",
            dest="secret_type",
            type=str,
            choices=["shared", "personal"],
            default="shared",
            help="Secret type (shared or personal, default: shared)",
        )
        return secInfExport

    @staticmethod
    def register_import_subcommands(
        subparser: argparse._SubParsersAction,
    ) -> argparse.ArgumentParser:
        secInfImport = subparser.add_parser("in", help="Infisical CLI import options")
        return secInfImport

    def export_secrets(self, payload: SecretsExportPayload) -> ResultPayload:
        from chaos.lib.secret_backends.key_backends.factory import get_key_backend

        self.check_status()
        payload.provider_specific_args = cast(
            InfisicalExportArgs, payload.provider_specific_args
        )
        save_to_config = payload.save_to_config

        messages: list[str] = []
        errors: list[str] = []

        item_id = payload.item_name
        if not item_id:
            errors.append("Item name is required for Infisical export.")
            return ResultPayload(success=False, error=errors, message=messages)

        env_name = payload.provider_specific_args.env_name
        secret_path = payload.provider_specific_args.secret_path
        project_id = payload.provider_specific_args.project_id
        secret_type = payload.provider_specific_args.secret_type

        if ":" in item_id:
            parts = item_id.split(":")
            if len(parts) > 4:
                errors.append(
                    "Invalid ITEM_ID format. Expected format: <secret_name>:<project_id>:<env_name>:<secret_path>"
                )
                return ResultPayload(success=False, error=errors, message=messages)
            item_id = parts[0]
            if len(parts) >= 2 and parts[1]:
                project_id = parts[1]
            if len(parts) >= 3 and parts[2]:
                env_name = parts[2]
            if len(parts) >= 4 and parts[3]:
                secret_path = parts[3]

        if not env_name:
            env_name = (
                self.config.get("secret_backends", {})
                .get("in", {})
                .get("env_name", "dev")
            )

        if not env_name:
            env_name = "dev"

        if not secret_path:
            secret_path = (
                self.config.get("secret_backends", {})
                .get("in", {})
                .get("secret_path", "/")
            )

        if not project_id:
            project_id = (
                self.config.get("secret_backends", {})
                .get("in", {})
                .get("project_id", "")
            )

        try:
            backend = get_key_backend(payload.key_type)
            key_content, prep_msgs = backend.prepare_export_content(payload)
            messages.extend(prep_msgs)
        except ValueError as e:
            errors.append(f"Unsupported key type or error loading backend: {e}")
            return ResultPayload(success=False, error=errors, message=messages)
        except Exception as e:
            errors.append(f"Error preparing key content for export: {e}")
            return ResultPayload(success=False, error=errors, message=messages)

        if not key_content:
            errors.append("No key content generated for export.")
            return ResultPayload(success=False, error=errors, message=messages)

        cmd = [
            "infisical",
            "secrets",
            "set",
            f"{item_id}=@/dev/stdin",
            "--env",
            env_name,
            "--path",
            secret_path,
            "--type",
            secret_type,
        ]

        if project_id:
            cmd.extend(["--projectId", project_id])

        try:
            _ = subprocess.run(
                cmd,
                text=True,
                capture_output=True,
                check=True,
                input=key_content,
            )
        except subprocess.CalledProcessError as e:
            errors.append(
                f"Failed to export secret to Infisical.\nError details: {e.stderr.strip() or e.stdout.strip()}"
            )
            return ResultPayload(success=False, error=errors, message=messages)

        messages.append(
            f"Successfully exported {payload.key_type} key to Infisical (ID: '{item_id}')."
        )
        if save_to_config:
            id_to_save = item_id
            if project_id or env_name != "dev" or secret_path != "/":
                id_to_save += f":{project_id or ''}"
                if env_name != "dev" or secret_path != "/":
                    id_to_save += f":{env_name}"
                    if secret_path != "/":
                        id_to_save += f":{secret_path}"

            messages.append(f"Saving Infisical item ID '{id_to_save}' to chaos config.")

            data_to_save = {
                f"{payload.key_type}_id": id_to_save,
            }
            _save_to_config(backend="in", data_to_save=data_to_save)

        return ResultPayload(success=True, message=messages)

    def check_status(self) -> None | tuple[bool, str]:
        if not checkDep("infisical"):
            raise RuntimeError("The Infisical CLI is required but not found in PATH.")

        return True, "Infisical CLI is installed."

    def readKeys(self, item_id: str) -> str:
        env_name = (
            self.config.get("secret_backends", {}).get("in", {}).get("env_name", "dev")
        )
        secret_path = (
            self.config.get("secret_backends", {}).get("in", {}).get("secret_path", "/")
        )
        project_id = (
            self.config.get("secret_backends", {}).get("in", {}).get("project_id", "")
        )

        if ":" in item_id:
            parts = item_id.split(":")
            if len(parts) > 4:
                raise ValueError(
                    "Invalid ITEM_ID format. Expected format: <secret_name>:<project_id>:<env_name>:<secret_path>"
                )
            item_id = parts[0]
            if len(parts) >= 2 and parts[1]:
                project_id = parts[1]
            if len(parts) >= 3 and parts[2]:
                env_name = parts[2]
            if len(parts) >= 4 and parts[3]:
                secret_path = parts[3]

        cmd = [
            "infisical",
            "secrets",
            "get",
            item_id,
            "--plain",
            "--env",
            env_name,
            "--path",
            secret_path,
        ]

        if project_id:
            cmd.extend(["--projectId", project_id])

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"Failed to read secret from Infisical.\nError details: {e.stderr.strip() or e.stdout.strip()}"
            )

    def get_ephemeral_key_args(self) -> tuple[str, str] | None:
        from chaos.lib.args.dataclasses import SecretsContext

        if isinstance(self.payload, SecretsContext) and self.payload.provider_config:
            return self.payload.provider_config.ephemeral_provider_args.get(
                "from_infisical"
            )
        return None
