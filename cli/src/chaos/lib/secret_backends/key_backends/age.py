from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Iterator

from chaos.lib.secret_backends.crypto import extract_age_keys, is_valid_age_key
from chaos.lib.secret_backends.key_backends.backend import KeyBackend

if TYPE_CHECKING:
    from typing import TypedDict

    from chaos.lib.args.dataclasses import SecretsExportPayload, SecretsRotatePayload

    class EphemeralEnvironment(TypedDict):
        env: dict[str, str]
        prefix: str
        pass_fds: list[int]


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
            raise ValueError("No age key path passed via --key-file.")

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

        if payload.no_import:
            key_content = f"# NO-IMPORT\n{key_content}"

        messages = [f"Exporting age public key: {pubkey}"]
        return key_content, messages

    def import_key(
        self, key_content: str, confirmed: bool = False
    ) -> tuple[list[str], list[str]]:
        currentPathAgeFile = Path.cwd() / "keys.txt"
        messages: list[str] = []
        errors: list[str] = []

        if currentPathAgeFile.exists() and not confirmed:
            return (
                ["A 'keys.txt' file already exists in the current directory."],
                ["Confirmation needed to overwrite 'keys.txt'."],
            )

        try:
            with currentPathAgeFile.open("w") as f:
                sanitized_content = "\n".join(
                    line.lstrip() for line in key_content.splitlines()
                )
                _ = f.write(sanitized_content)
                if not sanitized_content.endswith("\n"):
                    _ = f.write("\n")
            messages.append("Age key imported successfully to 'keys.txt'.")
        except Exception as e:
            errors.append(f"Error importing age key: {str(e)}")
            return errors, []

        return errors, messages

    def parse_key_content(
        self, key_content: str, provider_name: str
    ) -> tuple[str, str, str]:
        if not key_content:
            raise ValueError(f"Retrieved key from {provider_name} is empty.")

        sanitized_key_content = ""
        for line in key_content.splitlines():
            if line.startswith(" ") or line.startswith("\t"):
                line = line.lstrip()
            sanitized_key_content += line + "\n"

        pubKey, secKey = extract_age_keys(key_content)

        if not pubKey:
            raise ValueError(
                f"Could not find a public key in the secret from {provider_name}. Expected a line starting with '# public key:'."
            )
        if not secKey:
            raise ValueError(
                f"Could not find a secret key in the secret from {provider_name}. Expected a line starting with 'AGE-SECRET-KEY-'."
            )

        return pubKey, secKey, sanitized_key_content

    @contextmanager
    def ephemeral_key_context(
        self, pub_key: str, sec_key: str, parsed_key_content: str
    ) -> Iterator[EphemeralEnvironment]:
        import os

        from ..utils import setup_pipe

        if not parsed_key_content:
            yield {"env": {}, "prefix": "", "pass_fds": []}
            return
        sanitized_content = "\n".join(
            line.lstrip() for line in parsed_key_content.splitlines()
        )
        final_content = self._conc_age_keys(sanitized_content)

        r_age = setup_pipe(final_content)
        prefix = f"SOPS_AGE_KEY_FILE=/dev/fd/{r_age} "
        fds_to_pass = [r_age]

        try:
            yield {"env": {}, "prefix": prefix, "pass_fds": fds_to_pass}
        finally:
            os.close(r_age)

    @staticmethod
    def _conc_age_keys(secKey: str) -> str:
        """Concatenates existing Age keys from the environment with a new secret key.

        Reads keys from the SOPS_AGE_KEY_FILE environment variable (if set) and appends
        the provided key, returning the combined string.

        Args:
            secKey (str): The new secret age key to append.

        Returns:
            str: The combined Age keys.
        """
        import os

        sops_file_env = os.getenv("SOPS_AGE_KEY_FILE")
        if not sops_file_env or not Path(sops_file_env).exists():
            return secKey

        with open(sops_file_env, "r") as f:
            existing_keys_content = f.read()

        concResult = existing_keys_content.strip() + "\n" + secKey

        return concResult
