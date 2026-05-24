from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from typing import cast

from chaos.lib.args.dataclasses import (
    ProviderExportArgs,
    ProviderImportArgs,
    ResultPayload,
    SecretsExportPayload,
)

from .base import Provider


@dataclass(frozen=True)
class BitwardenExportArgs(ProviderExportArgs):
    organization_id: str | None = None
    collection_id: str | None = None
    bw_tags: tuple[str, ...] = ()


class BitwardenPasswordProvider(Provider):
    @classmethod
    def build_export_args(cls, **kwargs) -> BitwardenExportArgs:
        return BitwardenExportArgs(**kwargs)

    @classmethod
    def build_import_args(cls, **kwargs) -> ProviderImportArgs:
        return ProviderImportArgs()

    @staticmethod
    def get_export_arg_names() -> list[str]:
        return ["organization_id", "collection_id", "bw_tags"]

    @staticmethod
    def get_import_arg_names():
        return []

    @staticmethod
    def get_cli_name() -> tuple[str, str]:
        return "from_bw", "bw"

    @staticmethod
    def register_flags(parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--from-bw",
            "-b",
            type=str,
            nargs=2,
            metavar=("ITEM_ID", "KEY_TYPE"),
            help="Retrieve ephemeral keys from Bitwarden. Provide ITEM_ID and KEY_TYPE (age/gpg/vault).",
        )

    @staticmethod
    def register_export_subcommands(
        subparser: argparse._SubParsersAction,
    ) -> argparse.ArgumentParser:
        secBwExport = subparser.add_parser("bw", help="Bitwarden CLI export options")
        secBwExport.add_argument(
            "-o", "--organization-id", help="Organization ID where to create the item."
        )
        secBwExport.add_argument(
            "-c",
            "--collection-id",
            dest="collection_id",
            help="The ID of the collection to add the item to.",
        )
        secBwExport.add_argument(
            "--bw-tags",
            dest="bw_tags",
            nargs="*",
            default=[],
            help="Tags to add to the Bitwarden item.",
        )

        return secBwExport

    @staticmethod
    def register_import_subcommands(
        subparser: argparse._SubParsersAction,
    ) -> argparse.ArgumentParser:
        secBwImport = subparser.add_parser("bw", help="Bitwarden CLI import options")
        return secBwImport

    def export_secrets(self, payload: SecretsExportPayload) -> ResultPayload:
        import base64
        import json
        import subprocess

        from ..utils import _save_to_config

        """
        Exports keys to Bitwarden as new notes.
        """
        self.check_status()
        messages = []
        errors = []

        try:
            provider_args = cast(BitwardenExportArgs, payload.provider_specific_args)

            keyType = payload.key_type
            item_name = payload.item_name
            tags = provider_args.bw_tags
            save_to_config = payload.save_to_config

            collection_id = (
                self.config.get("secret_providers", {})
                .get("bw", {})
                .get("collection_id", "")
            )
            organization_id = (
                self.config.get("secret_providers", {})
                .get("bw", {})
                .get("organization_id", "")
            )

            if provider_args.collection_id:
                collection_id = provider_args.collection_id
            if provider_args.organization_id:
                organization_id = provider_args.organization_id

            from chaos.lib.secret_backends.key_backends.factory import get_key_backend

            try:
                key_backend = get_key_backend(keyType)
                key_content, prep_msgs = key_backend.prepare_export_content(payload)
                messages.extend(prep_msgs)
            except ValueError as e:
                raise ValueError(f"Unsupported key type or error loading backend: {e}")
            except ImportError as e:
                raise ImportError(
                    f"Error importing key backend for type '{keyType}': {e}"
                ) from e

            if not key_content:
                raise ValueError("No key content to export.")

            template_str = subprocess.run(
                ["bw", "get", "template", "item"],
                capture_output=True,
                text=True,
                check=True,
            ).stdout
            item_json = json.loads(template_str)

            item_json["type"] = 1
            item_json["login"] = {"username": "ch-aos", "password": "ch-aos"}
            item_json["name"] = f"Ch-aOS {keyType.upper()} Key: {item_name}"
            item_json["notes"] = key_content
            if collection_id:
                if not organization_id:
                    raise ValueError(
                        "When specifying a collection ID, an organization ID must also be provided."
                    )
                item_json["collectionIds"] = [collection_id]
            if organization_id:
                item_json["organizationId"] = organization_id
            if tags:
                item_json["fields"] = [tags]
            item_json["favorite"] = False

            item_str = json.dumps(item_json)
            encoded_item = base64.b64encode(item_str.encode()).decode()

            created_item_json = subprocess.run(
                ["bw", "create", "item", encoded_item],
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip()

            created_item = json.loads(created_item_json)
            item_id = created_item.get("id")

            messages.append(
                f"Successfully exported {keyType} key to Bitwarden item '{created_item['name']}' (ID: {created_item['id']})."
            )

            if save_to_config and item_id:
                data_to_save = {f"{keyType}_id": item_id}
                if collection_id:
                    data_to_save["collection_id"] = collection_id
                if organization_id:
                    data_to_save["organization_id"] = organization_id
                _save_to_config(backend="bw", data_to_save=data_to_save)

        except Exception as e:
            errors.append(str(e))
            return ResultPayload(success=False, error=errors, message=messages)

        return ResultPayload(success=True, message=messages)

    def check_status(self):
        import json
        import subprocess

        from chaos.lib.utils import checkDep

        if not checkDep("bw"):
            raise EnvironmentError(
                "The 'bw' CLI tool is required but not found in PATH."
            )

        try:
            status_result = subprocess.run(
                ["bw", "status"], capture_output=True, text=True, check=True
            )
            status = json.loads(status_result.stdout)

            if status["status"] == "unlocked":
                return True, "Bitwarden vault is unlocked."

            elif status["status"] == "locked":
                raise PermissionError(
                    "Bitwarden vault is locked. Please unlock it first with 'bw unlock'."
                )

            else:  # "unauthenticated"
                raise PermissionError(
                    "You are not logged into Bitwarden. Please log in first with 'bw login'."
                )

        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"Failed to check Bitwarden status: {e.stderr.strip()}"
            ) from e
        except (json.JSONDecodeError, KeyError) as e:
            raise RuntimeError(f"Failed to parse Bitwarden status: {e}")

    def readKeys(self, item_id: str) -> str:
        import subprocess

        try:
            result = subprocess.run(
                ["bw", "get", "notes", item_id],
                capture_output=True,
                text=True,
                check=True,
            )
            if not result.stdout.strip():
                raise ValueError(
                    f"No notes found in Bitwarden item with ID '{item_id}'. The key should be in the 'notes' field."
                )
            return result.stdout.strip()

        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"Error reading secret from Bitwarden item '{item_id}': {e.stderr.strip()}"
            ) from e

    def get_ephemeral_key_args(self) -> tuple[str, str] | None:
        from chaos.lib.args.dataclasses import SecretsContext

        if isinstance(self.payload, SecretsContext) and self.payload.provider_config:
            return self.payload.provider_config.ephemeral_provider_args.get("from_bw")
        return None


