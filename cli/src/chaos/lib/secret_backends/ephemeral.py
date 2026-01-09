import os
import tempfile
import subprocess
from contextlib import contextmanager
from pathlib import Path

@contextmanager
def ephemeralAgeKey(key_content: str):
    """
    Create a temporary file containing the provided Age key content.
    Args:
        key_content (str): The content of the Age key.
    Returns:
        str: The path to the temporary Age key file.
    """

    if not key_content:
        yield {}
        return

    with tempfile.NamedTemporaryFile(delete=False, mode='w', prefix='chaos-age-', dir="/dev/shm") as temp_file:
        sanitized_content = "\n".join(line.lstrip() for line in key_content.splitlines())
        temp_file.write(sanitized_content)
        if not sanitized_content.endswith('\n'):
            temp_file.write('\n')
        temp_file_path = temp_file.name

    try:
        yield {'SOPS_AGE_KEY_FILE': temp_file_path}
    finally:
        os.remove(temp_file_path)

@contextmanager
def ephemeralGpgKey(key_bytes: bytes):
    """
    Creates a temporary GNUPGHOME in memory (/dev/shm)
    Imports the gotten key to this GNUPGHOME and returns the env path
    """
    if not key_bytes:
        yield {}
        return

    with tempfile.TemporaryDirectory(dir='/dev/shm', prefix='chaos-gpg-') as temp_dir_name:
        temp_path = Path(temp_dir_name)

        try:
            subprocess.run(
                ['gpg', '--batch', '--import'],
                input=key_bytes,
                env={'GNUPGHOME': str(temp_path)},
                check=True,
                capture_output=True
            )
            yield {'GNUPGHOME': str(temp_path)}

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Erro ao importar chave GPG efêmera: {e.stderr.decode()}")

@contextmanager
def ephemeralVaultKeys(vault_token: str, vault_addr: str):
    from .utils import setup_pipe
    """
    Creates pipes for setting up the address and token for vault.
    """
    if not vault_addr or not vault_token:
        yield "", []
        return
    r_addr = setup_pipe(vault_addr)
    r_token = setup_pipe(vault_token)
    prefix = (f'read VAULT_ADDR </dev/fd/{r_addr};'
            f'read VAULT_TOKEN </dev/fd/{r_token};'
            'export VAULT_ADDR VAULT_TOKEN;')
    fds_to_pass = [r_addr, r_token]
    try:
        yield prefix, fds_to_pass
    finally:
        os.close(r_addr)
        os.close(r_token)
