"""Cryptographic utilities for key validation, extraction, and ephemeral environment setup."""

import base64
import re
import subprocess
import zlib
from pathlib import Path

from chaos.lib.args.dataclasses import ResultPayload


def compress(data: bytes) -> str:
    """Compresses data to base85-encoded zlib representation.

    This is primarily used for GPG keys so they can fit inside a Bitwarden note.

    Args:
        data (bytes): The raw bytes data to compress.

    Returns:
        str: The base85-encoded, zlib-compressed string representation of the data.

    Raises:
        RuntimeError: If data compression or encoding fails.
    """
    try:
        compressed_data = zlib.compress(data, level=9)
        encoded_data = base64.b85encode(compressed_data).decode("utf-8")
    except Exception as e:
        raise RuntimeError(f"Failed to compress and encode data: {e}") from e
    return encoded_data


def decompress(encoded_data: str) -> bytes:
    """Decompresses base85-encoded zlib data back to bytes.

    Args:
        encoded_data (str): The base85-encoded, compressed string.

    Returns:
        bytes: The decompressed original raw bytes data.

    Raises:
        RuntimeError: If data decoding or decompression fails.
    """

    try:
        compressed_data = base64.b85decode(encoded_data.encode("utf-8"))
        data = zlib.decompress(compressed_data)
        return data
    except Exception as e:
        raise RuntimeError(f"Failed to decode and decompress data: {e}") from e


def is_valid_fp(fingerprint: str) -> bool:
    """Checks for GPG fingerprint validity.

    Validates if the provided string is a valid 40-character hexadecimal GPG fingerprint.

    Args:
        fp (str): The fingerprint string to validate.

    Returns:
        bool: True if it is a valid GPG fingerprint, False otherwise.
    """

    clean_fingerprint = fingerprint.replace(" ", "").replace("\n", "")
    return re.fullmatch(r"[0-9A-Fa-f]{40}$", clean_fingerprint) is not None


