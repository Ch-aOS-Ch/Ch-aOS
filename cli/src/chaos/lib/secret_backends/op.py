import shlex
import subprocess
from rich.console import Console
import os
from pathlib import Path
from chaos.lib.utils import checkDep
from chaos.lib.secret_backends.utils import _build_op_keypath, decompress, extract_gpg_keys, get_sops_files, _reg_match_op_keypath, _op_get_item, _op_create_item, setup_vault_keys, setup_pipe, _import_age_keys, _import_gpg_keys, _import_vault_keys
import tempfile

console = Console()

"""1Password secret backend for Chaos. HEAVILY inspired by https://github.com/natrontech/sops-age-op"""

"""
Creates the temporary environment for 1Password keys based on the provided item ID and key type.

Allows for ephemeral setup of age, gpg, or vault keys retrieved from 1Password.
"""
def _setup_op_env(url: str, keyType: str) -> tuple[dict[str, str], list[int], str, tempfile.TemporaryDirectory | None, str | None]:
    path = url
    env = os.environ.copy()
    fds_to_pass: list[int] = []
    secKey = None
    prefix = ''
    gnupghome = None
    key_content = None
    age_temp_path = None

    if keyType == 'age':
        _, secKey, key_content = getAgeKeys(path)
    elif keyType == 'gpg':
        _, secKey = getGpgKeys(path)
        secKey = decompress(secKey)
    elif keyType == 'vault':
        vault_addr, vault_token = getOpVaultKeys(path)
        r_addr = setup_pipe(vault_addr)
        r_token = setup_pipe(vault_token)
        fds_to_pass.extend([r_addr, r_token])
        prefix = (f'read VAULT_ADDR </dev/fd/{r_addr};'
                f'read VAULT_TOKEN </dev/fd/{r_token};'
                'export VAULT_ADDR VAULT_TOKEN;')
    else:
        raise ValueError(f"Unsupported key type: {keyType}")

    if secKey and keyType == 'age':
        if not key_content:
            raise ValueError("No age key content retrieved from 1Password.")

        from chaos.lib.secret_backends.utils import conc_age_keys
        secKeyConc = conc_age_keys(key_content)

        with tempfile.NamedTemporaryFile(delete=False, mode='w', dir='/dev/shm', prefix='chaos-age-key-') as temp_age_file:
            temp_age_file.write(secKeyConc)
            if not secKeyConc.endswith('\n'):
                temp_age_file.write('\n')
            age_temp_path = temp_age_file.name

        env['SOPS_AGE_KEY_FILE'] = age_temp_path

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

"""Reads the secret key content from a 1Password item by its URL + path."""
def opReadKey(path: str, loc: str | None = None) -> str:
    if not checkDep("op"):
        raise EnvironmentError("The 'op' CLI tool is required but not found in PATH.")

    if loc:
        path = _build_op_keypath(path, loc)

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
def getAgeKeys(path) -> tuple[str, str, str]:
    key_content = opReadKey(path)

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
def getGpgKeys(path) -> tuple[str, str]:
    key_content = opReadKey(path)

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
def getOpVaultKeys(path: str) -> tuple[str, str]:
    key_content = opReadKey(path)

    vault_addr, vault_token = None, None
    for line in key_content.splitlines():
        if line.startswith("# Vault Address:"):
            vault_addr = line.split("::", 1)[1].strip()
        if line.startswith("Vault Key:"):
            vault_token = line.split(":", 1)[1].strip()

    if not vault_addr or not vault_token:
        raise ValueError("Could not extract both Vault address and token from 1Password item.")

    return vault_addr, vault_token

