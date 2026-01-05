import os
from .base import Provider
from .ephemeral import ephemeralAgeKey, ephemeralGpgKey, ephemeralVaultKeys
from .utils import decompress, get_sops_files, setup_vault_keys, extract_gpg_keys, _import_age_keys, _import_gpg_keys, _import_vault_keys
import subprocess
import json
from contextlib import contextmanager
from pathlib import Path
from rich.console import Console
from chaos.lib.utils import checkDep
import re

console = Console()

class OnePasswordProvider(Provider):
    """
    1Password secret backend provider.
    Implements methods to manage secrets using 1Password CLI.
    """

    @contextmanager
    def setupEphemeralEnv(self):
        """
        Set up an ephemeral environment for SOPS using 1Password CLI.
        Yields:
            dict: Context containing environment variables and command prefix.
        """

        item_id, key_type = self.args.from_op

        context = {
            "prefix": "",
            "pass_fds": [],
            "env": os.environ.copy(),
        }

        match key_type:
            case 'age':
                _, _, key_content = self._getOpAgeKeys(item_id)
                with ephemeralAgeKey(key_content) as age_env:
                    context["env"].update(age_env)
                    yield context
            case 'gpg':
                _, secKey = self._getOpGpgKeys(item_id)
                actualKey = decompress(secKey)
                with ephemeralGpgKey(actualKey) as gpg_env:
                    context["env"].update(gpg_env)
                    yield context
            case 'vault':
                vault_addr, vault_token = self._getOpGpgKeys(item_id)
                with ephemeralVaultKeys(vault_token, vault_addr) as (prefix, fds):
                    context["prefix"] = prefix
                    context["pass_fds"] = fds
                    yield context
            case _:
                raise ValueError(f"Unsupported key type '{key_type}'.")

    def export_secrets(self) -> None:
        args = self.args

        keyType = args.key_type
        keyPath = args.keys
        fingerprints = args.fingerprints
        tags = args.op_tags
        save_to_config = args.save_to_config

        _, _, config = get_sops_files(None, None, None)
        path = config.get('secret_providers', {}).get('op', {}).get(f'{keyType}_url', '')

        if args.url:
            path = args.url

        loc = args.op_location

        vault, title, _ = self._reg_match_op_keypath(path)
        if self._op_get_item(vault, title) is not None:
            raise ValueError(f"The item '{title}' already exists in vault '{vault}'")

        if keyType == 'age':
            if not keyPath:
                raise ValueError("No age key path passed via --keys.")

            keyPath = Path(keyPath).expanduser()
            if not keyPath.exists():
                raise FileNotFoundError(f"Path {keyPath} does not exist.")
            if not keyPath.is_file():
                raise ValueError(f"Path {keyPath} is not a file.")

            with open(keyPath, 'r') as f:
                key = f.read()

            if not all([key, path, loc]):
                raise ValueError("Missing required parameters for exporting keys to 1Password.")

            self._op_create_item(vault, title, loc, tags, key)

            pubkey = ""
            for line in key.splitlines():
                if line.startswith("# public key:"):
                    pubkey = line.split("# public key:", 1)[1].strip()
                    break
            if pubkey:
                console.print(f"[green]INFO:[/] Successfully exported {keyType} public key to 1Password: {pubkey}")

        elif keyType == 'gpg':
            if not fingerprints:
                raise ValueError("At least one GPG fingerprint is required. Please provide it with --fingerprints.")

            if not checkDep("gpg"):
                raise EnvironmentError("The 'gpg' CLI tool is required but not found in PATH.")

            key_content = extract_gpg_keys(fingerprints)

            if not all([key_content, path, loc]):
                raise ValueError("Missing required parameters for exporting keys to 1Password.")

            self._op_create_item(vault, title, loc, tags, key_content)

            console.print(f"[green]INFO:[/] Successfully exported GPG keys for to 1Password: '{', '.join(fingerprints)}'")

        elif keyType == 'vault':
            vaultAddr = args.vault_addr
            if not keyPath: raise ValueError("No Vault key path passed via --keys.")
            if not vaultAddr: raise ValueError("No Vault address passed via --vault-addr.")
            keyPath = Path(keyPath).expanduser()

            key_content = setup_vault_keys(vaultAddr, keyPath)

            if not all([key_content, path, loc]):
                raise ValueError("Missing required parameters for exporting keys to 1Password.")

            self._op_create_item(vault, title, loc, tags, key_content)
            console.print(f"[green]INFO:[/] Successfully exported vault token to 1Password.")
        else:
            raise ValueError(f"Unsupported key type: {keyType}")

        if save_to_config:
            from chaos.lib.secret_backends.utils import _save_to_config
            _save_to_config(
                backend='op',
                keyType=keyType,
                item_url=path,
                field=loc
            )

    def import_secrets(self) -> None:
        args = self.args
        keyType = args.key_type
        url = args.url
        loc = args.op_location
        if not keyType:
            raise ValueError("Key type must be specified for import.")
        if not url:
            raise ValueError("Item ID must be specified for import.")

        if keyType == 'age':
            pubKey, secKey, key_content = self._getOpAgeKeys(url)
            console.print(f"[green]Successfully imported age key from Bitwarden.[/green]")
            console.print(f"Public Key: [bold]{pubKey}[/bold]")
            console.print(f"Secret Key: [bold]{secKey}[/bold]")

            _import_age_keys(key_content)

        elif keyType == 'gpg':
            fingerprints, secKey = self._getOpGpgKeys(url)
            console.print(f"[green]Successfully imported GPG key from Bitwarden.[/green]")
            console.print(f"Fingerprints: [bold]{fingerprints}[/bold]")

            _import_gpg_keys(secKey)

        elif keyType == 'vault':
            vault_addr, vault_token = self._getOpVaultKeys(url)
            console.print(f"[green]Successfully imported Vault key from Bitwarden.[/green]")
            console.print(f"Vault Address: [bold]{vault_addr}[/bold]")
            console.print(f"Vault Token: [bold]{vault_token}[/bold]")

            key_content = f"# Vault Address:: {vault_addr}\nVault Key: {vault_token}\n"

            _import_vault_keys(key_content)

        else:
            raise ValueError(f"Unsupported key type: {keyType}")

    def _build_op_keypath(self, key: str, loc: str) -> str:
        match = re.match(r"op://([^/]+)/([^/]+)(?:/([^/]+))?", key)
        if not match:
            raise ValueError(f"Invalid 1Password key format: {key}. Expected format like 'op://vault/item'.")

        vault, item, field_in_key = match.groups()

        if field_in_key:
            if loc and field_in_key != loc:
                raise ValueError(
                    f"Path '{key}' already specifies a field ('{field_in_key}'), "
                    f"which conflicts with the provided location ('{loc}')."
                )
            return key

        if not loc:
            raise ValueError("A field location must be provided when the key path does not contain one.")

        return f"op://{vault}/{item}/{loc}"

    def _opReadKey(self, path: str, loc: str | None = None) -> str:
        if not checkDep("op"):
            raise EnvironmentError("The 'op' CLI tool is required but not found in PATH.")

        if loc:
            path = self._build_op_keypath(path, loc)

        if not path:
            raise ValueError("The provided 1Password path is invalid.")

        try:
            result = subprocess.run(
                ["op", "read", path],
                capture_output=True,
                text=True,
                check=True
            )

            if not result.stdout.strip():
                raise ValueError("No output received from 'op read' command.")
            return result.stdout.strip()

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Error reading secret from 1Password: {e.stderr.strip()}") from e

    """Extracts age keys from a 1Password item."""
    def _getOpAgeKeys(self, path) -> tuple[str, str, str]:
        key_content = self._opReadKey(path)

        if not key_content:
            raise ValueError("Retrieved key from 1Password is empty.")

        pubKey = ""
        secKey = ""

        for line in key_content.splitlines():
            line = line.strip()
            if line.startswith("# public key:"):
                pubKey = line.split(":", 1)[1].strip()
            if line.startswith("AGE-SECRET-KEY-"):
                secKey = line

        if not pubKey:
            raise ValueError("Could not find a public key in the secret from 1Password. Expected a line starting with '# public key:'.")

        if not secKey:
            raise ValueError("Could not find a secret key in the secret from 1Password. Expected a line starting with 'AGE-SECRET-KEY-'.")

        return pubKey, secKey, key_content

    """Extracts GPG keys from a 1Password item."""
    def _getOpGpgKeys(self, path) -> tuple[str, str]:
        key_content = self._opReadKey(path)

        if not key_content:
            raise ValueError("Retrieved GPG key from 1Password is empty.")

        fingerprints = ""
        for line in key_content.splitlines():
            if line.startswith("# fingerprints:"):
                fingerprints = line.split(":", 1)[1].strip()
                break

        if "-----BEGIN PGP PRIVATE KEY BLOCK-----" not in key_content:
            raise ValueError("The secret read from 1Password does not appear to be a GPG private key block.")

        noHeadersSecKey = key_content.split('-----BEGIN PGP PRIVATE KEY BLOCK-----', 1)[1].rsplit('-----END PGP PRIVATE KEY BLOCK-----', 1)[0]
        secKey = noHeadersSecKey.strip()

        return fingerprints, secKey

    """Extracts Vault keys from a 1Password item."""
    def _getOpVaultKeys(self, path: str) -> tuple[str, str]:
        key_content = self._opReadKey(path)

        vault_addr, vault_token = None, None
        for line in key_content.splitlines():
            if line.startswith("# Vault Address:"):
                vault_addr = line.split("::", 1)[1].strip()
            if line.startswith("Vault Key:"):
                vault_token = line.split(":", 1)[1].strip()

        if not vault_addr or not vault_token:
            raise ValueError("Could not extract both Vault address and token from 1Password item.")

        return vault_addr, vault_token

    def _reg_match_op_keypath(self, path: str) -> tuple[str, str, str|None]:
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
                check=True
            )
            item_data = result.stdout.strip()
            if not item_data:
                return None
            return json.loads(item_data)

        except subprocess.CalledProcessError as e:
            if "isn't in vault" in e.stderr or "no item found" in e.stderr:
                return None
            raise RuntimeError(f"Error retrieving item from 1Password: {e.stderr.strip()}") from e

    def _op_create_item(self, vault: str, title: str, field: str, tags: list[str], key: str) -> bool:
        try:
            field_args = []
            for tag in tags:
                field_args.extend(["--tag", tag])

            field_args.extend([f"--field", f"{field}={key}"])
            subprocess.run(
                ["op", "item", "create", "--title", title, "--vault", vault, '--category=password'] + field_args,
                capture_output=True,
                text=True,
                check=True
            )
            console.print(f"[green]INFO:[/] Successfully created item '{title}' in vault '{vault}'.")
            return True
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Error creating item in 1Password: {e.stderr.strip()}") from e