def pgp_exists(fingerprint: str) -> bool:
    """Checks if a GPG fingerprint exists in the local keyring.

    Args:
        fp (str): The GPG fingerprint to check.

    Returns:
        bool: True if the key exists locally, False otherwise.
    """
    try:
        subprocess.run(
            ["gpg", "--list-keys", fingerprint],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except subprocess.CalledProcessError:
        return False


def is_valid_age_key(pubKey: str) -> bool:
    """Validates a public age key.

    Args:
        pubKey (str): The public age key string to validate.

    Returns:
        bool: True if the key matches the age public key format, False otherwise.
    """
    return re.fullmatch(r"age1[a-z0-9]{58}", pubKey) is not None


def is_valid_age_secret_key(secKey: str) -> bool:
    """Validates a private (secret) age key.

    Args:
        secKey (str): The secret age key string to validate.

    Returns:
        bool: True if the key matches the age secret key format, False otherwise.
    """
    return re.fullmatch(r"AGE-SECRET-KEY-1[A-Za-z0-9]{58}", secKey) is not None


def extract_age_keys(key_content: str) -> tuple[str | None, str | None]:
    """Extracts age public and private keys from a text block.

    Args:
        key_content (str): The multiline string content containing the age keys.

    Returns:
        tuple[str | None, str | None]: A tuple containing the public key and secret key, respectively.
    """
    pubKey, secKey = None, None
    for line in key_content.splitlines():
        line = line.strip()
        if line.startswith("# public key:"):
            pubKey = line.split(":", 1)[1].strip()
        if line.startswith("AGE-SECRET-KEY-"):
            secKey = line
    return pubKey, secKey


def extract_gpg_keys(fingerprints: list[str]) -> str:
    """Extracts and encodes GPG secret keys for export.

    Exports the secret keys for the given fingerprints, compresses them using zlib,
    and encodes them into a custom ASCII-armored block.

    Args:
        fingerprints (list[str]): A list of GPG fingerprints to export.

    Returns:
        str: The compressed and encoded secret key block.

    Raises:
        RuntimeError: If the GPG export operation fails or no keys are found.
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


def _import_age_keys(key_content: str, confirmed: bool = False) -> ResultPayload[None]:
    currentPathAgeFile = Path.cwd() / "keys.txt"
    messages = []
    errors = []

    if currentPathAgeFile.exists() and not confirmed:
        return ResultPayload(
            success=False,
            message=["A 'keys.txt' file already exists in the current directory."],
            error=["Confirmation needed to overwrite 'keys.txt'."],
        )

    try:
        with currentPathAgeFile.open("w") as f:
            sanitized_content = "\n".join(
                line.lstrip() for line in key_content.splitlines()
            )
            f.write(sanitized_content)
            if not sanitized_content.endswith("\n"):
                f.write("\n")
        messages.append("Age key imported successfully to 'keys.txt'.")
    except Exception as e:
        errors.append(f"Error importing age key: {str(e)}")
        return ResultPayload(success=False, error=errors)

    return ResultPayload(success=True, message=messages)


def _import_gpg_keys(secKey: str) -> ResultPayload[None]:
    decompressedKey = decompress(secKey)
    messages = []
    errors = []

    try:
        import_cmd = ["gpg", "--batch", "--import"]
        subprocess.run(
            import_cmd,
            input=decompressedKey,
            check=True,
            capture_output=True,
        )
        messages.append("GPG key imported into your local GPG keyring successfully.")
    except subprocess.CalledProcessError as e:
        errors.append(f"Error importing GPG key: {e.stderr.decode().strip()}")
        return ResultPayload(success=False, error=errors)

    return ResultPayload(success=True, message=messages)


def _import_vault_keys(key_content: str) -> ResultPayload[None]:
    currentPathVaultFile = Path.cwd() / "vault_key.txt"
    messages = []
    errors = []

    try:
        with currentPathVaultFile.open("w") as f:
            f.write(key_content)
        messages.append("Vault key imported successfully to 'vault_key.txt'.")
    except Exception as e:
        errors.append(f"Error importing Vault key: {str(e)}")
        return ResultPayload(success=False, error=errors)

    return ResultPayload(success=True, message=messages)


def is_vault_in_use(sops_file_path: str) -> bool:
    """Checks if HashiCorp Vault is configured in the given SOPS file.

    Args:
        sops_file_path (str): The file path to the SOPS configuration file.

    Returns:
        bool: True if a Vault key group is found in the configuration, False otherwise.
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


def check_vault_auth() -> tuple[bool, str]:
    """Checks if the current HashiCorp Vault authentication is valid.

    Verifies the presence and validity of the VAULT_ADDR and VAULT_TOKEN environment variables.

    Returns:
        tuple[bool, str]: A tuple where the first element is a boolean indicating whether
            authentication is valid, and the second element is an accompanying message.
    """
    import os

    import requests

    vault_addr = os.getenv("VAULT_ADDR")
    if not vault_addr:
        return (
            False,
            "VAULT_ADDR environment variable is not set, which is required when using Vault keys.",
        )

    vault_token = os.getenv("VAULT_TOKEN")
    if not vault_token:
        return (
            False,
            "VAULT_TOKEN environment variable is not set. Please log in to Vault.",
        )

    try:
        headers = {"X-Vault-Token": vault_token}
        check_url = f"{vault_addr}/v1/auth/token/lookup-self"

        response = requests.get(check_url, headers=headers, timeout=5)
        response.raise_for_status()
        if response.status_code == 200:
            return True, "Vault token is valid."
        elif response.status_code == 403:
            return (
                False,
                "Vault token is invalid or expired. Please log in to Vault.",
            )
        else:
            return (
                False,
                f"Unexpected response from Vault: {response.status_code}",
            )

    except requests.exceptions.RequestException as e:
        return (
            False,
            f"Failed to connect to Vault at {vault_addr}: {e}",
        )
    except ImportError:
        return (
            False,
            "The 'hvac' library is not installed. Please install it to use Vault features (pip install hvac).",
        )
    except Exception as e:
        return (
            False,
            f"Failed to authenticate with Vault at {vault_addr}: {e}",
        )
