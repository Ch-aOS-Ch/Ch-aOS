from chaos.lib.secret_backends.utils import exctract_gpg_keys, get_sops_files, _check_bw_status, extract_age_keys
from chaos.lib.utils import checkDep
from rich.console import Console
from pathlib import Path
import subprocess
import json
import os
from omegaconf import OmegaConf, DictConfig
from typing import cast

console = Console()

def _setup_bw_env(item_id: str, keyType: str) -> tuple[dict[str, str], list[int], str]:
    env = os.environ.copy()
    fds_to_pass: list[int] = []
    secKey = None
    prefix = ''

    if keyType == 'age':
        _, secKey = getBwAgeKeys(item_id)
    elif keyType == 'gpg':
        _, secKey = getBwGpgKeys(item_id)
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

    if secKey:
        r_secKey = setup_pipe(secKey)
        fds_to_pass.append(r_secKey)
        env[f'SOPS_{keyType.upper()}_KEY_FILE'] = f"/dev/fd/{r_secKey}"

    return env, fds_to_pass, prefix

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

def getBwAgeKeys(item_id: str) -> tuple[str, str]:
    key_content = bwReadKey(item_id)
    if not key_content: raise ValueError("Retrieved key from Bitwarden is empty.")

    pubKey, secKey = extract_age_keys(key_content)

    if not pubKey:
        raise ValueError("Could not find a public key in the secret from Bitwarden. Expected a line starting with '# public key:'.")
    if not secKey:
        raise ValueError("Could not find a secret key in the secret from Bitwarden. Expected a line starting with 'AGE-SECRET-KEY-'.")

    return pubKey, secKey

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

def getBwGpgKeys(item_id: str) -> tuple[str, str]:
    key_content = bwReadKey(item_id)
    if not key_content:
        raise ValueError("Retrieved GPG key from Bitwarden is empty.")

    fingerprint = ""
    for line in key_content.splitlines():
        if line.startswith("# fingerprint:"):
            fingerprint = line.split(":", 1)[1].strip()
            break
    secKey = key_content

    if "-----BEGIN PGP PRIVATE KEY BLOCK-----" not in secKey:
        raise ValueError("The secret read from Bitwarden does not appear to be a GPG private key block.")

    return fingerprint, secKey

def bwSopsDec(args) -> subprocess.CompletedProcess[str]:
    item_id, keyType = args.from_bw
    secrets_file_override = args.secrets_file_override
    team = args.team
    sops_file_override = args.sops_file_override

    secretsFile, sopsFile, _ = get_sops_files(sops_file_override, secrets_file_override, team)
    env, fds, prefix = _setup_bw_env(item_id, keyType)
    cmd = f"sops --config {shlex.quote(str(sopsFile))} -d {shlex.quote(str(secretsFile))}"
    cmd = f"{prefix} {cmd}" if prefix else cmd

    try:
        result = subprocess.run(cmd, env=env, check=True, capture_output=True, text=True, pass_fds=fds)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Error decrypting file with sops and Bitwarden: {e.stderr.strip()}") from e
    finally:
        for r in fds:
            try:
                os.close(r)
            except OSError:
                pass

    if not result.stdout.strip():
        raise ValueError(f"No output received from {secretsFile} file.")

    return result

def bwSopsEdit(args) -> None:
    item_id, keyType = args.from_bw
    secrets_file_override = args.secrets_file_override
    team = args.team
    sops_file_override = args.sops_file_override

    secretsFile, sopsFile, _ = get_sops_files(sops_file_override, secrets_file_override, team)
    env, fds, prefix = _setup_bw_env(item_id, keyType)
    cmd = f"sops --config {sopsFile} {secretsFile}"
    cmd = f"{prefix} {cmd}" if prefix else cmd

    try:
        subprocess.run(cmd, env=env, check=True, capture_output=True, text=True, pass_fds=fds)
    except subprocess.CalledProcessError as e:
        if e.returncode != 200: # 200 is sops' "no changes" exit code
            raise RuntimeError(f"Error editing file with sops and Bitwarden: {e.stderr.strip()}") from e
    finally:
        for r in fds:
            try:
                os.close(r)
            except OSError:
                pass

def bwExportKeys(args):
    _check_bw_status()
    keyType = args.key_type
    keyPath = args.keys
    item_name = args.item_name
    fingerprint = args.fingerprint
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
        if not fingerprint: raise ValueError("A GPG fingerprint is required via --fingerprint.")
        if not checkDep("gpg"): raise EnvironmentError("The 'gpg' CLI tool is required but not found in PATH.")

        key_content = extract_gpg_keys(fingerprint)

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
        if collection_id:
            item_json["collectionIds"] = [collection_id]

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
