from chaos.lib.secret_backends.utils import _check_bws_status, exctract_gpg_keys, is_valid_age_secret_key, is_valid_vault_key, is_valid_age_key, is_valid_fp, extract_age_keys
from chaos.lib.utils import checkDep
from rich.console import Console
from pathlib import Path
import subprocess
import json
import os

console = Console()

def _get_age_key_content(key_path: Path) -> str:
    with key_path.open('r') as f:
        content = f.read()
    if '# public' not in content or 'AGE-SECRET-KEY-' not in content:
        raise ValueError("The specified key file does not appear to be a valid age key.")
    return content

def exportBwsAgeKey(key_path: Path, key: str, project_id: str) -> None:
    value = _get_age_key_content(key_path)
    pubKey, secKey = extract_age_keys(value)

    if not pubKey or not secKey: raise ValueError("Could not extract both public and secret keys from the provided age key file.")
    if not is_valid_age_key(pubKey): raise ValueError("The extracted public key from the age key file is not valid.")
    if not is_valid_age_secret_key(secKey): raise ValueError("The extracted secret key from the age key file is not valid.")

    cmd = ['bws secret create', key, value, project_id]

    console.print(f"[green]INFO:[/] Exporting age public key: {pubKey}")
    try:
        subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        console.print(f"[green]Successfully exported age key '{key}' to Bitwarden.[/green]")

    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Error exporting age key to Bitwarden: {e.stderr.strip()}") from e
    except FileNotFoundError:
        raise RuntimeError("Bitwarden Secrets CLI ('bws') is not installed or not found in PATH.") from None
    except Exception as e:
        raise RuntimeError(f"Unexpected error exporting age key to Bitwarden: {str(e)}") from e

def exportBwsGpgKey(key: str, project_id: str, fingerprint: str) -> None:
    key_content = exctract_gpg_keys(fingerprint)

    cmd = ['bws secret create', key, key_content, project_id]
    console.print(f"[green]INFO:[/] Exporting GPG key for fingerprint: {fingerprint}")

    try:
        subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        console.print(f"[green]Successfully exported GPG key '{key}' to Bitwarden.[/green]")

    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Error exporting GPG key to Bitwarden: {e.stderr.strip()}") from e
    except FileNotFoundError:
        raise RuntimeError("Bitwarden Secrets CLI ('bws') is not installed or not found in PATH.") from None
    except Exception as e:
        raise RuntimeError(f"Unexpected error exporting GPG key to Bitwarden: {str(e)}") from e

def bwsExportKeys(args) -> None:
    _check_bws_status()

    keyType = args.key_type
    project_id = args.project_id
    key = args.item_name
    fingerprint = args.fingerprint

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

            exportBwsAgeKey(keyPath, key, project_id)

        case 'gpg':
            if not fingerprint: raise ValueError("A GPG fingerprint is required via --fingerprint.")
            if not checkDep("gpg"): raise EnvironmentError("The 'gpg' CLI tool is required but not found in PATH.")
            if not is_valid_fp(fingerprint): raise ValueError("The provided GPG fingerprint is not valid.")

            exportBwsGpgKey(key, project_id, fingerprint)
            
        case _:
            raise ValueError(f"Unsupported key type: {keyType}")
