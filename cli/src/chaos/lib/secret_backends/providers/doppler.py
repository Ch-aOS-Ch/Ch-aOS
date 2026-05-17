import argparse
import os
import subprocess
from dataclasses import dataclass
from typing import Literal, cast

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
class DopplerExportArgs(ProviderExportArgs):
    project_name: str
    visibility: Literal["masked", "unmasked", "restricted"]
    note: str | None = None
    config_name: str | None = None


class DopplerProvider(Provider):
    @classmethod
    def build_export_args(cls, **kwargs) -> DopplerExportArgs:
        return DopplerExportArgs(**kwargs)

    @classmethod
    def build_import_args(cls, **kwargs) -> ProviderImportArgs:
        return ProviderImportArgs(**kwargs)

    @staticmethod
    def get_cli_name() -> tuple[str, str]:
        return "from_doppler", "dp"

    @staticmethod
    def get_export_arg_names() -> list[str]:
        return ["project_name", "visibility", "note", "config_name"]

    @staticmethod
    def get_import_arg_names():
        return []

    @staticmethod
    def register_flags(parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--from-doppler",
            "-dp",
            type=str,
            nargs=2,
            metavar=("ITEM_ID", "KEY_TYPE"),
            help="Retrieve ephemeral keys from Doppler. Provide ITEM_ID and KEY_TYPE (age/gpg/vault).\n ITEM_ID format: <secret_name>:<project_name>:<config_name?>.\n project_name and config_name can also be set via config file.",
        )

    @staticmethod
    def register_export_subcommands(
        subparser: argparse._SubParsersAction,
    ) -> argparse.ArgumentParser:
        secDopExport = subparser.add_parser("dp", help="Doppler CLI export options")
        secDopExport.add_argument(
            "-p",
            "--project-name",
            type=str,
            required=True,
            help="Doppler project name to export secrets from",
        )
        secDopExport.add_argument(
            "-v",
            "--visibility",
            type=str,
            choices=["masked", "unmasked", "restricted"],
            default="masked",
            help="Visibility of secrets to export (default: masked)",
        )
        secDopExport.add_argument(
            "-c",
            "--config-name",
            type=str,
            help="Doppler config name to export secrets from",
        )
        secDopExport.add_argument(
            "-o",
            "--note",
            type=str,
            help="Optional note to include with the exported secret.",
        )

        return secDopExport

    @staticmethod
    def register_import_subcommands(
        subparser: argparse._SubParsersAction,
    ) -> argparse.ArgumentParser:
        secDopImport = subparser.add_parser("dp", help="Doppler CLI import options")
        return secDopImport

    def export_secrets(self, payload: SecretsExportPayload) -> ResultPayload:
        from chaos.lib.secret_backends.key_backends.factory import get_key_backend

        self.check_status()
        payload.provider_specific_args = cast(
            DopplerExportArgs, payload.provider_specific_args
        )
        save_to_config = payload.save_to_config

        token = os.getenv("DOPPLER_TOKEN", "")

        project: str = ""
        config_name: str = ""

        messages: list[str] = []
        errors: list[str] = []

        item_id = payload.item_name
        if not item_id:
            errors.append("Item name is required for Doppler export.")
            return ResultPayload(success=False, error=errors, message=messages)

        project = payload.provider_specific_args.project_name or project
        config_name = payload.provider_specific_args.config_name or config_name

        if not project and ":" in item_id:
            parts = item_id.split(":")
            if len(parts) > 3:
                errors.append(
                    "Invalid ITEM_ID format. Expected format: <secret_name>:<project_name>:<config_name?>"
                )
                return ResultPayload(success=False, error=errors, message=messages)
            item_id = parts[0]
            if len(parts) >= 2:
                project = parts[1]

            if len(parts) == 3:
                config_name = parts[2]

        if not project:
            project = (
                self.config.get("secret_backends", {})
                .get("dp", {})
                .get("project_name", "")
            )

        if not project:
            errors.append(
                "Project name is required to read secrets from Doppler.\n  Please add a 'secret_backends.doppler.project_name' entry to your config file."
            )
            return ResultPayload(success=False, error=errors, message=messages)

        if not config_name:
            config_name = (
                self.config.get("secret_backends", {})
                .get("dp", {})
                .get("config_name", "")
            )

        if not token and not config_name:
            errors.append(
                "No authentication method found for Doppler CLI.\n  Please set a DOPPLER_TOKEN environment variable\n  or specify 'secret_backends.dp.config_name' to your config."
            )
            return ResultPayload(success=False, error=errors, message=messages)

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
            "doppler",
            "secrets",
            "set",
            "--project",
            project,
            "--visibility",
            payload.provider_specific_args.visibility,
        ]
        if config_name:
            cmd.extend(["--config", config_name])
        cmd.append(item_id)

        env = os.environ.copy()
        if token:
            env["DOPPLER_TOKEN"] = token

        if payload.provider_specific_args.note:
            note_set_cmd = [
                "doppler",
                "secrets",
                "notes",
                "set",
                "--project",
                project,
            ]
            if config_name:
                note_set_cmd.extend(["--config", config_name])
            note_set_cmd.append(item_id)
            note_set_cmd.append(payload.provider_specific_args.note)

        try:
            _ = subprocess.run(
                cmd,
                input=key_content,
                text=True,
                capture_output=True,
                check=True,
                env=env,
            )
        except subprocess.CalledProcessError as e:
            if "Invalid reference format" in e.stderr.strip():
                # Replace e.stderr with a more user-friendly message about escaping special characters
                # Also, the normal message leaked the secret value to the stdout, which is a security risk
                e.stderr = "Doppler CLI error: Invalid reference format. This often occurs when the secret value contains characters that are not properly escaped."
            errors.append(
                f"Failed to export secret to Doppler.\nError details: {e.stderr.strip()}"
            )
            return ResultPayload(success=False, error=errors, message=messages)

        if payload.provider_specific_args.note:
            try:
                _ = subprocess.run(
                    note_set_cmd,
                    text=True,
                    capture_output=True,
                    check=True,
                    env=env,
                )
            except subprocess.CalledProcessError as e:
                errors.append(
                    f"Secret was exported to Doppler, but failed to set note.\nError details: {e.stderr.strip()}"
                )
                return ResultPayload(success=False, error=errors, message=messages)

        messages.append(
            f"Successfully exported {payload.key_type} key to Doppler (ID: '{item_id}')."
        )
        if item_id and save_to_config:
            messages.append(f"Saving Doppler item ID '{item_id}' to chaos config.")
            data_to_save = {f"{payload.key_type}_id": item_id}
            _save_to_config(backend="dp", data_to_save=data_to_save)
        return ResultPayload(success=True, message=messages)

    def check_status(self) -> None | tuple[bool, str]:
        if not checkDep("doppler"):
            raise RuntimeError("The Doppler CLI is required but not found in PATH.")

        try:
            me_result = subprocess.run(
                ["doppler", "me", "--json"], capture_output=True, text=True, check=True
            )
            status_info = me_result.stdout.strip()
        except subprocess.CalledProcessError as e:
            raise PermissionError(
                f"Doppler CLI is installed but not authed, run `doppler login` to authenticate.\nError details: {e.stderr.strip()}"
            )

        if "Doppler Error" in status_info:
            raise PermissionError(
                f"Doppler CLI is installed but not authed, run `doppler login` to authenticate.\nError details: {status_info}"
            )

        return True, "Doppler CLI is installed and authenticated."

    def readKeys(self, item_id: str) -> str:
        token = os.getenv("DOPPLER_TOKEN", "")

        project: str = ""
        config_name: str = ""

        if ":" in item_id:
            parts = item_id.split(":")
            if len(parts) > 3:
                raise ValueError(
                    "Invalid ITEM_ID format. Expected format: <secret_name>:<project_name>:<config_name?>"
                )
            item_id = parts[0]
            if len(parts) >= 2:
                project = parts[1]

            if len(parts) == 3:
                config_name = parts[2]

        if not project:
            project = (
                self.config.get("secret_backends", {})
                .get("dp", {})
                .get("project_name", "")
            )

        if not project:
            raise RuntimeError(
                "Project name is required to read secrets from Doppler.\n  Please add a 'secret_backends.dp.project_name' entry to your config file."
            )

        if not config_name:
            config_name = (
                self.config.get("secret_backends", {})
                .get("dp", {})
                .get("config_name", "")
            )

        if not token and not config_name:
            raise RuntimeError(
                "No authentication method found for Doppler CLI.\n  Please set a DOPPLER_TOKEN environment variable\n  or specify 'secret_backends.dp.config_name' to your config."
            )

        cmd = ["doppler", "secrets", "get", item_id, "--plain", "--project", project]
        if config_name:
            cmd.extend(["--config", config_name])

        env = os.environ.copy()

        if token:
            env["DOPPLER_TOKEN"] = token

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, check=True, env=env
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            if "restricted secrets" in e.stderr:
                raise PermissionError(
                    f"Access denied when trying to read secret, please, use a token with access to restricted secrets.\nError details: {e.stderr.strip()}"
                )
            raise RuntimeError(
                f"Failed to read secret from Doppler.\nError details: {e.stderr.strip()}"
            )

    def get_ephemeral_key_args(self) -> tuple[str, str] | None:
        from chaos.lib.args.dataclasses import SecretsContext

        if isinstance(self.payload, SecretsContext) and self.payload.provider_config:
            return self.payload.provider_config.ephemeral_provider_args.get(
                "from_doppler"
            )
        return None
