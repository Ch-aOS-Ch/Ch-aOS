from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Iterator

from chaos.lib.secret_backends.key_backends.backend import KeyBackend
from chaos.lib.secret_backends.utils import _is_valid_vault_key, setup_vault_keys

if TYPE_CHECKING:
    from typing import TypedDict

    from chaos.lib.args.dataclasses import SecretsExportPayload, SecretsRotatePayload

    class EphemeralEnvironment(TypedDict):
        env: dict[str, str]
        prefix: str
        pass_fds: list[int]


class VaultBackend(KeyBackend):
    @property
    def key_type(self) -> str:
        return "vault"

    def validate_for_add(
        self, keys: list[str], payload: SecretsRotatePayload
    ) -> tuple[set[str], list[str], list[str]]:
        messages: list[str] = []
        errors: list[str] = []
        valids: set[str] = set()
        for key in keys:
            clean_key = key.strip()
            is_valid, message = _is_valid_vault_key(clean_key)
            if is_valid:
                messages.append(message)
                valids.add(clean_key)
            else:
                errors.append(f"{message} Skipping key '{key}'.")
                continue
        return valids, messages, errors

    def validate_for_rem(
        self, keys: list[str], payload: SecretsRotatePayload
    ) -> tuple[set[str], list[str], list[str]]:
        clean_keys = {key.strip() for key in keys}
        return clean_keys, [], []

    def prepare_export_content(
        self, payload: SecretsExportPayload
    ) -> tuple[str, list[str]]:
        import os

        vaultAddr = payload.vault_addr
        if not payload.keys:
            raise ValueError("No Vault key path passed via --keys.")

        if not vaultAddr:
            vaultAddr = os.getenv("VAULT_ADDR")

        if not vaultAddr:
            raise ValueError("No Vault address passed via --vault-addr.")

        key_path = Path(payload.keys).expanduser()
        if not key_path.is_file():
            raise FileNotFoundError(f"Path {key_path} is not a file.")

        key_content = setup_vault_keys(vaultAddr, key_path)
        if payload.no_import:
            key_content = f"# NO-IMPORT\n{key_content}"

        messages = [f"Exporting Vault key from {key_path}"]
        return key_content, messages

    def import_key(
        self, key_content: str, confirmed: bool = False
    ) -> tuple[list[str], list[str]]:
        currentPathVaultFile = Path.cwd() / "vault_key.txt"
        messages: list[str] = []
        errors: list[str] = []

        if currentPathVaultFile.exists() and not confirmed:
            return (
                ["A 'vault_key.txt' file already exists in the current directory."],
                ["Confirmation needed to overwrite 'vault_key.txt'."],
            )

        try:
            with currentPathVaultFile.open("w") as f:
                _ = f.write(key_content)
            messages.append("Vault key imported successfully to 'vault_key.txt'.")
        except Exception as e:
            errors.append(f"Error importing Vault key: {str(e)}")
            return errors, []

        return errors, []

    def parse_key_content(
        self, key_content: str, provider_name: str
    ) -> tuple[str, str, str]:
        if not key_content:
            raise ValueError(f"Retrieved key from {provider_name} is empty.")

        vault_addr, vault_token = None, None
        for line in key_content.splitlines():
            if line.strip().startswith("# Vault Address:"):
                vault_addr = line.split("::", 1)[1].strip()
            if line.strip().startswith("Vault Key:"):
                vault_token = line.split(":", 1)[1].strip()

        if not vault_addr or not vault_token:
            raise ValueError(
                f"Could not extract both Vault address and token from {provider_name} item."
            )

        return vault_addr, vault_token, key_content

    @contextmanager
    def ephemeral_key_context(
        self, pub_key: str, sec_key: str, parsed_key_content: str
    ) -> Iterator[EphemeralEnvironment]:
        import os
        import platform
        import tempfile

        from ..utils import mac_ram_disk, setup_pipe

        vault_addr, vault_token = pub_key, sec_key

        if not vault_addr or not vault_token:
            yield {"env": {}, "prefix": "", "pass_fds": []}
            return

        r_addr = setup_pipe(vault_addr)
        fds_to_pass = [r_addr]
        is_mac = platform.system() == "Darwin"

        if is_mac:
            from contextlib import ExitStack

            with ExitStack() as stack:
                try:
                    ram_dir = stack.enter_context(mac_ram_disk())
                    temp_dir_name = stack.enter_context(
                        tempfile.TemporaryDirectory(dir=ram_dir, prefix="chaos-vault-")
                    )
                    temp_path = Path(temp_dir_name)

                    token_file = temp_path / ".vault-token"
                    with os.fdopen(
                        os.open(token_file, os.O_WRONLY | os.O_CREAT, 0o600), "w"
                    ) as f:
                        _ = f.write(vault_token)
                except Exception as e:
                    os.close(r_addr)
                    raise RuntimeError(f"Failed to generate Vault home: {e}")

                gnupghome = {
                    "GNUPGHOME": str(
                        os.getenv("GNUPGHOME", str(os.getenv("HOME")) + "/.gnupg")
                    )
                }
                prefix = f"VAULT_ADDR=$(cat /dev/fd/{r_addr}) HOME={temp_path} GNUPGHOME={gnupghome['GNUPGHOME']} "
                try:
                    yield {"env": {}, "prefix": prefix, "pass_fds": fds_to_pass}
                finally:
                    os.close(r_addr)
        else:
            shm_dir = "/dev/shm"
            if not os.path.isdir(shm_dir) or not os.access(shm_dir, os.W_OK):
                os.close(r_addr)
                raise RuntimeError(
                    f"Shared memory directory {shm_dir} is not available. Cannot create ephemeral Vault home."
                )
            with tempfile.TemporaryDirectory(
                dir=shm_dir, prefix="chaos-vault-"
            ) as temp_dir_name:
                try:
                    temp_path = Path(temp_dir_name)

                    token_file = temp_path / ".vault-token"
                    with os.fdopen(
                        os.open(token_file, os.O_WRONLY | os.O_CREAT, 0o600), "w"
                    ) as f:
                        _ = f.write(vault_token)
                except Exception as e:
                    os.close(r_addr)
                    raise RuntimeError(f"Failed to generate Vault home: {e}")

                gnupghome = {
                    "GNUPGHOME": str(
                        os.getenv("GNUPGHOME", str(os.getenv("HOME")) + "/.gnupg")
                    )
                }
                prefix = f"VAULT_ADDR=$(cat /dev/fd/{r_addr}) HOME={temp_path} GNUPGHOME={gnupghome['GNUPGHOME']} "
                try:
                    yield {"env": {}, "prefix": prefix, "pass_fds": fds_to_pass}
                finally:
                    os.close(r_addr)