@dataclass(frozen=True)
class BitwardenSecretsExportArgs(ProviderExportArgs):
    project_id: str | None = None


class BitwardenSecretsProvider(Provider):
    @classmethod
    def build_export_args(cls, **kwargs) -> BitwardenSecretsExportArgs:
        return BitwardenSecretsExportArgs(**kwargs)

    @classmethod
    def build_import_args(cls, **kwargs) -> ProviderImportArgs:
        return ProviderImportArgs()

    @staticmethod
    def get_export_arg_names() -> list[str]:
        return ["project_id"]

    @staticmethod
    def get_import_arg_names():
        return []

    @staticmethod
    def get_cli_name() -> tuple[str, str]:
        return "from_bws", "bws"

    @staticmethod
    def register_flags(parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--from-bws",
            "-B",
            type=str,
            nargs=2,
            metavar=("ITEM_ID", "KEY_TYPE"),
            help="Retrieve ephemeral keys from Bitwarden Secrets CLI. Provide ITEM_ID and KEY_TYPE (age/gpg/vault).",
        )

    @staticmethod
    def register_export_subcommands(
        subparser: argparse._SubParsersAction,
    ) -> argparse.ArgumentParser:
        secBwsExport = subparser.add_parser(
            "bws", help="Bitwarden Secrets CLI export options"
        )
        secBwsExport.add_argument(
            "-i",
            "--project-id",
            help="The Bitwarden project ID where to export the key.",
        )

        return secBwsExport

    @staticmethod
    def register_import_subcommands(
        subparser: argparse._SubParsersAction,
    ) -> argparse.ArgumentParser:
        secBwsImport = subparser.add_parser(
            "bws", help="Bitwarden Secrets CLI import options"
        )
        return secBwsImport

    def export_secrets(self, payload: SecretsExportPayload) -> ResultPayload:
        import json
        import subprocess

        self.check_status()

        messages = []
        errors = []
        try:
            provider_args = cast(
                BitwardenSecretsExportArgs, payload.provider_specific_args
            )

            keyType = payload.key_type
            key = payload.item_name
            save_to_config = payload.save_to_config

            config = self.config

            project_id = (
                config.get("secret_providers", {}).get("bws", {}).get("project_id", "")
            )

            if provider_args.project_id:
                project_id = provider_args.project_id

            if not keyType:
                raise ValueError("Key type must be specified for export.")
            if not project_id:
                raise ValueError("Project ID must be specified for export.")
            if not key:
                raise ValueError("Item name must be specified for export.")

            from chaos.lib.secret_backends.key_backends.factory import get_key_backend

            try:
                key_backend = get_key_backend(keyType)
                key_content, prep_msgs = key_backend.prepare_export_content(payload)
                messages.extend(prep_msgs)
            except ValueError as e:
                raise ValueError(f"Unsupported key type or error loading backend: {e}")
            except ImportError as e:
                raise ImportError(
                    f"Error importing key backend for type '{keyType}': {e}"
                ) from e

            cmd = [
                "xargs",
                "-I",
                "{}",
                "bws",
                "secret",
                "create",
                key,
                "{}",
                project_id,
            ]
            try:
                result = subprocess.run(
                    cmd, capture_output=True, text=True, check=True, input=key_content
                )
                created_item = json.loads(result.stdout)
                item_id = created_item.get("id")
                messages.append(
                    f"Successfully exported {keyType} key '{key}' to Bitwarden with id {item_id}"
                )

                if save_to_config and item_id:
                    data_to_save = {f"{keyType}_id": item_id, "project_id": project_id}
                    from chaos.lib.secret_backends.utils import _save_to_config

                    _save_to_config(backend="bws", data_to_save=data_to_save)

            except subprocess.CalledProcessError as e:
                raise RuntimeError(
                    f"Error exporting key to Bitwarden: {e.stderr.strip()}"
                ) from e

        except Exception as e:
            errors.append(str(e))
            return ResultPayload(success=False, error=errors, message=messages)

        return ResultPayload(success=True, message=messages)

    def check_status(self):
        from chaos.lib.utils import checkDep

        if not checkDep("bws"):
            raise EnvironmentError(
                "The Bitwarden Secrets CLI ('bws') is required but not found in PATH."
            )
        if not os.getenv("BWS_ACCESS_TOKEN"):
            raise PermissionError(
                "BWS_ACCESS_TOKEN environment variable is not set. Please authenticate."
            )
        return True, "Bitwarden Secrets CLI is ready."

    def readKeys(self, item_id: str) -> str:
        import subprocess

        from omegaconf import DictConfig, OmegaConf

        try:
            result = subprocess.run(
                ["bws", "secret", "get", item_id],
                capture_output=True,
                text=True,
                check=True,
            )
            key_content = result.stdout.strip()
            key_content_conf = OmegaConf.create(key_content)
            key_content = cast(str, cast(DictConfig, key_content_conf).get("value"))
            return key_content
        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"Error retrieving keys from Bitwarden: {e.stderr.strip()}"
            ) from e

    def get_ephemeral_key_args(self) -> tuple[str, str] | None:
        from chaos.lib.args.dataclasses import SecretsContext

        if isinstance(self.payload, SecretsContext) and self.payload.provider_config:
            return self.payload.provider_config.ephemeral_provider_args.get("from_bws")
        return None


