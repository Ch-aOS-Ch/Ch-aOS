import os
from .base import SecretBackend
from .ephemeral import ephemeralAgeKey, ephemeralGpgKey, ephemeralVaultKeys
import subprocess
import json
from contextlib import contextmanager
from chaos.lib.utils import checkDep
from chaos.lib.secret_backends.utils import extract_age_keys

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

    def export_secrets(self):
        self._check_bw_status()
