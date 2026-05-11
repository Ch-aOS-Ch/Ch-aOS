from pathlib import Path
from typing import TYPE_CHECKING

from chaos.lib.secret_backends.key_backends.backend import KeyBackend
from chaos.lib.secret_backends.utils import _is_valid_vault_key, setup_vault_keys

if TYPE_CHECKING:
    from chaos.lib.args.dataclasses import SecretsExportPayload, SecretsRotatePayload


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
        vaultAddr = payload.vault_addr
        if not payload.keys:
            raise ValueError("No Vault key path passed via --keys.")
        if not vaultAddr:
            raise ValueError("No Vault address passed via --vault-addr.")

        key_path = Path(payload.keys).expanduser()
        if not key_path.is_file():
            raise FileNotFoundError(f"Path {key_path} is not a file.")

        key_content = setup_vault_keys(vaultAddr, key_path)
        messages = [f"Exporting Vault key from {key_path}"]
        return key_content, messages