"""Decrypts a sops-encrypted file using keys retrieved from 1Password."""
def opSopsDec(args) -> subprocess.CompletedProcess[str]:
    url, keyType = args.from_op
    team = args.team
    secrets_file_override = args.secrets_file_override
    sops_file_override = args.sops_file_override

    secretsFile, sopsFile, _ = get_sops_files(sops_file_override, secrets_file_override, team)

    env, fds, prefix, gnupghome, agePath = _setup_op_env(url, keyType)
    cmd = f"sops --config {shlex.quote(str(sopsFile))} -d {shlex.quote(str(secretsFile))}"
    cmd = f"{prefix} {cmd}" if prefix else cmd

    try:
        result = subprocess.run(cmd, env=env, check=True, capture_output=True, text=True, pass_fds=fds, shell=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Error decrypting file with sops: {e.stderr.strip()}") from e
    finally:
        for r in fds:
            try:
                os.close(r)
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

"""Opens a sops-encrypted file for editing using keys retrieved from 1Password."""
def opSopsEdit(args) -> None:
    url, keyType = args.from_op
    secrets_file_override = args.secrets_file_override
    team = args.team
    sops_file_override = args.sops_file_override

    secretsFile, sopsFile, _ = get_sops_files(sops_file_override, secrets_file_override, team)
    env, fds, prefix, gnupghome, agePath = _setup_op_env(url, keyType)
    cmd = f"sops --config {shlex.quote(str(sopsFile))} {shlex.quote(str(secretsFile))}"
    cmd = f"{prefix} {cmd}" if prefix else cmd

    try:
        subprocess.run(cmd, env=env, check=True, pass_fds=fds, shell=True)
    except subprocess.CalledProcessError as e:
        if e.returncode != 200: # 200 is sops' "no changes" exit code
            raise RuntimeError(f"Error editing file with sops: {e.stderr.strip()}") from e
    finally:
        for r in fds:
            try:
                os.close(r)
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

"""Exports keys to a 1Password item."""
def opExportKeys(args):
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

    vault, title, _ = _reg_match_op_keypath(path)
    if _op_get_item(vault, title) is not None:
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

        _op_create_item(vault, title, loc, tags, key)

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

        _op_create_item(vault, title, loc, tags, key_content)

        console.print(f"[green]INFO:[/] Successfully exported GPG keys for to 1Password: '{', '.join(fingerprints)}'")

    elif keyType == 'vault':
        vaultAddr = args.vault_addr
        if not keyPath: raise ValueError("No Vault key path passed via --keys.")
        if not vaultAddr: raise ValueError("No Vault address passed via --vault-addr.")
        keyPath = Path(keyPath).expanduser()

        key_content = setup_vault_keys(vaultAddr, keyPath)

        if not all([key_content, path, loc]):
            raise ValueError("Missing required parameters for exporting keys to 1Password.")

        _op_create_item(vault, title, loc, tags, key_content)
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

"""Imports keys from a 1Password item."""
def opImportKeys(args):
    keyType = args.key_type
    url = args.url
    loc = args.op_location
    if not keyType:
        raise ValueError("Key type must be specified for import.")
    if not url:
        raise ValueError("Item ID must be specified for import.")

    if keyType == 'age':
        pubKey, secKey, key_content = getAgeKeys(url)
        console.print(f"[green]Successfully imported age key from Bitwarden.[/green]")
        console.print(f"Public Key: [bold]{pubKey}[/bold]")
        console.print(f"Secret Key: [bold]{secKey}[/bold]")

        _import_age_keys(key_content)

    elif keyType == 'gpg':
        fingerprints, secKey = getGpgKeys(url)
        console.print(f"[green]Successfully imported GPG key from Bitwarden.[/green]")
        console.print(f"Fingerprints: [bold]{fingerprints}[/bold]")

        _import_gpg_keys(secKey)

    elif keyType == 'vault':
        vault_addr, vault_token = getOpVaultKeys(url)
        console.print(f"[green]Successfully imported Vault key from Bitwarden.[/green]")
        console.print(f"Vault Address: [bold]{vault_addr}[/bold]")
        console.print(f"Vault Token: [bold]{vault_token}[/bold]")

        key_content = f"# Vault Address:: {vault_addr}\nVault Key: {vault_token}\n"

        _import_vault_keys(key_content)

    else:
        raise ValueError(f"Unsupported key type: {keyType}")
