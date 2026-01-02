from typing import cast

from chaos.lib.secret_backends.utils import _check_bws_status, decompress, extract_gpg_keys, is_valid_age_secret_key, is_valid_age_key, extract_age_keys, setup_vault_keys, setup_pipe, get_sops_files, _import_gpg_keys, _import_age_keys, _import_vault_keys
from omegaconf import DictConfig, OmegaConf
from chaos.lib.utils import checkDep
from rich.console import Console
from pathlib import Path
import subprocess
import shlex
import json
import os
import tempfile

console = Console()

"""Bitwarden Secrets (bws) backend for Chaos."""

"Validates and reads the age key content from the specified file path."
def _get_age_key_content(key_path: Path) -> str:
    with key_path.open('r') as f:
        content = f.read()
    if '# public' not in content or 'AGE-SECRET-KEY-' not in content:
        raise ValueError("The specified key file does not appear to be a valid age key.")
    return content

"Exports an age key to Bitwarden Secrets."
def exportBwsAgeKey(key_path: Path, key: str, project_id: str, save_to_config: bool) -> None:
    value = _get_age_key_content(key_path)
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

"Exports a GPG key to Bitwarden Secrets."
def exportBwsGpgKey(key: str, project_id: str, fingerprints: list[str], save_to_config: bool) -> None:
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

"Exports a Vault key to Bitwarden Secrets."
def exportBwsVaultKey(keyPath: Path, vaultAddr: str, key: str, project_id: str, save_to_config: bool) -> None:
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

"Main function to handle exporting keys to Bitwarden Secrets."
def bwsExportKeys(args) -> None:
    _check_bws_status()

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

            exportBwsAgeKey(keyPath, key, project_id, save_to_config)

        case 'gpg':
            if not fingerprints: raise ValueError("At least one GPG fingerprint is required via --fingerprints.")
            if not checkDep("gpg"): raise EnvironmentError("The 'gpg' CLI tool is required but not found in PATH.")

            exportBwsGpgKey(key, project_id, fingerprints, save_to_config)

        case 'vault':
            vaultAddr = args.vault_addr
            keyPath = Path(args.keys)
            if not keyPath: raise ValueError("No Vault key path passed via --keys.")
            if not vaultAddr: raise ValueError("No Vault address passed via --vault-addr.")

            exportBwsVaultKey(keyPath, vaultAddr, key, project_id, save_to_config)
        case _:
            raise ValueError(f"Unsupported key type: {keyType}")

"Retrieves age keys from Bitwarden Secrets."
def getBwsAgeKeys(item_id: str) -> tuple[str, str, str]:
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

        return pubKey, secKey, key_content

    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Error retrieving age keys from Bitwarden: {e.stderr.strip()}") from e

"Retrieves gpg keys from Bitwarden Secrets."
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
        fingerprints = None
        for line in key_content.splitlines():
            if line.startswith("# fingerprints:"):
                fingerprints = line.split(":", 1)[1].strip()
                break

        if not fingerprints:
            raise ValueError("Could not extract GPG fingerprint from Bitwarden item.")

        if "-----BEGIN PGP PRIVATE KEY BLOCK-----" not in key_content:
            raise ValueError("The secret read from Bitwarden does not appear to be a GPG private key block.")

        noHeadersSecKey = key_content.split('-----BEGIN PGP PRIVATE KEY BLOCK-----', 1)[1].rsplit('-----END PGP PRIVATE KEY BLOCK-----', 1)[0]
        secKey = noHeadersSecKey.strip()
        return fingerprints, secKey

    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Error retrieving GPG keys from Bitwarden: {e.stderr.strip()}") from e

"Retrieves Hashicorp vault token and address from Bitwarden Secrets."
def getBwsVaultKey(item_id: str) -> tuple[str, str]:
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

        vault_addr, vault_token = None, None
        for line in key_content.splitlines():
            if line.startswith("# Vault Address:"):
                vault_addr = line.split("::", 1)[1].strip()
            if line.startswith("Vault Key:"):
                vault_token = line.split(":", 1)[1].strip()

        if not vault_addr or not vault_token:
            raise ValueError("Could not extract both Vault address and token from Bitwarden item.")

        return vault_addr, vault_token

    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Error retrieving Vault keys from Bitwarden: {e.stderr.strip()}") from e

"""
Creates the temporary environment for Bitwarden keys based on the provided item ID and key type.

Allows for ephemeral setup of age, gpg, or vault keys retrieved from Bitwarden.
"""
def _setup_bws_env(item_id: str, keyType: str) -> tuple[dict[str, str], list[int], str, tempfile.TemporaryDirectory | None, str | None]:
    env = os.environ.copy()
    fds_to_pass: list[int] = []
    secKey = None
    prefix = ''
    gnupghome = None
    key_content = None
    age_temp_path = None

    match keyType:
        case 'age':
            _, secKey, key_content = getBwsAgeKeys(item_id)
        case 'gpg':
            _, secKey = getBwsGpgKeys(item_id)
            secKey = decompress(secKey)
        case 'vault':
            vault_addr, vault_token = getBwsVaultKey(item_id)
            r_addr = setup_pipe(vault_addr)
            r_token = setup_pipe(vault_token)
            fds_to_pass.extend([r_addr, r_token])
            prefix = (f'read VAULT_ADDR </dev/fd/{r_addr};'
                    f'read VAULT_TOKEN </dev/fd/{r_token};'
                    'export VAULT_ADDR VAULT_TOKEN;')
        case _:
            raise ValueError(f"Unsupported key type: {keyType}")

    if secKey and keyType == 'age':
        if not key_content:
            raise ValueError("No age key content retrieved from Bitwarden.")

        from chaos.lib.secret_backends.utils import conc_age_keys
        secKeyConc = conc_age_keys(key_content)

        with tempfile.NamedTemporaryFile(delete=False, mode='w', dir='/dev/shm', prefix='chaos-age-key-') as temp_age_file:
            temp_age_file.write(secKeyConc)
            if not secKeyConc.endswith('\n'):
                temp_age_file.write('\n')
            age_temp_path = temp_age_file.name

        env[f'SOPS_AGE_KEY_FILE'] = age_temp_path

    if secKey and keyType == 'gpg':
        from chaos.lib.secret_backends.utils import setup_gpg_keys
        gnupghome = tempfile.TemporaryDirectory(dir='/dev/shm', prefix='chaos-gpg-')
        env['GNUPGHOME'] = gnupghome.name
        import_cmd = ['gpg', '--batch', '--import']
        setup_gpg_keys(gnupghome)
        try:
            subprocess.run(
                import_cmd,
                input=secKey,
                env=env,
                check=True,
                capture_output=True
            )
        except subprocess.CalledProcessError as e:
            gnupghome.cleanup()
            raise RuntimeError(f"Error importing GPG key: {e.stderr.strip()}") from e

    return env, fds_to_pass, prefix, gnupghome, age_temp_path

