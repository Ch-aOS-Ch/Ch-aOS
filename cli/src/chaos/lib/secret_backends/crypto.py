import base64
import re
import subprocess
import zlib
from pathlib import Path


def compress(data: bytes) -> str:
    """
    Compression/Decompression for gpg keys. This is the only way they can fit inside a bw notes
    """
    try:
        compressed_data = zlib.compress(data, level=9)
        encoded_data = base64.b85encode(compressed_data).decode("utf-8")
    except Exception as e:
        raise RuntimeError(f"Failed to compress and encode data: {e}") from e
    return encoded_data


def decompress(encoded_data: str) -> bytes:
    import base64
    import zlib

    try:
        compressed_data = base64.b85decode(encoded_data.encode("utf-8"))
        data = zlib.decompress(compressed_data)
        return data
    except Exception as e:
        raise RuntimeError(f"Failed to decode and decompress data: {e}") from e


def is_valid_fp(fp):
    """
    Checks for gpg fingerprint validity
    """
    import re

    clean_fingerprint = fp.replace(" ", "").replace("\n", "")
    if re.fullmatch(r"^[0-9A-Fa-f]{40}$", clean_fingerprint):
        return True
    else:
        return False


def pgp_exists(fp):
    """
    Checks for gpg fp existence
    """
    try:
        subprocess.run(
            ["gpg", "--list-keys", fp],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except subprocess.CalledProcessError:
        return False


def is_valid_age_key(pubKey: str) -> bool:
    """
    Validates public age keys
    """
    isValid = False
    testPub = re.fullmatch(r"age1[a-z0-9]{58}", pubKey)
    if testPub:
        isValid = True
    return isValid


def is_valid_age_secret_key(secKey: str) -> bool:
    """
    Validates private age keys
    """
    isValid = False
    testSec = re.fullmatch(r"AGE-SECRET-KEY-1[A-Za-z0-9]{58}", secKey)
    if testSec:
        isValid = True
    return isValid


def extract_age_keys(key_content: str) -> tuple[str | None, str | None]:
    """
    extracts age private and public keys
    """
    pubKey, secKey = None, None
    for line in key_content.splitlines():
        line = line.strip()
        if line.strip().startswith("# public key:"):
            pubKey = line.split(":", 1)[1].strip()
        if line.strip().startswith("AGE-SECRET-KEY-"):
            secKey = line
    return pubKey, secKey


def extract_gpg_keys(fingerprints: list[str]) -> str:
    """
    Extracts gpg private and public keys (note that chaos exported gpg keys use the chaos compress and decompress methods.)
    """

    try:
        result = subprocess.run(
            ["gpg", "--export-secret-keys"] + fingerprints,
            capture_output=True,
            check=True,
        )
        gpg_key: bytes = result.stdout
        if not gpg_key:
            raise ValueError(
                "No output from 'gpg --export-secret-keys'. Is the fingerprint correct?"
            )
        encoded_gpg: str = compress(gpg_key)
        key_content = f"""# fingerprints: {fingerprints}
-----BEGIN PGP PRIVATE KEY BLOCK-----
{encoded_gpg}
-----END PGP PRIVATE KEY BLOCK-----"""

        return key_content

    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"Failed to export GPG secret key: {e.stderr.strip()}"
        ) from e
    except FileNotFoundError:
        raise RuntimeError(
            "The 'gpg' CLI tool is not installed or not found in PATH."
        ) from None
    except Exception as e:
        raise RuntimeError(f"Unexpected error exporting GPG key: {str(e)}") from e


def _import_age_keys(key_content: str) -> None:
    from rich.console import Console
    from rich.prompt import Confirm

    console = Console()
    currentPathAgeFile = Path.cwd() / "keys.txt"

    if currentPathAgeFile.exists():
        console.print(
            "[yellow]WARNING:[/] A 'keys.txt' file already exists in the current directory. It will be overwritten."
        )
        confirm = Confirm.ask("Do you want to proceed?", default=False)

        if not confirm:
            console.print("Operation cancelled by user.")
            return

    with currentPathAgeFile.open("w") as f:
        sanitized_content = "".join(line.lstrip() for line in key_content.splitlines())
        f.write(sanitized_content)
        if not sanitized_content.endswith(""):
            f.write("")


def _import_gpg_keys(secKey: str) -> None:
    from rich.console import Console

    console = Console()
    decompressedKey = decompress(secKey)

    try:
        import_cmd = ["gpg", "--batch", "--import"]
        subprocess.run(
            import_cmd,
            input=decompressedKey,
            check=True,
            capture_output=True,
        )
        console.print(
            "[green]GPG key imported into your local GPG keyring successfully.[/green]"
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Error importing GPG key: {e.stderr.strip()}") from e


def _import_vault_keys(key_content: str) -> None:
    currentPathVaultFile = Path.cwd() / "vault_key.txt"

    with currentPathVaultFile.open("w") as f:
        f.write(key_content)


def is_vault_in_use(sops_file_path: str) -> bool:
    """
    checks if vault is in use in the sops file
    yeah, just that
    """
    import os
    from typing import cast

    from omegaconf import DictConfig, OmegaConf

    if not sops_file_path or not os.path.exists(sops_file_path):
        return False
    try:
        config = OmegaConf.load(sops_file_path)
        config = cast(DictConfig, config)
        creation_rules = config.get("creation_rules", [])
        for rule in creation_rules:
            for key_group in rule.get("key_groups", []):
                if "vault" in key_group and key_group.get("vault"):
                    return True
    except Exception:
        return False
    return False


def check_vault_auth():
    """checks if vault auth is valid"""
    import os

    import requests

    vault_addr = os.getenv("VAULT_ADDR")
    if not vault_addr:
        return (
            False,
            "[bold red]ERROR:[/] VAULT_ADDR environment variable is not set, which is required when using Vault keys.",
        )

    vault_token = os.getenv("VAULT_TOKEN")
    if not vault_token:
        return (
            False,
            "[bold red]ERROR:[/] VAULT_TOKEN environment variable is not set. Please log in to Vault.",
        )

    try:
        headers = {"X-Vault-Token": vault_token}
        check_url = f"{vault_addr}/v1/auth/token/lookup-self"

        response = requests.get(check_url, headers=headers, timeout=5)
        response.raise_for_status()
        if response.status_code == 200:
            return True, "[green]INFO:[/] Vault token is valid."
        elif response.status_code == 403:
            return (
                False,
                "[bold red]ERROR:[/] Vault token is invalid or expired. Please log in to Vault.",
            )
        else:
            return (
                False,
                f"[]bold red]ERROR:[/] Unexpected response from Vault: {response.status_code}",
            )

    except requests.exceptions.RequestException as e:
        return (
            False,
            f"[bold red]ERROR:[/] Failed to connect to Vault at {vault_addr}: {e}",
        )
    except ImportError:
        return (
            False,
            "[bold red]ERROR:[/] The 'hvac' library is not installed. Please install it to use Vault features (`pip install hvac`).",
        )
    except Exception as e:
        return (
            False,
            f"[bold red]ERROR:[/] Failed to authenticate with Vault at {vault_addr}: {e}",
        )
