import subprocess
from typing import TYPE_CHECKING

from chaos.lib.secret_backends.crypto import extract_gpg_keys, is_valid_fp, pgp_exists
from chaos.lib.secret_backends.key_backends.backend import KeyBackend
from chaos.lib.utils import checkDep

if TYPE_CHECKING:
    from chaos.lib.args.dataclasses import SecretsExportPayload, SecretsRotatePayload


class PgpBackend(KeyBackend):
    @property
    def key_type(self) -> str:
        return "pgp"

    def validate_for_add(
        self, keys: list[str], payload: SecretsRotatePayload
    ) -> tuple[set[str], list[str], list[str]]:
        server = payload.pgp_server
        valids: set[str] = set()
        errors: list[str] = []
        messages: list[str] = []
        for key in keys:
            clean_key = key.replace(" ", "")
            if len(clean_key) < 40:
                errors.append(f"Unsafe PGP key fingerprint: {key}. Skipping.")
                errors.append(
                    "To list your GPG keys, run: gpg --list-secret-keys --keyid-format LONG"
                )
                continue

            if not is_valid_fp(clean_key):
                errors.append(f"Invalid PGP fingerprint: {key}. Skipping.")
                errors.append(
                    "To list your GPG keys, run: gpg --list-secret-keys --keyid-format LONG"
                )
                continue

            if not pgp_exists(clean_key):
                errors.append(f"PGP fingerprint {key} does not exist locally.")
                if not server:
                    errors.append(
                        f"PGP fingerprint {key} does not exist locally and no server was passed. Skipping"
                    )
                    errors.append(
                        "To list your GPG keys, run: gpg --list-secret-keys --keyid-format LONG"
                    )
                    continue
                try:
                    command_message = subprocess.run(
                        ["gpg", "--keyserver", server, "--recv-keys", clean_key],
                        check=True,
                        capture_output=True,
                        text=True,
                    ).stdout
                    messages.append(command_message)
                    messages.append(
                        f"Fingerprint {key} was successfully imported from {server}"
                    )
                except subprocess.SubprocessError as e:
                    errors.append(
                        f"Could not import {key} from {server}: {e}.\nSkipping."
                    )
                    continue
            valids.add(clean_key)
        return valids, messages, errors

    def validate_for_rem(
        self, keys: list[str], payload: SecretsRotatePayload
    ) -> tuple[set[str], list[str], list[str]]:
        clean_keys = set()
        errors = []
        for key in keys:
            clean_key = key.replace(" ", "")
            if not is_valid_fp(clean_key):
                errors.append(f"Invalid PGP fingerprint: {key}. Skipping.")
                continue
            clean_keys.add(clean_key)
        return clean_keys, [], errors

    def prepare_export_content(
        self, payload: SecretsExportPayload
    ) -> tuple[str, list[str]]:
        fingerprints = payload.fingerprints
        if not fingerprints:
            raise ValueError(
                "At least one GPG fingerprint is required via --fingerprints."
            )
        if not checkDep("gpg"):
            raise EnvironmentError(
                "The 'gpg' CLI tool is required but not found in PATH."
            )

        key_content = extract_gpg_keys(fingerprints)
        messages = [f"Exporting GPG keys for fingerprints: {', '.join(fingerprints)}"]
        return key_content, messages
