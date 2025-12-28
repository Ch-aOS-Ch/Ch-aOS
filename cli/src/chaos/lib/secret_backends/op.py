import subprocess
from rich.console import Console
import os
from pathlib import Path
from chaos.lib.utils import checkDep
from chaos.lib.secret_backends.utils import _build_op_keypath, get_sops_files, _reg_match_op_keypath, _op_get_item, _op_create_item

console = Console()

def _setup_op_env(url: str, keyType: str) -> tuple[dict[str, str], int]:
    path = url

    r, w = os.pipe()
    env = os.environ.copy()
    if keyType == 'age':
        _, secKey = getAgeKeys(path)
    elif keyType == 'gpg':
        _, secKey = getGpgKeys(path)
    else:
        raise ValueError(f"Unsupported key type.")
    try:
        os.write(w, secKey.encode())
        os.fchmod(w, 0o600)
        os.close(w)
        env[f'SOPS_{keyType.upper()}_KEY_FILE'] = f"/dev/fd/{r}"
    except Exception as e:
        raise RuntimeError(f"Error setting up environment for sops decryption: {str(e)}") from e
    return env, r

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

def getAgeKeys(path) -> tuple[str, str]:
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

    return pubKey, secKey

def getGpgKeys(path) -> tuple[str, str]:
    key_content = opReadKey(path)

    if not key_content:
        raise ValueError("Retrieved GPG key from 1Password is empty.")

    fingerprint = ""
    for line in key_content.splitlines():
        if line.startswith("# fingerprint:"):
            fingerprint = line.split(":", 1)[1].strip()
            break

    secKey = key_content

    if "-----BEGIN PGP PRIVATE KEY BLOCK-----" not in secKey:
        raise ValueError("The secret read from 1Password does not appear to be a GPG private key block.")

    return fingerprint, secKey

def opSopsDec(args) -> subprocess.CompletedProcess[str]:
    url, keyType = args.from_op
    team = args.team
    secrets_file_override = args.secrets_file_override
    sops_file_override = args.sops_file_override

    secretsFile, sopsFile, _ = get_sops_files(sops_file_override, secrets_file_override, team)

    env, r = _setup_op_env(url, keyType)

    try:
        result = subprocess.run(['sops', '--config', sopsFile, '-d', secretsFile], env=env, check=True, capture_output=True, text=True, pass_fds=(r,))
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Error decrypting file with sops: {e.stderr.strip()}") from e
    finally:
        try:
            os.close(r)
        except OSError:
            pass

    if not result.stdout.strip():
        raise ValueError(f"No output received from {secretsFile} file.")

    return result

def opSopsEdit(args) -> None:
    url, keyType = args.from_op
    secrets_file_override = args.secrets_file_override
    team = args.team
    sops_file_override = args.sops_file_override

    env, r = _setup_op_env(url, keyType)

    secretsFile, sopsFile, _ = get_sops_files(sops_file_override, secrets_file_override, team)

    try:
        subprocess.run(['sops', '--config', sopsFile, secretsFile], env=env, check=True, pass_fds=(r,))
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Error editing file with sops: {e.stderr.strip()}") from e
    finally:
        try:
            os.close(r)
        except OSError:
            pass

def opExportKeys(args):
    keyType = args.key_type
    keyPath = args.keys
    fingerprint = args.fingerprint
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
        if not fingerprint:
            raise ValueError("A GPG fingerprint is required. Please provide it with --fingerprint.")

        if not checkDep("gpg"):
            raise EnvironmentError("The 'gpg' CLI tool is required but not found in PATH.")

        try:
            result = subprocess.run(
                ["gpg", "--export-secret-keys", "--armor", fingerprint],
                capture_output=True,
                text=True,
                check=True
            )
            key_content = result.stdout.strip()
            if not key_content:
                raise ValueError("No output from 'gpg --export-secret-keys'. Is the fingerprint correct?")

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to export GPG secret key: {e.stderr.strip()}") from e

        key_with_comment = f"# fingerprint: {fingerprint}\n{key_content}"

        if not all([key_with_comment, path, loc]):
            raise ValueError("Missing required parameters for exporting keys to 1Password.")

        _op_create_item(vault, title, loc, tags, key_with_comment)

        console.print(f"[green]INFO:[/] Successfully exported GPG key for fingerprint to 1Password: {fingerprint}")
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
