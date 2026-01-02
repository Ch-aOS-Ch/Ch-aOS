from chaos.lib.secret_backends.utils import extract_gpg_keys, get_sops_files, _check_bw_status, extract_age_keys
from chaos.lib.utils import checkDep
from rich.console import Console
from pathlib import Path
import subprocess
import tempfile
import json
import os

"""
Module that handles bw (Bitwarden) secret backend operations for Chaos.
"""

"""
Creates the temporary environment for Bitwarden keys based on the provided item ID and key type.

Allows for ephemeral setup of age, gpg, or vault keys retrieved from Bitwarden.
"""
def _setup_bw_env(item_id: str, keyType: str) -> tuple[dict[str, str], list[int], str, tempfile.TemporaryDirectory | None, str | None]:
    env = os.environ.copy()
    fds_to_pass: list[int] = []
    secKey = None
    prefix = ''
    gnupghome = None
    key_content = None
    age_temp_path = None

    if keyType == 'age':
        _, secKey, key_content = getBwAgeKeys(item_id)
    elif keyType == 'gpg':
        _, secKey = getBwGpgKeys(item_id)
        secKey = decompress(secKey)
    elif keyType == 'vault':
        vault_addr, vault_token = getBwVaultKeys(item_id)
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
            raise ValueError("No age key content retrieved from Bitwarden.")

        from chaos.lib.secret_backends.utils import conc_age_keys
        secKeyConc = conc_age_keys(key_content)

        with tempfile.NamedTemporaryFile(delete=False, mode='w', dir='/dev/shm', prefix='chaos-age-key-') as temp_age_file:
            temp_age_file.write(secKeyConc)
            if not secKeyConc.endswith('\n'):
                temp_age_file.write('\n')
            age_temp_path = temp_age_file.name

        env['SOPS_AGE_KEY_FILE'] = age_temp_path

    if secKey and keyType == 'gpg':
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
            raise RuntimeError(f"Error importing GPG key: {e.stderr.decode().strip()}") from e

    return env, fds_to_pass, prefix, gnupghome, age_temp_path

"""Reads the secret key content from a Bitwarden item by its ID."""
def bwReadKey(item_id: str) -> str:
    _check_bw_status()
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

"""Retrieves age keys from a Bitwarden item by its ID."""
def getBwAgeKeys(item_id: str) -> tuple[str, str, str]:
    key_content = bwReadKey(item_id)
    if not key_content: raise ValueError("Retrieved key from Bitwarden is empty.")

    pubKey, secKey = extract_age_keys(key_content)

    if not pubKey:
        raise ValueError("Could not find a public key in the secret from Bitwarden. Expected a line starting with '# public key:'.")
    if not secKey:
        raise ValueError("Could not find a secret key in the secret from Bitwarden. Expected a line starting with 'AGE-SECRET-KEY-'.")

    return pubKey, secKey, key_content

"""Retrieves Vault keys from a Bitwarden item by its ID."""
def getBwVaultKeys(item_id: str) -> tuple[str, str]:
    key_content = bwReadKey(item_id)

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
def getBwGpgKeys(item_id: str) -> tuple[str, str]:
    key_content = bwReadKey(item_id)
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

