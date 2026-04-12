"""Context managers for handling ephemeral cryptographic keys in secure memory environments."""

import os
import subprocess
import tempfile
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def ephemeralAgeKey(key_content: str):
    from ..utils import conc_age_keys, setup_pipe

    """Create a temporary file containing the provided Age key content.
    Args:
        key_content (str): The content of the Age key.

    Returns:
        tuple: A context manager that yields a tuple containing:
            A string to be used as a prefix in shell commands to set the SOPS_AGE_KEY environment variable.
            A list of file descriptors that need to be passed to subprocesses.
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
def mac_ram_disk():
    """Creates an ephemeral RAM Disk on macOS
    Yields:
        The mount point of the RAM Disk
    """

    # 4096 sectors of 512 bytes = 2MB in RAM
    attach_cmd = subprocess.run(
        ["hdiutil", "attach", "-nomount", "ram://4096"],
        capture_output=True,
        text=True,
        check=True,
    )
    device = attach_cmd.stdout.strip()

    try:
        subprocess.run(
            ["diskutil", "erasevolume", "HFS+", "ChaosGPG", device],
            capture_output=True,
            check=True,
        )
        mount_point = "/Volumes/ChaosGPG"
        yield mount_point
    finally:
        subprocess.run(
            ["hdiutil", "detach", device, "-force"], capture_output=True, check=False
        )


@contextmanager
def ephemeralGpgKey(key_bytes: bytes):
    import platform

    from ..utils import setup_gpg_keys

    """Creates a temporary GNUPGHOME in memory (/dev/shm on Linux, RAM Disk on macOS)
    Imports the gotten key to this GNUPGHOME and returns the env path

    Args:
        key_bytes: The unarmored GPG key to be imported ephemerally

    Yields:
        A dict containing the GNUPGHOME directory as the shm path. This is yielded as a dict to be used directly with os.env
    """
    if not key_bytes:
        yield {}
        return

    is_mac = platform.system() == "Darwin"

    if is_mac:
        from contextlib import ExitStack

        with ExitStack() as stack:
            try:
                ram_dir = stack.enter_context(mac_ram_disk())
                temp_dir_name = stack.enter_context(
                    tempfile.TemporaryDirectory(dir=ram_dir, prefix="chaos-gpg-")
                )

                temp_path = Path(temp_dir_name)
                setup_gpg_keys(temp_path)
            except Exception as e:
                raise RuntimeError(f"Failed to generate GPG home: {e}")

            try:
                subprocess.run(
                    ["gpg", "--batch", "--import"],
                    input=key_bytes,
                    env={"GNUPGHOME": str(temp_path)},
                    check=True,
                    capture_output=True,
                )

            except subprocess.CalledProcessError as e:
                err_msg = e.stderr.decode() if getattr(e, "stderr", None) else str(e)
                raise RuntimeError(f"Failed to import GPG key: {err_msg}")

            yield {"GNUPGHOME": str(temp_path)}
    else:
        shm_dir = "/dev/shm" if os.path.exists("/dev/shm") else None
        with tempfile.TemporaryDirectory(
            dir=shm_dir, prefix="chaos-gpg-"
        ) as temp_dir_name:
            try:
                temp_path = Path(temp_dir_name)
                setup_gpg_keys(temp_path)
            except Exception as e:
                raise RuntimeError(f"Failed to generate GPG home: {e}")

            try:
                subprocess.run(
                    ["gpg", "--batch", "--import"],
                    input=key_bytes,
                    env={"GNUPGHOME": str(temp_path)},
                    check=True,
                    capture_output=True,
                )
            except subprocess.CalledProcessError as e:
                err_msg = e.stderr.decode() if getattr(e, "stderr", None) else str(e)
                raise RuntimeError(f"Failed to import GPG key: {err_msg}")

            yield {"GNUPGHOME": str(temp_path)}


@contextmanager
def ephemeralVaultKeys(vault_token: str, vault_addr: str):
    from ..utils import setup_pipe

    """Creates pipes for setting up the address and token for vault.
    Args:
        vault_token: The token to authenticate with vault
        vault_addr: The address of the vault server
    Yields:
        A tuple containing:
            A string to be used as a prefix in shell commands to set the VAULT_ADDR and VAULT_TOKEN environment variables.
            A list of file descriptors that need to be passed to subprocesses.
    """
    if not vault_addr or not vault_token:
        yield "", []
        return
    r_addr = setup_pipe(vault_addr)
    r_token = setup_pipe(vault_token)
    prefix = (
        f"read VAULT_ADDR </dev/fd/{r_addr};"
        f"read VAULT_TOKEN </dev/fd/{r_token};"
        "export VAULT_ADDR VAULT_TOKEN;"
    )
    fds_to_pass = [r_addr, r_token]
    try:
        yield prefix, fds_to_pass
    finally:
        os.close(r_addr)
        os.close(r_token)