"""Decrypts a SOPS-encrypted file using Bitwarden-stored, locally ephemeral keys."""
def bwsSopsDec(args) -> subprocess.CompletedProcess[str]:
    item_id, keyType = args.from_bws
    secrets_file_override = args.secrets_file_override
    team = args.team
    sops_file_override = args.sops_file_override

    secretsFile, sopsFile, _ = get_sops_files(sops_file_override, secrets_file_override, team)

    env, fds_to_pass, prefix, gnupghome, agePath = _setup_bws_env(item_id, keyType)

    cmd = f"sops --config {shlex.quote(str(sopsFile))} -d {shlex.quote(str(secretsFile))}"
    cmd = f"{prefix}{cmd}" if prefix else cmd

    try:
        result = subprocess.run(cmd, env=env, check=True, capture_output=True, text=True, pass_fds=fds_to_pass, shell=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Error decrypting file with sops and Bitwarden: {e.stderr.strip()}") from e
    finally:
        for fd in fds_to_pass:
            try:
                os.close(fd)
            except OSError:
                pass

        if gnupghome:
            try:
                gnupghome.cleanup()
            except OSError:
                console.print(f"[yellow]WARNING:[/] Could not remove temporary GNUPGHOME directory {gnupghome.name}")

        if agePath:
            try:
                os.remove(agePath)
            except OSError:
                console.print(f"[yellow]WARNING:[/] Could not remove temporary age key file {agePath}")

    if not result.stdout.strip():
        raise ValueError(f"No output received from {secretsFile} file.")

    return result

"""Allows for editing a SOPS-encrypted file using Bitwarden-stored, locally ephemeral keys."""
def bwsSopsEdit(args) -> None:
    item_id, keyType = args.from_bws
    secrets_file_override = args.secrets_file_override
    team = args.team
    sops_file_override = args.sops_file_override

    secretsFile, sopsFile, _ = get_sops_files(sops_file_override, secrets_file_override, team)

    env, fds_to_pass, prefix, gnupghome, agePath = _setup_bws_env(item_id, keyType)

    cmd = f"sops --config {shlex.quote(str(sopsFile))} {shlex.quote(str(secretsFile))}"
    cmd = f"{prefix}{cmd}" if prefix else cmd

    try:
        subprocess.run(cmd, env=env, check=True, pass_fds=fds_to_pass, shell=True)
    except subprocess.CalledProcessError as e:
        if e.returncode != 200:
            raise RuntimeError(f"Error editing file with sops and Bitwarden: {e.stderr.strip()}") from e
    finally:
        for fd in fds_to_pass:
            try:
                os.close(fd)
            except OSError:
                pass

        if gnupghome:
            try:
                gnupghome.cleanup()
            except OSError:
                console.print(f"[yellow]WARNING:[/] Could not remove temporary GNUPGHOME directory {gnupghome.name}")

        if agePath:
            try:
                os.remove(agePath)
            except OSError:
                console.print(f"[yellow]WARNING:[/] Could not remove temporary age key file {agePath}")

"""Imports keys from Bitwarden into local key stores."""
def bwsImportKeys(args) -> None:
    _check_bws_status()
    keyType = args.key_type
    item_id = args.item_id
    if not keyType:
        raise ValueError("Key type must be specified for import.")
    if not item_id:
        raise ValueError("Item ID must be specified for import.")
    match keyType:
        case 'age':
            pubKey, secKey, key_content = getBwsAgeKeys(item_id)
            console.print(f"[green]Successfully imported age key from Bitwarden.[/green]")
            console.print(f"Public Key: [bold]{pubKey}[/bold]")
            console.print(f"Secret Key: [bold]{secKey}[/bold]")

            _import_age_keys(key_content)

        case 'gpg':
            fingerprints, secKey = getBwsGpgKeys(item_id)
            console.print(f"[green]Successfully imported GPG key from Bitwarden.[/green]")
            console.print(f"Fingerprints: [bold]{fingerprints}[/bold]")

            _import_gpg_keys(secKey)

        case 'vault':
            vault_addr, vault_token = getBwsVaultKey(item_id)
            console.print(f"[green]Successfully imported Vault key from Bitwarden.[/green]")
            console.print(f"Vault Address: [bold]{vault_addr}[/bold]")
            console.print(f"Vault Token: [bold]{vault_token}[/bold]")

            key_content = f"# Vault Address:: {vault_addr}\nVault Key: {vault_token}\n"

            _import_vault_keys(key_content)

        case _:
            raise ValueError(f"Unsupported key type: {keyType}")
