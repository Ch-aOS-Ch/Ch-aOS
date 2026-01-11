import os
import tempfile
import subprocess
from contextlib import contextmanager
from pathlib import Path

@contextmanager
def ephemeralAgeKey(key_content: str):
    from .utils import conc_age_keys, setup_pipe
    """
    Create a temporary file containing the provided Age key content.
    Args:
        key_content (str): The content of the Age key.
    Returns:
        tuple: A context manager that yields a tuple containing:
            - A string to be used as a prefix in shell commands to set the SOPS_AGE_KEY environment variable.
            - A list of file descriptors that need to be passed to subprocesses.
    """

    if not key_content:
        yield {}
        return
    sanitized_content = "\n".join(line.lstrip() for line in key_content.splitlines())
    final_content = conc_age_keys(sanitized_content)

    r_age = setup_pipe(final_content)
    prefix = f'export SOPS_AGE_KEY="$(cat /dev/fd/{r_age})";'
    fds_to_pass = [r_age]

    try:
        yield prefix, fds_to_pass
    finally:
        os.close(r_age)

@contextmanager
def ephemeralGpgKey(key_bytes: bytes):
    from .utils import setup_gpg_keys
    """
    Creates a temporary GNUPGHOME in memory (/dev/shm)
    Imports the gotten key to this GNUPGHOME and returns the env path
    """
    if not key_bytes:
        yield {}
        return

    with tempfile.TemporaryDirectory(dir='/dev/shm', prefix='chaos-gpg-') as temp_dir_name:
        temp_path = Path(temp_dir_name)
        setup_gpg_keys(temp_path)

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
