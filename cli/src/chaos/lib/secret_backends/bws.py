from typing import cast
from chaos.lib.secret_backends.utils import _check_bws_status, exctract_gpg_keys, is_valid_vault_key, is_valid_age_key, is_valid_fp, extract_age_keys
from chaos.lib.secret_backends.utils import get_sops_files
from omegaconf import DictConfig, OmegaConf
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

    cmd = ['bws', 'secret', 'create', key, value, project_id]

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

    cmd = ['bws', 'secret', 'create', key, key_content, project_id]
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

def getBwsAgeKeys(item_id: str) -> tuple[str, str]:
    try:
        result = subprocess.run(
            ['bws', 'secret', 'get', item_id],
            capture_output=True,
            text=True,
            check=True
        )
        key_content = result.stdout.strip()
        key_content = OmegaConf.create(key_content)
        key_content = cast(str, cast(DictConfig, key_content).get('value'))
        pubKey, secKey = extract_age_keys(key_content)

        if not pubKey or not secKey:
            raise ValueError("Could not extract both public and secret keys from Bitwarden item.")

        return pubKey, secKey

    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Error retrieving age keys from Bitwarden: {e.stderr.strip()}") from e

def getBwsGpgKeys(item_id: str) -> tuple[str, str]:
    try:
        result = subprocess.run(
            ['bws', 'secret', 'get', item_id],
            capture_output=True,
            text=True,
            check=True
        )
        key_content = result.stdout.strip()
        key_content = OmegaConf.create(key_content)
        key_content = cast(str, cast(DictConfig, key_content).get('value'))
        fingerprint = None
        for line in key_content.splitlines():
            if line.startswith("# fingerprint:"):
                fingerprint = line.split(":", 1)[1].strip()
                break

        if not fingerprint:
            raise ValueError("Could not extract GPG fingerprint from Bitwarden item.")

        if "-----BEGIN PGP PRIVATE KEY BLOCK-----" not in key_content:
            raise ValueError("The secret read from Bitwarden does not appear to be a GPG private key block.")
        return fingerprint, key_content

    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Error retrieving GPG keys from Bitwarden: {e.stderr.strip()}") from e

def _setup_bws_env(item_id: str, keyType: str) -> dict[str, str]:
    env = os.environ.copy()
    match keyType:
        case 'age':
            _, secKey = getBwsAgeKeys(item_id)
        case 'gpg':
            _, secKey = getBwsGpgKeys(item_id)
        case _:
            raise ValueError(f"Unsupported key type: {keyType}")

    env[f'SOPS_{keyType.upper()}_KEY'] = secKey

    return env

def bwsSopsDec(args) -> subprocess.CompletedProcess[str]:
    item_id, keyType = args.from_bws
    secrets_file_override = args.secrets_file_override
    team = args.team
    sops_file_override = args.sops_file_override

    secretsFile, sopsFile, _ = get_sops_files(sops_file_override, secrets_file_override, team)

    env = _setup_bws_env(item_id, keyType)

    try:
        result = subprocess.run(['sops', '--config', sopsFile, '-d', secretsFile], env=env, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Error decrypting file with sops and Bitwarden: {e.stderr.strip()}") from e

    if not result.stdout.strip():
        raise ValueError(f"No output received from {secretsFile} file.")

    return result

def bwsSopsEdit(args) -> None:
    item_id, keyType = args.from_bws
    secrets_file_override = args.secrets_file_override
    team = args.team
    sops_file_override = args.sops_file_override

    secretsFile, sopsFile, _ = get_sops_files(sops_file_override, secrets_file_override, team)

    env = _setup_bws_env(item_id, keyType)

    try:
        subprocess.run(['sops', '--config', sopsFile, secretsFile], env=env, check=True)
    except subprocess.CalledProcessError as e:
        if e.returncode != 200: # 200 is sops' "no changes" exit code
            raise RuntimeError(f"Error editing file with sops and Bitwarden: {e.stderr.strip()}") from e
