import os
from .base import SecretBackend
from .ephemeral import ephemeralAgeKey, ephemeralGpgKey, ephemeralVaultKeys
import subprocess
import json
from contextlib import contextmanager
from chaos.lib.utils import checkDep
from chaos.lib.secret_backends.utils import extract_age_keys, get_sops_files

class BitwardenPasswordBackend(SecretBackend):
    def _check_bw_status(self):
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

    """Retrieves age keys from a Bitwarden item by its ID."""
    def getBwAgeKeys(self, item_id: str) -> tuple[str, str, str]:
        key_content = self.bwReadKey(item_id)
        if not key_content: raise ValueError("Retrieved key from Bitwarden is empty.")

        pubKey, secKey = extract_age_keys(key_content)

        if not pubKey:
            raise ValueError("Could not find a public key in the secret from Bitwarden. Expected a line starting with '# public key:'.")
        if not secKey:
            raise ValueError("Could not find a secret key in the secret from Bitwarden. Expected a line starting with 'AGE-SECRET-KEY-'.")

        return pubKey, secKey, key_content

    """Retrieves Vault keys from a Bitwarden item by its ID."""
    def getBwVaultKeys(self, item_id: str) -> tuple[str, str]:
        key_content = self.bwReadKey(item_id)

        vault_addr, vault_token = None, None
        for line in key_content.splitlines():
            if line.startswith("# Vault Address:"):
                vault_addr = line.split("::", 1)[1].strip()
            if line.startswith("Vault Key:"):
                vault_token = line.split(":", 1)[1].strip()

        if not vault_addr or not vault_token:
            raise ValueError("Could not extract both Vault address and token from Bitwarden item.")

        return vault_addr, vault_token

    """Retrieves GPG keys from a Bitwarden item by its ID."""
    def getBwGpgKeys(self, item_id: str) -> tuple[str, str]:
        key_content = self.bwReadKey(item_id)
        if not key_content:
            raise ValueError("Retrieved GPG key from Bitwarden is empty.")

        fingerprints = ""
        for line in key_content.splitlines():
            if line.startswith("# fingerprints:"):
                fingerprints = line.split(":", 1)[1].strip()
                break

        if "-----BEGIN PGP PRIVATE KEY BLOCK-----" not in key_content:
            raise ValueError("The secret read from Bitwarden does not appear to be a GPG private key block.")

        noHeadersSecKey = key_content.split('-----BEGIN PGP PRIVATE KEY BLOCK-----', 1)[1].rsplit('-----END PGP PRIVATE KEY BLOCK-----', 1)[0]
        secKey = noHeadersSecKey.strip()

        return fingerprints, secKey

    """Reads the secret key content from a Bitwarden item by its ID."""
    def bwReadKey(self, item_id: str) -> str:
        self._check_bw_status()
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

    @contextmanager
    def setupEphemeralEnv(self):
        item_id, key_type = self.args.from_bw

        context = {
            "env": os.environ.copy(),
            "prefix": "",
            "pass_fds": []
        }

        match key_type:
            case 'age':
                _, _, key_content = self.getBwAgeKeys(item_id)
                with ephemeralAgeKey(key_content) as age_env:
                    context["env"].update(age_env)
                    yield context
            case 'gpg':
                from chaos.lib.secret_backends.utils import decompress
                _, secKey = self.getBwGpgKeys(item_id)
                secKey = decompress(secKey)
                with ephemeralGpgKey(secKey) as gpg_env:
                    context["env"].update(gpg_env)
                    yield context
            case 'vault':
                vault_addr, vault_token = self.getBwVaultKeys(item_id)
                with ephemeralVaultKeys(vault_token, vault_addr) as (prefix, fds):
                    context["prefix"] = prefix
                    context["pass_fds"] = fds
                    yield context
            case _:
                raise ValueError(f"Unsupported key type '{key_type}'.")

    def export_secrets(self) -> None:
        """
        Exports keys to Bitwarden as new notes.
        """
        from pathlib import Path
        from chaos.lib.secret_backends.utils import extract_gpg_keys, setup_vault_keys, _save_to_config
        from rich.console import Console

        console = Console()

        self._check_bw_status()

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

            item_json["type"] = 2
            item_json["name"] = item_name
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
            item_json["secureNote"] = {"type": 0}

            encoded_item = subprocess.run(
                ['bw', 'encode'],
                input=json.dumps(item_json),
                capture_output=True, text=True, check=True
            ).stdout.strip()

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

    def import_secrets(self) -> None:
        """
        Imports keys from Bitwarden into the local environment.
        """
        from chaos.lib.secret_backends.utils import _import_age_keys, _import_gpg_keys, _import_vault_keys
        from rich.console import Console

        console = Console()

        self._check_bw_status()

        keyType = self.args.key_type
        item_id = self.args.item_id

        if not keyType:
            raise ValueError("Key type must be specified for import.")
        if not item_id:
            raise ValueError("Item ID must be specified for import.")

        match keyType:
            case 'age':
                pubKey, secKey, key_content = self.getBwAgeKeys(item_id)
                console.print(f"[green]Successfully imported age key from Bitwarden.[/green]")
                console.print(f"Public Key: [bold]{pubKey}[/bold]")
                console.print(f"Secret Key: [bold]{secKey}[/bold]")
                _import_age_keys(key_content)

            case 'gpg':
                fingerprints, secKey = self.getBwGpgKeys(item_id)
                console.print(f"[green]Successfully imported GPG key from Bitwarden.[/green]")
                console.print(f"Fingerprints: [bold]{fingerprints}[/bold]")
                _import_gpg_keys(secKey)

            case 'vault':
                vault_addr, vault_token = self.getBwVaultKeys(item_id)
                console.print(f"[green]Successfully imported Vault key from Bitwarden.[/green]")
                console.print(f"Vault Address: [bold]{vault_addr}[/bold]")
                console.print(f"Vault Token: [bold]{vault_token}[/bold]")
                key_content = f"# Vault Address:: {vault_addr}\nVault Key: {vault_token}\n"
                _import_vault_keys(key_content)

            case _:
                raise ValueError(f"Unsupported key type: {keyType}")
