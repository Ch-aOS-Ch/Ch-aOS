import os
import base64
from .base import Provider
import subprocess
import json
from pathlib import Path
from rich.console import Console
from chaos.lib.utils import checkDep
from chaos.lib.secret_backends.utils import (
    extract_age_keys,
    _save_to_config,
    extract_gpg_keys,
    setup_vault_keys,
    get_sops_files,
    is_valid_age_key,
    is_valid_age_secret_key,
)
from omegaconf import OmegaConf, DictConfig
from typing import cast

console = Console()

class BitwardenPasswordProvider(Provider):
    def export_secrets(self) -> None:
        """
        Exports keys to Bitwarden as new notes.
        """

        self.check_status()

        keyType = self.args.key_type
        keyPath = self.args.keys
        item_name = self.args.item_name
        fingerprints = self.args.fingerprints
        tags = self.args.bw_tags
        save_to_config = self.args.save_to_config

        collection_id = self.config.get('secret_providers', {}).get('bw', {}).get('collection_id', '')
        organization_id = self.config.get('secret_providers', {}).get('bw', {}).get('organization_id', '')

        if self.args.collection_id:
            collection_id = self.args.collection_id
        if self.args.organization_id:
            organization_id = self.args.organization_id

        key_content = ""
        if keyType == 'age':
            if not keyPath: raise ValueError("No age key path passed via --keys.")
            keyPath = Path(keyPath).expanduser()
            if not keyPath.is_file(): raise FileNotFoundError(f"Path {keyPath} is not a file.")

            with open(keyPath, 'r') as f:
                key_content = f.read()

            pubkey, seckey = extract_age_keys(key_content)

            if not pubkey:
                raise ValueError("Could not find a public key in the provided age key file. Expected a line starting with '# public key:'.")
            if not seckey:
                raise ValueError("Could not find a secret key in the provided age key file. Expected a line starting with 'AGE-SECRET-KEY-'.")

            console.print(f"[green]INFO:[/] Exporting age public key: {pubkey}")

        elif keyType == 'gpg':
            if not fingerprints: raise ValueError("At least one GPG fingerprint is required via --fingerprints.")
            if not checkDep("gpg"): raise EnvironmentError("The 'gpg' CLI tool is required but not found in PATH.")

            key_content = extract_gpg_keys(fingerprints)

        elif keyType == 'vault':
            vaultAddr = self.args.vault_addr
            if not keyPath: raise ValueError("No Vault key path passed via --keys.")
            if not vaultAddr: raise ValueError("No Vault address passed via --vault-addr.")

            keyPath = Path(keyPath).expanduser()
            if not keyPath.is_file(): raise FileNotFoundError(f"Path {keyPath} is not a file.")

            key_content = setup_vault_keys(vaultAddr, keyPath)

        else:
            raise ValueError(f"Unsupported key type: {keyType}")

        try:
            template_str = subprocess.run(
                ['bw', 'get', 'template', 'item'],
                capture_output=True, text=True, check=True
            ).stdout
            item_json = json.loads(template_str)

            item_json["type"] = 1
            item_json["login"] = {"username": "ch-aos", "password": "ch-aos"}
            item_json["name"] = f"Ch-aOS {keyType.upper()} Key: {item_name}"
            item_json["notes"] = key_content
            if collection_id:
                if not organization_id:
                    raise ValueError("When specifying a collection ID, an organization ID must also be provided.")
                item_json["collectionIds"] = [collection_id]
            if organization_id:
                item_json["organizationId"] = organization_id
            if tags:
                item_json['fields'] = [tags]
            item_json["favorite"] = False

            item_str = json.dumps(item_json)
            encoded_item = base64.b64encode(item_str.encode()).decode()

            created_item_json = subprocess.run(
                ['bw', 'create', 'item', encoded_item],
                 capture_output=True, text=True, check=True
            ).stdout.strip()

            created_item = json.loads(created_item_json)
            item_id = created_item.get("id")

            console.print(f"[bold green]Success![/] Successfully exported {keyType} key to Bitwarden item '{created_item['name']}' (ID: {created_item['id']}).")

            if save_to_config and item_id:
                _save_to_config(item_id=item_id, collection_id=collection_id, organization_id=organization_id, backend='bw', keyType=keyType)

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Error creating item in Bitwarden: {e.stderr.strip()}") from e
        except (json.JSONDecodeError, KeyError) as e:
            raise RuntimeError(f"Failed to parse Bitwarden output: {e}") from e

    def check_status(self):
        if not checkDep("bw"):
            raise EnvironmentError("The 'bw' CLI tool is required but not found in PATH.")

        try:
            status_result = subprocess.run(['bw', 'status'], capture_output=True, text=True, check=True)
            status = json.loads(status_result.stdout)

            if status['status'] == 'unlocked':
                return True, "Bitwarden vault is unlocked."

            elif status['status'] == 'locked':
                raise PermissionError("Bitwarden vault is locked. Please unlock it first with 'bw unlock'.")

            else: # "unauthenticated"
                raise PermissionError("You are not logged into Bitwarden. Please log in first with 'bw login'.")

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to check Bitwarden status: {e.stderr.strip()}") from e
        except (json.JSONDecodeError, KeyError) as e:
            raise RuntimeError(f"Failed to parse Bitwarden status: {e}")

    def readKeys(self, item_id: str) -> str:
        self.check_status()
        try:
            result = subprocess.run(
                ["bw", "get", "notes", item_id],
                capture_output=True,
                text=True,
                check=True
            )
            if not result.stdout.strip():
                raise ValueError(f"No notes found in Bitwarden item with ID '{item_id}'. The key should be in the 'notes' field.")
            return result.stdout.strip()

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Error reading secret from Bitwarden item '{item_id}': {e.stderr.strip()}") from e

    def get_ephemeral_key_args(self) -> tuple[str, str] | None:
        return self.args.from_bw

