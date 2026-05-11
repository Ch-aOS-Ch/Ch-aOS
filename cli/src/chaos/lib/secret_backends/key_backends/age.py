from pathlib import Path
from typing import TYPE_CHECKING

from chaos.lib.secret_backends.crypto import extract_age_keys, is_valid_age_key
from chaos.lib.secret_backends.key_backends.backend import KeyBackend

if TYPE_CHECKING:
    from chaos.lib.args.dataclasses import SecretsExportPayload, SecretsRotatePayload


class AgeBackend(KeyBackend):
    @property
    def key_type(self) -> str:
        return "age"

    def validate_for_add(
        self, keys: list[str], payload: SecretsRotatePayload
    ) -> tuple[set[str], list[str], list[str]]:
        valids: set[str] = set()
        errors: list[str] = []
        for key in keys:
            clean_key = key.strip()
            if not is_valid_age_key(clean_key):
                errors.append(f"Invalid age key: {key}. Skipping.")
                errors.append("To get your age public key:")
                errors.append(
                    "  - From a native age private key file (e.g., ~/.config/chaos/keys.txt): age-keygen -y ~/.config/chaos/keys.txt"
                )
                errors.append(
                    "  - From a SSH public key (e.g., ~/.ssh/id_rsa.pub, requires ssh-to-age): ssh-to-age -i ~/.ssh/id_rsa.pub"
                )
                continue
            valids.add(clean_key)
        return valids, [], errors

    def validate_for_rem(
        self, keys: list[str], payload: SecretsRotatePayload
    ) -> tuple[set[str], list[str], list[str]]:
        clean_keys = {key.strip() for key in keys}
        return clean_keys, [], []

    def prepare_export_content(
        self, payload: SecretsExportPayload
    ) -> tuple[str, list[str]]:
        if not payload.keys:
            raise ValueError("No age key path passed via --keys.")

        key_path = Path(payload.keys).expanduser()
        if not key_path.is_file():
            raise FileNotFoundError(f"Path {key_path} is not a file.")

        with open(key_path, "r") as f:
            key_content = f.read()

        pubkey, seckey = extract_age_keys(key_content)

        if not pubkey:
            raise ValueError(
                "Could not find a public key in the provided age key file. Expected a line starting with '# public key:'."
            )
        if not seckey:
            raise ValueError(
                "Could not find a secret key in the provided age key file. Expected a line starting with 'AGE-SECRET-KEY-'."
            )

        messages = [f"Exporting age public key: {pubkey}"]
        return key_content, messages