class BitwardenRbwProvider(Provider):
    @classmethod
    def build_export_args(cls, **kwargs) -> ProviderExportArgs:
        return ProviderExportArgs()

    @classmethod
    def build_import_args(cls, **kwargs) -> ProviderImportArgs:
        return ProviderImportArgs()

    @staticmethod
    def get_import_arg_names():
        return []

    @staticmethod
    def get_export_arg_names():
        return []

    @staticmethod
    def get_cli_name() -> tuple[str, str]:
        return "from_rbw", "rbw"

    @staticmethod
    def register_flags(parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--from-rbw",
            "-rb",
            type=str,
            nargs=2,
            metavar=("ITEM_ID", "KEY_TYPE"),
            help="Retrieve ephemeral keys from rbw (Bitwarden CLI). Provide ITEM_ID and KEY_TYPE (age/gpg/vault).",
        )

    @staticmethod
    def register_import_subcommands(
        subparser: argparse._SubParsersAction,
    ) -> argparse.ArgumentParser:
        secRbwImport = subparser.add_parser(
            "rbw", help="rbw (Bitwarden CLI) import options"
        )
        return secRbwImport

    @staticmethod
    def register_export_subcommands(
        subparser: argparse._SubParsersAction,
    ) -> argparse.ArgumentParser:
        secRbwExport = subparser.add_parser(
            "rbw", help="rbw (Bitwarden CLI) export options"
        )
        return secRbwExport

    def export_secrets(self, payload: SecretsExportPayload) -> ResultPayload:
        import subprocess

        from ..utils import _save_to_config

        self.check_status()

        messages = []
        errors = []

        try:
            keyType = payload.key_type
            item_name = payload.item_name
            save_to_config = payload.save_to_config

            from chaos.lib.secret_backends.key_backends.factory import get_key_backend

            try:
                key_backend = get_key_backend(keyType)

                key_content, prep_msgs = key_backend.prepare_export_content(payload)
                messages.extend(prep_msgs)

            except ValueError as e:
                raise ValueError(f"Unsupported key type or error loading backend: {e}")
            except ImportError as e:
                raise ImportError(
                    f"Error importing key backend for type '{keyType}': {e}"
                ) from e

            if not key_content:
                raise ValueError("No key content to export.")

            if not item_name:
                raise ValueError("No item name provided for export.")

            processed_key_content = "\n".join(
                f" {line}" if line.startswith("#") else line
                for line in key_content.splitlines()
            )

            credential_content = f"ch-aos\n{processed_key_content}"

            subprocess.run(
                ["rbw", "add", f"Ch-aOS {keyType.upper()} Key: {item_name}", "ch-aos"],
                check=True,
                input=credential_content,
                text=True,
                capture_output=True,
            )

            item_id = self._get_item_id(f"Ch-aOS {keyType.upper()} Key: {item_name}")
            messages.append(
                f"Successfully exported {keyType} key to Bitwarden item (ID: {item_id})."
            )
            if item_id and save_to_config:
                messages.append(
                    f"Saving Bitwarden item ID '{item_id}' to chaos config."
                )
                data_to_save = {f"{keyType}_id": item_id}
                _save_to_config(backend="rbw", data_to_save=data_to_save)

        except Exception as e:
            errors.append(str(e))
            return ResultPayload(success=False, error=errors, message=messages)

        return ResultPayload(success=True, message=messages)

    def check_status(self) -> tuple[bool, str]:
        import subprocess

        from chaos.lib.utils import checkDep

        if not checkDep("rbw"):
            raise EnvironmentError(
                "The 'rbw' CLI tool is required but not found in PATH."
            )

        try:
            result = subprocess.run(
                ["rbw", "unlocked"], capture_output=True, text=True, check=True
            )
            status_info = result.stdout.strip()
            if not status_info:
                return True, "rbw is unlocked."
            return True, "rbw is unlocked."
        except subprocess.CalledProcessError:
            return (
                False,
                "rbw is locked. Please unlock it with 'rbw unlock' or 'rbw login' first.\n    Note: for official Bitwarden users, 'rbw register' is required before 'rbw login'.\n    It will ask you foro your CLIENT ID and SECRET from your Bitwarden account settings.",
            )

    def readKeys(self, item_id: str) -> str:
        import subprocess

        try:
            result = subprocess.run(
                ["rbw", "get", item_id, "--field=notes"],
                capture_output=True,
                text=True,
                check=True,
            )
            key_content = result.stdout.strip()

            if not key_content:
                raise ValueError(
                    f"No notes found in Bitwarden item with ID '{item_id}'. The key should be in the 'notes' field."
                )

            return key_content
        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"Error reading secret from Bitwarden item '{item_id}': {e.stderr.strip()}"
            ) from e

    def get_ephemeral_key_args(self) -> tuple[str, str] | None:
        from chaos.lib.args.dataclasses import SecretsContext

        if isinstance(self.payload, SecretsContext) and self.payload.provider_config:
            return self.payload.provider_config.ephemeral_provider_args.get("from_rbw")
        return None

    def _get_item_id(self, name: str) -> str:
        import subprocess

        try:
            items_raw = subprocess.Popen(
                ["rbw", "list", "--fields", "id", "--fields", "name"],
                stdout=subprocess.PIPE,
            )

        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"Error retrieving Bitwarden items: {e.stderr.strip()}"
            ) from e

        try:
            items = subprocess.run(
                ["grep", name],
                stdin=items_raw.stdout,
                capture_output=True,
                text=True,
                check=True,
            )

            if not items.stdout.strip():
                raise ValueError(f"No Bitwarden item found with name '{name}'.")
            items = items.stdout.strip().splitlines()
            if len(items) > 1:
                raise ValueError(f"Multiple Bitwarden items found with name '{name}.")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"Error searching for Bitwarden item '{name}': {e.stderr.strip()}"
            ) from e

        id = items[0].split("\t")[0]

        return id
