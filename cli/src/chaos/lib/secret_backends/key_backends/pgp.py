import subprocess
from contextlib import contextmanager
from typing import TYPE_CHECKING, Iterator

from chaos.lib.secret_backends.crypto import (
    decompress,
    extract_gpg_keys,
    is_valid_fp,
    pgp_exists,
)
from chaos.lib.secret_backends.key_backends.backend import KeyBackend
from chaos.lib.utils import checkDep

if TYPE_CHECKING:
    from typing import TypedDict

    from chaos.lib.args.dataclasses import SecretsExportPayload, SecretsRotatePayload

    class EphemeralEnvironment(TypedDict):
        env: dict[str, str]
        prefix: str
        pass_fds: list[int]


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
        if payload.no_import:
            key_content = f"# NO-IMPORT\n{key_content}"

        messages = [f"Exporting GPG keys for fingerprints: {', '.join(fingerprints)}"]
        return key_content, messages

    def import_key(
        self, key_content: str, confirmed: bool = False
    ) -> tuple[list[str], list[str]]:
        decompressedKey = decompress(key_content)
        messages: list[str] = []
        errors: list[str] = []

        try:
            import_cmd = ["gpg", "--batch", "--import"]
            _ = subprocess.run(
                import_cmd,
                input=decompressedKey,
                check=True,
                capture_output=True,
            )
            messages.append(
                "GPG key imported into your local GPG keyring successfully."
            )
        except subprocess.CalledProcessError as e:
            errors.append(f"Error importing GPG key: {e.stderr.decode().strip()}")  # pyright: ignore[reportAny]
            return errors, messages

        return errors, messages

    def parse_key_content(
        self, key_content: str, provider_name: str
    ) -> tuple[str, str, str]:
        if not key_content:
            raise ValueError(f"Retrieved GPG key from {provider_name} is empty.")

        fingerprints = ""
        for line in key_content.splitlines():
            if line.strip().startswith("# fingerprints:"):
                fingerprints = line.split(":", 1)[1].strip()
                break

        if "-----BEGIN PGP PRIVATE KEY BLOCK-----" not in key_content:
            raise ValueError(
                f"The secret read from {provider_name} does not appear to be a GPG private key block."
            )

        noHeadersSecKey = key_content.split("-----BEGIN PGP PRIVATE KEY BLOCK-----", 1)[
            1
        ].rsplit("-----END PGP PRIVATE KEY BLOCK-----", 1)[0]
        secKey = noHeadersSecKey.strip()

        return fingerprints, secKey, key_content

    @contextmanager
    def ephemeral_key_context(
        self, pub_key: str, sec_key: str, parsed_key_content: str
    ) -> Iterator[EphemeralEnvironment]:
        import os
        import platform
        import tempfile
        import time
        from pathlib import Path

        from ..crypto import decompress
        from ..utils import mac_ram_disk, setup_gpg_keys

        key_bytes = decompress(parsed_key_content)

        if not key_bytes:
            yield {"env": {}, "prefix": "", "pass_fds": []}
            return

        is_mac = platform.system() == "Darwin"

        if is_mac:
            from contextlib import ExitStack

            with ExitStack() as stack:
                try:
                    ram_dir = stack.enter_context(mac_ram_disk())
                    temp_dir_name = stack.enter_context(
                        tempfile.TemporaryDirectory(
                            dir=ram_dir, prefix=f"chaos-gpg-{time.time_ns()}-"
                        )
                    )

                    temp_path = Path(temp_dir_name)
                    setup_gpg_keys(temp_path)
                except Exception as e:
                    raise RuntimeError(f"Failed to generate GPG home: {e}")

                try:
                    _ = subprocess.run(
                        ["gpg", "--batch", "--import"],
                        input=key_bytes,
                        env={"GNUPGHOME": str(temp_path)},
                        check=True,
                        capture_output=True,
                    )

                except subprocess.CalledProcessError as e:
                    err_msg = (
                        e.stderr.decode() if getattr(e, "stderr", None) else str(e)
                    )
                    raise RuntimeError(f"Failed to import GPG key: {err_msg}")

                yield {
                    "env": {"GNUPGHOME": str(temp_path)},
                    "prefix": "",
                    "pass_fds": [],
                }
        else:
            shm_dir = "/dev/shm" if os.path.exists("/dev/shm") else None
            with tempfile.TemporaryDirectory(
                dir=shm_dir, prefix=f"chaos-gpg-{time.time_ns()}"
            ) as temp_dir_name:
                try:
                    temp_path = Path(temp_dir_name)
                    setup_gpg_keys(temp_path)
                except Exception as e:
                    raise RuntimeError(f"Failed to generate GPG home: {e}")

                try:
                    _ = subprocess.run(
                        ["gpg", "--batch", "--import"],
                        input=key_bytes,
                        env={"GNUPGHOME": str(temp_path)},
                        check=True,
                        capture_output=True,
                    )
                except subprocess.CalledProcessError as e:
                    err_msg = (
                        e.stderr.decode() if getattr(e, "stderr", None) else str(e)
                    )
                    raise RuntimeError(f"Failed to import GPG key: {err_msg}")

                yield {
                    "env": {"GNUPGHOME": str(temp_path)},
                    "prefix": "",
                    "pass_fds": [],
                }
