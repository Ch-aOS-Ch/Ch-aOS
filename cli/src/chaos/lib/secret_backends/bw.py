import subprocess
from rich.console import Console
import os
from pathlib import Path
import json
from chaos.lib.utils import checkDep
from chaos.lib.secret_backends.utils import get_sops_files

console = Console()

def _check_bw_status():
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

def _setup_bw_env(item_id: str, keyType: str) -> dict:
    env = os.environ.copy()
    if keyType == 'age':
        _, secKey = getAgeKeys(item_id)
    elif keyType == 'gpg':
        _, secKey = getGpgKeys(item_id)
    else:
        raise ValueError(f"Unsupported key type: {keyType}")
    env[f'SOPS_{keyType.upper()}_KEY'] = secKey
    return env

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

def getAgeKeys(item_id: str) -> tuple[str, str]:
    key_content = bwReadKey(item_id)
    if not key_content:
        raise ValueError("Retrieved key from Bitwarden is empty.")

    pubKey, secKey = "", ""
    for line in key_content.splitlines():
        line = line.strip()
        if line.startswith("# public key:"):
            pubKey = line.split(":", 1)[1].strip()
        if line.startswith("AGE-SECRET-KEY-"):
            secKey = line

    if not pubKey:
        raise ValueError("Could not find a public key in the secret from Bitwarden. Expected a line starting with '# public key:'.")
    if not secKey:
        raise ValueError("Could not find a secret key in the secret from Bitwarden. Expected a line starting with 'AGE-SECRET-KEY-'.")

    return pubKey, secKey

def getGpgKeys(item_id: str) -> tuple[str, str]:
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
    env = _setup_bw_env(item_id, keyType)

    try:
        result = subprocess.run(['sops', '--config', sopsFile, '-d', secretsFile], env=env, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Error decrypting file with sops and Bitwarden: {e.stderr.strip()}") from e

    if not result.stdout.strip():
        raise ValueError(f"No output received from {secretsFile} file.")

    return result

def bwSopsEdit(args) -> None:
    item_id, keyType = args.from_bw
    secrets_file_override = args.secrets_file_override
    team = args.team
    sops_file_override = args.sops_file_override

    secretsFile, sopsFile, _ = get_sops_files(sops_file_override, secrets_file_override, team)
    env = _setup_bw_env(item_id, keyType)

    try:
        subprocess.run(['sops', '--config', sopsFile, secretsFile], env=env, check=True)
    except subprocess.CalledProcessError as e:
        if e.returncode != 200: # 200 is sops' "no changes" exit code
            raise RuntimeError(f"Error editing file with sops and Bitwarden: {e.stderr.strip()}") from e

def bwExportKeys(args):
    _check_bw_status()
    keyType = args.key_type
    keyPath = args.keys
    item_name = args.item_name
    fingerprint = args.fingerprint
    tags = args.bw_tags
    collection_id = args.collection_id
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

        try:
            result = subprocess.run(
                ["gpg", "--export-secret-keys", "--armor", fingerprint],
                capture_output=True, text=True, check=True
            )
            gpg_key = result.stdout.strip()
            if not gpg_key: raise ValueError("No output from 'gpg --export-secret-keys'. Is the fingerprint correct?")
            key_content = f"# fingerprint: {fingerprint}\n{gpg_key}"
            console.print(f"[green]INFO:[/] Exporting GPG key for fingerprint: {fingerprint}")

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to export GPG secret key: {e.stderr.strip()}") from e
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

        if tags:
            tag_json = {"tags": tags}
            encoded_tags = subprocess.run(
                ['bw', 'encode'],
                input=json.dumps(tag_json),
                capture_output=True, text=True, check=True
            ).stdout.strip()
            subprocess.run(['bw', 'edit', 'item', created_item['id'], encoded_tags], check=True)

        console.print(f"[bold green]Success![/] Successfully exported {keyType} key to Bitwarden item '{created_item['name']}' (ID: {created_item['id']}).")

    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Error creating item in Bitwarden: {e.stderr.strip()}") from e
    except (json.JSONDecodeError, KeyError) as e:
        raise RuntimeError(f"Failed to parse Bitwarden output: {e}") from e