class BitwardenSecretsProvider(Provider):
    def export_secrets(self) -> None:
        args = self.args
        self.check_status()

        keyType = args.key_type
        key = args.item_name
        fingerprints = args.fingerprints
        save_to_config = args.save_to_config

        _,_, config = get_sops_files(None, None, None)

        project_id = config.get('secret_providers', {}).get('bws', {}).get('project_id', '')

        if args.project_id:
            project_id = args.project_id

        if not keyType:
            raise ValueError("Key type must be specified for export.")
        if not project_id:
            raise ValueError("Project ID must be specified for export.")
        if not key:
            raise ValueError("Item name must be specified for export.")

        match keyType:
            case 'age':
                if not args.keys: raise ValueError("No age key path passed via --keys.")
                keyPath = Path(args.keys)

                self._exportBwsAgeKey(keyPath, key, project_id, save_to_config)

            case 'gpg':
                if not fingerprints: raise ValueError("At least one GPG fingerprint is required via --fingerprints.")
                if not checkDep("gpg"): raise EnvironmentError("The 'gpg' CLI tool is required but not found in PATH.")

                self._exportBwsGpgKey(key, project_id, fingerprints, save_to_config)

            case 'vault':
                vaultAddr = args.vault_addr
                keyPath = Path(args.keys)
                if not keyPath: raise ValueError("No Vault key path passed via --keys.")
                if not vaultAddr: raise ValueError("No Vault address passed via --vault-addr.")

                self._exportBwsVaultKey(keyPath, vaultAddr, key, project_id, save_to_config)
            case _:
                raise ValueError(f"Unsupported key type: {keyType}")

    def check_status(self):
        if not checkDep("bws"):
            raise EnvironmentError("The Bitwarden Secrets CLI ('bws') is required but not found in PATH.")
        if not os.getenv("BWS_ACCESS_TOKEN"):
            raise PermissionError("BWS_ACCESS_TOKEN environment variable is not set. Please authenticate.")
        return True, "Bitwarden Secrets CLI is ready."

    def readKeys(self, item_id: str) -> str:
        try:
            result = subprocess.run(
                ['bws', 'secret', 'get', item_id],
                capture_output=True,
                text=True,
                check=True
            )
            key_content = result.stdout.strip()
            key_content_conf = OmegaConf.create(key_content)
            key_content = cast(str, cast(DictConfig, key_content_conf).get('value'))
            return key_content
        except subprocess.CalledProcessError as e:
                raise RuntimeError(f"Error retrieving keys from Bitwarden: {e.stderr.strip()}") from e

    def get_ephemeral_key_args(self) -> tuple[str, str] | None:
        return self.args.from_bws

    def _get_age_key_content(self, key_path: Path) -> str:
        with key_path.open('r') as f:
            content = f.read()
        if '# public' not in content or 'AGE-SECRET-KEY-' not in content:
            raise ValueError("The specified key file does not appear to be a valid age key.")
        return content

    def _exportBwsVaultKey(self, keyPath: Path, vaultAddr: str, key: str, project_id: str, save_to_config: bool) -> None:
        key_content = setup_vault_keys(vaultAddr, keyPath)
        cmd = ['bws', 'secret', 'create', key, key_content, project_id]
        console.print(f"[cyan]INFO:[/] Exporting Vault key from {keyPath}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            created_item = json.loads(result.stdout)
            item_id = created_item.get("id")
            console.print(f"[green]Successfully exported Vault key '{key}' to Bitwarden with id {item_id}[/green]")

            if save_to_config and item_id:
                from chaos.lib.secret_backends.utils import _save_to_config
                _save_to_config(item_id=item_id, project_id=project_id, backend='bws', keyType='vault')

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Error exporting GPG key to Bitwarden: {e.stderr.strip()}") from e
        except FileNotFoundError:
            raise RuntimeError("Bitwarden Secrets CLI ('bws') is not installed or not found in PATH.") from None
        except Exception as e:
            raise RuntimeError(f"Unexpected error exporting GPG key to Bitwarden: {str(e)}") from e

    def _exportBwsGpgKey(self, key: str, project_id: str, fingerprints: list[str], save_to_config: bool) -> None:
        key_content = extract_gpg_keys(fingerprints)

        cmd = ['bws', 'secret', 'create', key, key_content, project_id]
        console.print(f"[cyan]INFO:[/] Exporting GPG key for fingerprints: {', '.join(fingerprints)}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            created_item = json.loads(result.stdout)
            item_id = created_item.get("id")
            console.print(f"[green]Successfully exported GPG key '{key}' to Bitwarden with id {item_id}[/green]")

            if save_to_config and item_id:
                from chaos.lib.secret_backends.utils import _save_to_config
                _save_to_config(item_id=item_id, project_id=project_id, backend='bws', keyType='gpg')

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Error exporting GPG key to Bitwarden: {e.stderr.strip()}") from e
        except FileNotFoundError:
            raise RuntimeError("Bitwarden Secrets CLI ('bws') is not installed or not found in PATH.") from None
        except Exception as e:
            raise RuntimeError(f"Unexpected error exporting GPG key to Bitwarden: {str(e)}") from e

    def _exportBwsAgeKey(self, key_path: Path, key: str, project_id: str, save_to_config: bool) -> None:
        value = self._get_age_key_content(key_path)
        pubKey, secKey = extract_age_keys(value)

        if not pubKey or not secKey: raise ValueError("Could not extract both public and secret keys from the provided age key file.")
        if not is_valid_age_key(pubKey): raise ValueError("The extracted public key from the age key file is not valid.")
        if not is_valid_age_secret_key(secKey): raise ValueError("The extracted secret key from the age key file is not valid.")

        cmd = ['bws', 'secret', 'create', key, value, project_id]

        console.print(f"[cyan]INFO:[/] Exporting age public key: {pubKey}")
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            created_item = json.loads(result.stdout)
            item_id = created_item.get("id")

            console.print(f"[green]Successfully exported age key '{key}' to Bitwarden with id {item_id}[/green]")

            if save_to_config and item_id:
                from chaos.lib.secret_backends.utils import _save_to_config
                _save_to_config(item_id=item_id, project_id=project_id, backend='bws', keyType='age')

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Error exporting age key to Bitwarden: {e.stderr.strip()}") from e
        except FileNotFoundError:
            raise RuntimeError("Bitwarden Secrets CLI ('bws') is not installed or not found in PATH.") from None
        except Exception as e:
            raise RuntimeError(f"Unexpected error exporting age key to Bitwarden: {str(e)}") from e

