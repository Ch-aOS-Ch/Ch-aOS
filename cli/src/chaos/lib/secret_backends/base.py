from abc import ABC, abstractmethod
from contextlib import contextmanager
import shlex
import subprocess

class SecretBackend(ABC):
    """
    Abstract base class for secret backends.

    Base operations for managing secrets.
    """

    def __init__(self, args, global_config: dict):
        self.args = args
        self.config = global_config

    @abstractmethod
    @contextmanager
    def setupEphemeralEnv(self) -> dict:
        """
        Context manager to set up an ephemeral environment for SOPS.

        Args:
            secrets_file_override (str): Path to override the default secrets file.
            sops_file_override (str): Path to override the default SOPS file.
        """
        pass

    @abstractmethod
    def export_secrets(self) -> None:
        """
        Exporta chaves de arquivos locais para o secret backend.
        """
        raise NotImplementedError

    @abstractmethod
    def import_secrets(self) -> None:
        """
        Importa chaves do secret backend para arquivos locais.
        """
        raise NotImplementedError

    def edit(self, secrets_file: str, sops_file: str) -> None:
        """
        Edit secrets using SOPS.
        Args:
            secrets_file (str): Path to the secrets file.
            sops_file (str): Path to the SOPS file.
        """
        sops_command = ['sops', '--config', sops_file, secrets_file]
        with self.setupEphemeralEnv() as ctx:
            prefix = ctx["prefix"]
            pass_fds = ctx["pass_fds"]
            env = ctx["env"]
            cmd = shlex.join(sops_command)

            if prefix:
                cmd = f"{prefix} {cmd}"

            try:
                subprocess.run(
                    cmd,
                    check=True,
                    env=env,
                    pass_fds=pass_fds,
                    shell=True,
                )
            except subprocess.CalledProcessError as e:
                if e.returncode == 200:
                    return
                err = e.stderr.strip() if e.stderr else "No additional error information."
                raise RuntimeError(f"Error running SOPS edit command: {err}") from e

    def decrypt(self, secrets_file: str, sops_file: str) -> str:
        """
        Decrypt secrets using SOPS.
        Args:
            secrets_file (str): Path to the secrets file.
            sops_file (str): Path to the SOPS file.
        returns:
            str: Decrypted secrets content.
        """
        sops_command = ['sops', '--config', sops_file, '-d', secrets_file]
        result = self._run_sops_command(sops_command).stdout
        return result

    def _run_sops_command(self, command: list[str]) -> subprocess.CompletedProcess:
        """
        Run a SOPS command in a subprocess.
        Args:
            command (list): List of command arguments to run.
        returns:
            subprocess.CompletedProcess: The result of the subprocess execution.
        """
        try:
            with self.setupEphemeralEnv() as ctx:
                prefix = ctx["prefix"]
                pass_fds = ctx["pass_fds"]
                env = ctx["env"]

                cmd = shlex.join(command)
                if prefix:
                    cmd = f"{prefix} {cmd}"

                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=True,
                    env=env,
                    pass_fds=pass_fds,
                    shell=True,
                )
                return result
        except subprocess.CalledProcessError as e:
            err = e.stderr.strip() if e.stderr else "No additional error information."
            raise RuntimeError(f"Error running SOPS command: {err}") from e