"""Decrypts a SOPS-encrypted file using Bitwarden-stored, locally ephemeral keys."""
def bwSopsDec(args) -> subprocess.CompletedProcess[str]:
    item_id, keyType = args.from_bw
    secrets_file_override = args.secrets_file_override
    team = args.team
    sops_file_override = args.sops_file_override

    secretsFile, sopsFile, _ = get_sops_files(sops_file_override, secrets_file_override, team)
    env, fds, prefix, gnupghome, agePath = _setup_bw_env(item_id, keyType)
    cmd = f"sops --config {shlex.quote(str(sopsFile))} -d {shlex.quote(str(secretsFile))}"
    cmd = f"{prefix} {cmd}" if prefix else cmd

    try:
        result = subprocess.run(cmd, env=env, check=True, capture_output=True, text=True, pass_fds=fds, shell=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Error decrypting file with sops and Bitwarden: {e.stderr.strip()}") from e
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

"""Allows for editing a SOPS-encrypted file using Bitwarden-stored, locally ephemeral keys."""
def bwSopsEdit(args) -> None:
    item_id, keyType = args.from_bw
    secrets_file_override = args.secrets_file_override
    team = args.team
    sops_file_override = args.sops_file_override

    secretsFile, sopsFile, _ = get_sops_files(sops_file_override, secrets_file_override, team)
    env, fds, prefix, gnupghome, agePath = _setup_bw_env(item_id, keyType)
    cmd = f"sops --config {shlex.quote(str(sopsFile))} {shlex.quote(str(secretsFile))}"
    cmd = f"{prefix} {cmd}" if prefix else cmd

    try:
        subprocess.run(cmd, env=env, check=True, pass_fds=fds, shell=True)
    except subprocess.CalledProcessError as e:
        if e.returncode != 200: # 200 is sops' "no changes" exit code
            raise RuntimeError(f"Error editing file with sops and Bitwarden: {e.stderr.strip()}") from e
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

"""
Exports keys to Bitwarden by creating a new item with the key content in the notes field.

Note: gpg keys need to be compressed using zlib+b85 to fit within Bitwarden's item size limits.
"""
def bwExportKeys(args):
    _check_bw_status()
    keyType = args.key_type
    keyPath = args.keys
    item_name = args.item_name
    fingerprints = args.fingerprints
    tags = args.bw_tags
    save_to_config = args.save_to_config

    _, _, config = get_sops_files(None, None, None)

    collection_id = config.get('secret_providers', {}).get('bw', {}).get('collection_id', '')
    organization_id = config.get('secret_providers', {}).get('bw', {}).get('organization_id', '')

    if args.collection_id:
        collection_id = args.collection_id
    if args.organization_id:
        organization_id = args.organization_id

    key_content = ""
    if keyType == 'age':
        if not keyPath: raise ValueError("No age key path passed via --keys.")
        keyPath = Path(keyPath).expanduser()
        if not keyPath.is_file(): raise FileNotFoundError(f"Path {keyPath} is not a file.")
        with open(keyPath, 'r') as f:
            key_content = f.read()

        pubkey = ""
        for line in key_content.splitlines():
            if line.startswith("# public key:"):
                pubkey = line.split("# public key:", 1)[1].strip()
                break
        if not pubkey:
            raise ValueError("Could not extract public key from key file.")
        console.print(f"[green]INFO:[/] Exporting age public key: {pubkey}")

    elif keyType == 'gpg':
        if not fingerprints: raise ValueError("At least one GPG fingerprint is required via --fingerprints.")
        if not checkDep("gpg"): raise EnvironmentError("The 'gpg' CLI tool is required but not found in PATH.")

        key_content = extract_gpg_keys(fingerprints)

    elif keyType == 'vault':
        vaultAddr = args.vault_addr
        if not keyPath: raise ValueError("No Vault key path passed via --keys.")
        if not vaultAddr: raise ValueError("No Vault address passed via --vault-addr.")
        keyPath = Path(keyPath).expanduser()

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

        if tags:
            tag_json = {"tags": tags}
            encoded_tags = subprocess.run(
                ['bw', 'encode'],
                input=json.dumps(tag_json),
                capture_output=True, text=True, check=True
            ).stdout.strip()
            subprocess.run(['bw', 'edit', 'item', created_item['id'], encoded_tags], check=True)

        console.print(f"[bold green]Success![/] Successfully exported {keyType} key to Bitwarden item '{created_item['name']}' (ID: {created_item['id']}).")

        if save_to_config and item_id:
            from chaos.lib.secret_backends.utils import _save_to_config
            _save_to_config(item_id=item_id, collection_id=collection_id, organization_id=organization_id, backend='bw', keyType=keyType)

    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Error creating item in Bitwarden: {e.stderr.strip()}") from e
    except (json.JSONDecodeError, KeyError) as e:
        raise RuntimeError(f"Failed to parse Bitwarden output: {e}") from e

"""Imports keys from Bitwarden into local key stores."""
def bwImportKeys(args):
    _check_bw_status()
    keyType = args.key_type
    item_id = args.item_id
    if not keyType:
        raise ValueError("Key type must be specified for import.")
    if not item_id:
        raise ValueError("Item ID must be specified for import.")
    match keyType:
        case 'age':
            pubKey, secKey, key_content = getBwAgeKeys(item_id)
            console.print(f"[green]Successfully imported age key from Bitwarden.[/green]")
            console.print(f"Public Key: [bold]{pubKey}[/bold]")
            console.print(f"Secret Key: [bold]{secKey}[/bold]")

            _import_age_keys(key_content)

        case 'gpg':
            fingerprints, secKey = getBwGpgKeys(item_id)
            console.print(f"[green]Successfully imported GPG key from Bitwarden.[/green]")
            console.print(f"Fingerprints: [bold]{fingerprints}[/bold]")

            _import_gpg_keys(secKey)

        case 'vault':
            vault_addr, vault_token = getBwVaultKeys(item_id)
            console.print(f"[green]Successfully imported Vault key from Bitwarden.[/green]")
            console.print(f"Vault Address: [bold]{vault_addr}[/bold]")
            console.print(f"Vault Token: [bold]{vault_token}[/bold]")

            key_content = f"# Vault Address:: {vault_addr}\nVault Key: {vault_token}\n"

            _import_vault_keys(key_content)

        case _:
            raise ValueError(f"Unsupported key type: {keyType}")
