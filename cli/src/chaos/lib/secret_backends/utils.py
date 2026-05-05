"""Utility functions for handling SOPS file operations, provider resolution, and decryption workflows."""

import os
import shutil
from pathlib import Path
from typing import TYPE_CHECKING, Union, cast

from ..args.dataclasses import (
    ProviderConfigPayload,
    SecretsContext,
    SecretsExportPayload,
    SecretsImportPayload,
)
from ..utils import validate_path
from .providers.base import Provider

if TYPE_CHECKING:
    from typing import Any

    from omegaconf import DictConfig, ListConfig

    from chaos.lib.args.dataclasses import SecretsRotatePayload


def _resolveProvider(
    context: SecretsContext, global_config: DictConfig
) -> Provider | None:
    """Resolves and returns the appropriate secret provider based on context and configuration.

    Args:
        context (SecretsContext): The contextual data governing the secret operations.
        global_config (dict | DictConfig): The global chaos configuration data.

    Returns:
        Provider | None: The resolved provider object, or None if no matching provider is found.
    """
    if context.provider_config and context.provider_config.provider is not None:
        context = _handle_provider_arg(context, global_config)

    return _getProvider(context, global_config)


def _getProvider(context: SecretsContext, global_config) -> Provider | None:
    """Returns the appropriate secret provider based on the command-line arguments.

    Searches through installed provider plugins and selects one matching the provided
    ephemeral provider arguments in the context.

    Args:
        context (SecretsContext): The secrets context containing ephemeral provider arguments.
        global_config (dict | DictConfig): The global chaos configuration data.

    Returns:
        Provider | None: The matching provider instance, or None if no provider matches.
    """
    from chaos.lib.utils import get_providerEps

    provider_eps = get_providerEps()

    if not provider_eps:
        return None

    ephemeral_flags = (
        context.provider_config.ephemeral_provider_args
        if context.provider_config
        else {}
    )

    for ep in provider_eps:
        ProviderClass = ep.load()
        providerFlag, _ = ProviderClass.get_cli_name()

        if providerFlag in ephemeral_flags and ephemeral_flags[providerFlag]:
            return ProviderClass(context, global_config)

    return None


def _getProviderByName(
    payload: Union[SecretsExportPayload, SecretsImportPayload], global_config
) -> Provider:
    """Retrieves a specific secret provider by its registered CLI name.

    Args:
        payload (Union[SecretsExportPayload, SecretsImportPayload]): The payload containing the requested provider_name.
        global_config (dict | DictConfig): The global chaos configuration.

    Returns:
        Provider: The matching provider instance.

    Raises:
        ValueError: If no secret providers are available or if the requested provider is not found.
        TypeError: If the found provider does not support the required operations.
    """
    from chaos.lib.utils import get_providerEps

    provider = None
    provider_eps = get_providerEps()
    if not provider_eps:
        raise ValueError("No secret providers available for exporting secrets.")

    for ep in provider_eps:
        ProviderClass = ep.load()
        _, providerCliName = ProviderClass.get_cli_name()
        if providerCliName == payload.provider_name:
            provider = ProviderClass(payload, global_config)

            if not isinstance(provider, Provider) or not hasattr(
                provider, "export_secrets"
            ):
                raise TypeError(
                    f"The provider '{providerCliName}' does not support exporting secrets."
                )
            break

    if not provider or provider is None:
        raise ValueError(f"No secret provider found for '{payload.provider_name}'.")
    return provider


def setup_gpg_keys(gnupghome) -> None:
    """Sets up a temporary GNUPGHOME directory to keep imported GPG keys ephemeral.

    Copies existing private keys and trustdb from the user's main GNUPGHOME (if present)
    to the temporary directory, and imports public keys so they are available in the ephemeral context.

    Args:
        gnupghome (Path | tempfile.TemporaryDirectory): The temporary directory path to configure.
    """
    import subprocess

    actualGnupgHome_path = Path(os.getenv("GNUPGHOME", str(Path.home() / ".gnupg")))
    temp_gnupg_path = Path(gnupghome.name)

    if not actualGnupgHome_path.exists():
        return

    srcPriv = actualGnupgHome_path / "private-keys-v1.d"
    detstPriv = temp_gnupg_path / "private-keys-v1.d"

    shutil.copytree(srcPriv, detstPriv, dirs_exist_ok=True)
    os.chmod(detstPriv, 0o700)

    pubKeyDump = temp_gnupg_path / "host_pubkeys.gpg"

    try:
        with open(pubKeyDump, "wb") as f:
            subprocess.run(
                ["gpg", "--export"], stdout=f, check=True, stderr=subprocess.DEVNULL
            )

    except subprocess.CalledProcessError:
        raise RuntimeError(
            "Failed to export GPG public keys from the existing GNUPGHOME."
        )

    temp_env = os.environ.copy()
    temp_env["GNUPGHOME"] = str(temp_gnupg_path)
    try:
        subprocess.run(
            ["gpg", "--batch", "--import", str(pubKeyDump)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env=temp_env,
        )
    except subprocess.CalledProcessError:
        return

    src_trust = actualGnupgHome_path / "trustdb.gpg"
    if src_trust.exists():
        shutil.copy2(src_trust, temp_gnupg_path / "trustdb.gpg")


def conc_age_keys(secKey: str) -> str:
    """Concatenates existing Age keys from the environment with a new secret key.

    Reads keys from the SOPS_AGE_KEY_FILE environment variable (if set) and appends
    the provided key, returning the combined string.

    Args:
        secKey (str): The new secret age key to append.

    Returns:
        str: The combined Age keys.
    """
    sops_file_env = os.getenv("SOPS_AGE_KEY_FILE")
    if not sops_file_env or not Path(sops_file_env).exists():
        return secKey

    with open(sops_file_env, "r") as f:
        existing_keys_content = f.read()

    concResult = existing_keys_content.strip() + "\n" + secKey

    return concResult


def setup_vault_keys(vaultAddr: str, keyPath: Path) -> str:
    """Reads and validates a Vault token for exporting.

    Constructs a formatted string containing the Vault address and token for storing in an external provider.

    Args:
        vaultAddr (str): The HashiCorp Vault server address.
        keyPath (Path): The file path containing the Vault token.

    Returns:
        str: The formatted key content string with address and token.

    Raises:
        EnvironmentError: If the 'vault' CLI tool is missing.
        ValueError: If the key format is invalid.
    """
    from chaos.lib.utils import checkDep

    if not checkDep("vault"):
        raise EnvironmentError(
            "The 'vault' CLI tool is required but not found in PATH."
        )
    with open(keyPath, "r") as f:
        key = f.read().strip()
    if not _is_valid_vault_key(key):
        raise ValueError("The provided Vault key does not appear to be valid.")
    if not key.startswith("hvs.") and not key.startswith("s."):
        raise ValueError(
            'The provided Vault key does not appear to be a valid HCP Vault URI (must start with "hvs." or "s.").'
        )

    key_content = f"""# Vault Address:: {vaultAddr}
Vault Key: {key}
"""
    return key_content


def setup_pipe(token: str) -> int:
    """Creates a Unix pipe to pass a token securely via a File Descriptor (FD).

    Args:
        token (str): The secret token string to pass into the pipe.

    Returns:
        int: The file descriptor (FD) number for the read end of the pipe.
    """
    r, w = os.pipe()
    os.write(w, token.encode())
    os.fchmod(w, 0o600)
    os.close(w)
    return r


def _is_valid_vault_key(key: str) -> tuple[bool, str]:
    """Checks if a Vault server URI is valid and reachable.

    Attempts to fetch the seal-status of the Vault server.

    Args:
        key (str): The Vault server URI to check.

    Returns:
        tuple[bool, str]: A tuple containing a boolean indicating validity, and a status message.
    """
    import requests
    import requests.exceptions

    try:
        url = f"{key.rstrip('/')}/v1/sys/seal-status"
        response = requests.get(url, timeout=5)

        try:
            seal_status = response.json()
        except ValueError:
            return (
                False,
                f"Vault URI '{key}' returned unexpected non-JSON data.",
            )

        if not seal_status:
            return (
                False,
                f"Vault URI '{key}' did not return a valid seal status or Vault server is unreachable.",
            )

        if "sealed" in seal_status:
            return (
                True,
                f"Valid vault URI. Server status: {seal_status['sealed']}.",
            )
        elif "data" in seal_status and "sealed" in seal_status["data"]:
            return (
                True,
                f"Valid vault URI. Server status: {seal_status['data']['sealed']}.",
            )
        else:
            return (
                False,
                f"Vault URI '{key}' is a reachable endpoint, but status check failed or returned unexpected data.",
            )
    except requests.exceptions.MissingSchema:
        return (
            False,
            f"Vault URI '{key}' is an invalid URL format. Missing schema (e.g., 'https://').",
        )
    except requests.exceptions.ConnectionError:
        return (
            False,
            f"Vault URI '{key}' is a valid URL format but unreachable. Check network connectivity or if the Vault server is running.",
        )
    except Exception as e:
        return (
            False,
            f"An unexpected error occurred while validating Vault URI '{key}': {e}",
        )


def get_sops_files(
    sops_file_override, secrets_file_override, team
) -> tuple[str, str, DictConfig]:
    """Gets the appropriate SOPS and secrets files based on overrides, team context, and global configuration.

    Args:
        sops_file_override (str | None): A path overriding the default SOPS configuration file.
        secrets_file_override (str | None): A path overriding the default secrets file.
        team (str | None): The team context (e.g., 'company.team.group').

    Returns:
        tuple[str, str, dict | DictConfig]: A tuple containing:
            - The path to the secrets file.
            - The path to the SOPS configuration file.
            - The global configuration mapping.

    Raises:
        ValueError: If the team string is malformed or if there are path traversal attempts.
        FileNotFoundError: If the specified team directory or override files are not found.
    """
    from pathlib import Path

    from omegaconf import DictConfig, OmegaConf

    secretsFile = secrets_file_override
    sopsFile = sops_file_override

    CONFIG_DIR = os.getenv("CHAOS_CONFIG_DIR", Path.home() / ".config" / "chaos")
    CONFIG_FILE_PATH = os.path.join(CONFIG_DIR, "config.yml")

    global_config = None
    if os.path.exists(CONFIG_FILE_PATH):
        global_config = OmegaConf.load(CONFIG_FILE_PATH) or OmegaConf.create()

    global_config = (
        cast(DictConfig, global_config) if global_config else OmegaConf.create()
    )

    if team:
        if "." not in team:
            raise ValueError("Must set a company for your team. (company.team.group)")

        parts = team.split(".")
        company = parts[0]
        team_name = parts[1]
        group = parts[2] if len(parts) > 2 else None

        if not company:
            raise ValueError(f"Company name cannot be empty in '{team}'.")
        if not team_name:
            raise ValueError(f"Team name cannot be empty in '{team}'.")
        if group is not None and not group:
            raise ValueError(f"Group name cannot be empty in '{team}'.")

        if ".." in company or company.startswith("/"):
            raise ValueError(f"Invalid company name '{company}'.")

        if ".." in team_name or team_name.startswith("/"):
            raise ValueError(f"Invalid team name '{team_name}'.")

        teamPath = Path(
            os.getenv(
                "CHAOS_TEAMS_DIR",
                Path.home()
                / ".local"
                / "share"
                / "chaos"
                / "teams"
                / company
                / team_name,
            )
        )

        if teamPath.exists():
            sopsFile = teamPath / "sops-config.yml"
            default_secrets_filename = "secrets/secrets.yml"
            if group:
                groupPath = f"secrets/{group}"
                if not (teamPath / groupPath).exists():
                    raise FileNotFoundError(
                        f"Group directory for '{group}' not found at {teamPath / groupPath}."
                    )
                default_secrets_filename = f"{groupPath}/secrets.yml"
            secretsFile = teamPath / default_secrets_filename

            if sops_file_override:
                if ".." in sops_file_override or sops_file_override.startswith("/"):
                    raise ValueError(
                        f"Invalid team sops file override '{sops_file_override}'."
                    )
                override_path = (teamPath / sops_file_override).resolve(strict=False)
                if not str(override_path).startswith(str(teamPath)):
                    raise ValueError("Path traversal detected.")
                sopsFile = teamPath / sops_file_override

            if secrets_file_override:
                if ".." in secrets_file_override or secrets_file_override.startswith(
                    "/"
                ):
                    raise ValueError(
                        f"Invalid team secrets file override '{secrets_file_override}'."
                    )
                if not group:
                    secretsFile = teamPath / "secrets" / secrets_file_override
                else:
                    secretsFile = teamPath / "secrets" / group / secrets_file_override

            return str(secretsFile), str(sopsFile), global_config
        else:
            raise FileNotFoundError(
                f"Team directory for '{team_name}' not found at {teamPath}."
            )

    global_config = cast(DictConfig, global_config)
    if not secretsFile:
        secretsFile = global_config.get("secrets_file")
    if not sopsFile:
        sopsFile = global_config.get("sops_file")

    if not secretsFile or not sopsFile:
        ChOboloPath = global_config.get("chobolo_file", None)
        if ChOboloPath:
            try:
                ChObolo = OmegaConf.load(ChOboloPath)
                ChObolo = cast(DictConfig, ChObolo)
                secrets_config = ChObolo.get("secrets", None)
                if secrets_config:
                    if not secretsFile:
                        secretsFile = secrets_config.get("sec_file")
                    if not sopsFile:
                        sopsFile = secrets_config.get("sec_sops")
            except Exception:
                pass  # If the chobolo file is malformed or missing, we can ignore it and rely on other config sources or defaults.

    validate_path(secretsFile)
    validate_path(sopsFile)

    return secretsFile, sopsFile, global_config


def flatten(items: list | ListConfig) -> Any:
    """Turns a concatenated or nested list into a single flat generator.

    Args:
        items (Iterable): An iterable of items or nested lists.

    Yields:
        Any: Unpacked items from the nested iterables.
    """
    from omegaconf import ListConfig

    for i in items:
        if isinstance(i, (list, ListConfig)):
            yield from flatten(i)
        else:
            yield i


def _save_to_config(backend: str, data_to_save: dict) -> None:
    """Saves provider-specific data to the chaos global configuration file.

    Updates the '~/.config/chaos/config.yml' file with new settings under the
    specified backend key.

    Args:
        backend (str): The name of the provider backend (e.g., 'bw', 'bws').
        data_to_save (dict): A dictionary of key-value pairs to store.
    """
    from omegaconf import OmegaConf

    config_path = Path.home() / ".config/chaos/config.yml"
    config = OmegaConf.load(config_path) if config_path.exists() else OmegaConf.create()

    if "secret_providers" not in config:
        config.secret_providers = OmegaConf.create()

    if backend not in config.secret_providers:
        config.secret_providers[backend] = OmegaConf.create()

    for key, value in data_to_save.items():
        if value:
            config.secret_providers[backend][key] = value

    OmegaConf.save(config, config_path)


def handleUpdateAllSecrets(context: SecretsContext) -> tuple[list[str], list[str]]:
    """Updates encryption keys for all related secret files and rambles.

    Iterates over the main secrets file and any associated ramble files to apply
    `sops updatekeys`, ensuring all files reflect the current key configuration.

    Args:
        context (SecretsContext): The execution context defining file overrides and team structure.

    Returns:
        tuple[list[str], list[str]]: A tuple containing a list of informational messages
            and a list of error messages encountered during the update.
    """
    import subprocess

    from omegaconf import OmegaConf

    from chaos.lib.secret_backends.crypto import check_vault_auth, is_vault_in_use

    messages = ["\nStarting key update for all secret files..."]
    errors: list[str] = []

    main_secrets_file, sops_file_path, global_config = get_sops_files(
        context.sops_file_override, context.secrets_file_override, context.team
    )

    if is_vault_in_use(sops_file_path):
        is_authed, message = check_vault_auth()
        if not is_authed:
            errors.append(message)
            return messages, errors

    if not sops_file_path:
        messages.append(
            "Warning: No sops config file found for main secrets. Skipping main secrets file update."
        )
    elif main_secrets_file and Path(main_secrets_file).exists():
        try:
            data = OmegaConf.load(main_secrets_file)
            if "sops" in data:
                messages.append(
                    f"Updating keys for main secrets file: {main_secrets_file}"
                )

                provider = _resolveProvider(context, global_config)

                if provider:
                    provider.updatekeys(main_secrets_file, sops_file_path)
                else:
                    subprocess.run(
                        [
                            "sops",
                            "--config",
                            sops_file_path,
                            "updatekeys",
                            "-y",
                            main_secrets_file,
                        ],
                        check=True,
                        text=True,
                        capture_output=True,
                    )
                messages.append("Keys updated successfully.")
        except subprocess.CalledProcessError as e:
            errors.append(f"Failed to update keys for {main_secrets_file}: {e.stderr}")
        except Exception as e:
            errors.append(f"Could not process file {main_secrets_file}: {e}")
    else:
        messages.append("Main secrets file not found or not configured. Skipping.")

    messages.append("\nUpdating ramble files...")
    from chaos.lib.args.dataclasses import RambleUpdateEncryptPayload
    from chaos.lib.ramble import handleUpdateEncryptRamble

    payload = RambleUpdateEncryptPayload(context=context)
    result = handleUpdateEncryptRamble(payload)

    if result.message:
        messages.extend(result.message)
    if result.error:
        errors.extend(result.error)

    return messages, errors


def _handle_provider_arg(context: SecretsContext, config) -> SecretsContext:
    """Resolves dynamic provider arguments based on global configuration.

    Processes the requested provider backend name, looks up its stored configuration
    (like item IDs or URLs), and constructs a new context with the resolved ephemeral arguments.

    Args:
        context (SecretsContext): The initial secrets context containing raw provider requests.
        config (dict | DictConfig): The global configuration mapping containing stored provider data.

    Returns:
        SecretsContext: A new context object populated with the resolved provider arguments.

    Raises:
        FileNotFoundError: If the global config lacks the 'secret_providers' section.
        ValueError: If the provider format is invalid, missing, or unsupported.
    """
    from chaos.lib.utils import get_providerEps

    if not context.provider_config or context.provider_config.provider is None:
        return context

    if not config or "secret_providers" not in config:
        raise FileNotFoundError(
            "Could not find 'secret_providers' in ~/.config/chaos/config.yml."
        )

    providers_config = config.secret_providers
    provider_name = context.provider_config.provider

    if provider_name == "default":
        provider_name = providers_config.get("default")
        if not provider_name:
            raise ValueError(
                "A default provider is requested, but 'default' is not set in secret_providers config."
            )

    if "." not in provider_name:
        raise ValueError(
            f"Invalid provider format: '{provider_name}'. Expected 'backend.key_type' (e.g., 'bw.age')."
        )

    backend, key_type = provider_name.split(".", 1)

    if backend not in providers_config:
        raise ValueError(
            f"Provider backend '{backend}' not found in secret_providers config."
        )

    backend_config = providers_config[backend]
    id_key = f"{key_type}_id"
    url_key = f"{key_type}_url"

    provider_eps = get_providerEps()
    if not provider_eps:
        raise ValueError(
            "No secret providers found. Please ensure that at least one provider plugin is installed."
        )

    provider_found = False
    new_ephemeral_args = context.provider_config.ephemeral_provider_args.copy()

    for provider_ep in provider_eps:
        ProviderClass = provider_ep.load()
        providerFlag, providerName = ProviderClass.get_cli_name()

        if providerName == backend:
            value_to_set = None
            if id_key in backend_config:
                item_id = backend_config[id_key]
                value_to_set = (item_id, key_type)
            elif url_key in backend_config:
                item_url = backend_config[url_key]
                value_to_set = (item_url, key_type)
            else:
                raise ValueError(
                    f"Could not find '{id_key}' or '{url_key}' in backend '{backend}' config for provider '{provider_name}'."
                )

            new_ephemeral_args[providerFlag] = value_to_set
            provider_found = True
            break

    if not provider_found:
        raise ValueError(
            f"No installed provider plugin matched the backend '{backend}'."
        )

    new_provider_config = ProviderConfigPayload(
        provider=None, ephemeral_provider_args=new_ephemeral_args
    )
    return SecretsContext(
        team=context.team,
        sops_file_override=context.sops_file_override,
        secrets_file_override=context.secrets_file_override,
        provider_config=new_provider_config,
        i_know_what_im_doing=context.i_know_what_im_doing,
    )


def _generic_handle_add(
    key_type: str,
    payload: SecretsRotatePayload,
    sops_file_override: str,
    valids: set[str],
) -> tuple[list[str], list[str]]:
    """Generic handler for adding keys to a SOPS configuration file.

    Updates specific creation rules within the SOPS configuration by appending
    new keys to the designated key groups. Optionally creates new key groups if requested.

    Args:
        key_type (str): The type of key being added (e.g., 'pgp', 'age', 'vault').
        payload (SecretsRotatePayload): The rotation payload containing rule indices and creation flags.
        sops_file_override (str): The path to the SOPS configuration file.
        valids (set): A set of validated keys to add.

    Returns:
        tuple[list[str], list[str]]: A tuple with informational messages and error messages.
    """
    from omegaconf import DictConfig, OmegaConf

    messages: list[str] = []
    errors: list[str] = []
    if not valids:
        messages.append("No valid keys. Returning.")
        return messages, errors

    try:
        create = payload.create
        config_data = OmegaConf.load(sops_file_override)
        config_data = cast(DictConfig, config_data)
        creation_rules = config_data.get("creation_rules", [])
        if not creation_rules:
            errors.append(
                f"No 'creation_rules' found in {sops_file_override}. Cannot add keys."
            )
            return messages, errors

        rule_index = payload.index
        rules_to_process = creation_rules
        if rule_index is not None:
            if not (0 <= rule_index < len(creation_rules)):
                errors.append(
                    f"Invalid rule index {rule_index}. Must be between 0 and {len(creation_rules) - 1}."
                )
                return messages, errors
            rules_to_process = [creation_rules[rule_index]]

        if not create:
            total_added_keys = set()
            for rule in rules_to_process:
                for key_group in rule.get("key_groups", []):
                    if (
                        key_type in key_group
                        and getattr(key_group, key_type) is not None
                    ):
                        existing_keys = list(flatten(getattr(key_group, key_type)))

                        keys_to_write = list(existing_keys)
                        current_keys_set = set(keys_to_write)
                        for key_to_add in valids:
                            if key_to_add not in current_keys_set:
                                keys_to_write.append(key_to_add)
                                total_added_keys.add(key_to_add)

                        setattr(key_group, key_type, keys_to_write)

            if not total_added_keys:
                messages.append(
                    f"All provided keys are already in the relevant sops config '{key_type}' sections, or no '{key_type}' sections were found. No changes made."
                )
                return messages, errors

            OmegaConf.save(config_data, sops_file_override)
            messages.append(
                f"Successfully updated sops config! New keys added: {list(total_added_keys)}"
            )
        else:
            for rule in rules_to_process:
                new_group = OmegaConf.create({key_type: list(valids)})
                if "key_groups" in rule and rule.key_groups is not None:
                    rule.key_groups.append(new_group)
                else:
                    rule.key_groups = [new_group]

            OmegaConf.save(config_data, sops_file_override)
            messages.append(
                f"Successfully updated sops config! New {key_type.upper()} key group created with keys: {list(valids)}"
            )

    except Exception as e:
        errors.append(
            f"Failed to load or save sops config file {sops_file_override}: {e}"
        )
    return messages, errors


def _generic_handle_rem(
    key_type: str,
    payload: SecretsRotatePayload,
    sops_file_override: str,
    keys_to_remove: set[str],
) -> tuple[list[str], list[str]]:
    """Generic handler for removing keys from a SOPS configuration file.

    Scans creation rules and filters out the specified keys from the relevant key groups.
    Empty key groups are removed entirely.

    Args:
        key_type (str): The type of key being removed (e.g., 'pgp', 'age', 'vault').
        payload (SecretsRotatePayload): The rotation payload containing context and target rule index.
        sops_file_override (str): The path to the SOPS configuration file.
        keys_to_remove (set): A set of keys to strip out of the configuration.

    Returns:
        tuple[list[str], list[str]]: A tuple with informational messages and error messages.
    """
    from omegaconf import DictConfig, OmegaConf

    messages: list[str] = []
    errors: list[str] = []
    rule_index = payload.index
    ikwid = payload.context.i_know_what_im_doing

    if not keys_to_remove:
        messages.append("No keys to remove. Exiting.")
        return messages, errors

    try:
        config_data = OmegaConf.load(sops_file_override)
        config_data = cast(DictConfig, config_data)
        creation_rules = config_data.get("creation_rules", [])
        if not creation_rules:
            errors.append(
                "No 'creation_rules' found in the sops config. Nothing to do."
            )
            return messages, errors

        if not ikwid:
            msgs = ["Keys to remove:"]
            for key in keys_to_remove:
                msgs.append(f"  {key}")
            messages.append("\n".join(msgs))

        rules_to_process = creation_rules
        if rule_index is not None:
            if not (0 <= rule_index < len(creation_rules)):
                errors.append(
                    f"Invalid rule index {rule_index}. Must be between 0 and {len(creation_rules) - 1}."
                )
                return messages, errors
            rules_to_process = [creation_rules[rule_index]]

        for rule in rules_to_process:
            if rule.get("key_groups"):
                for i in range(len(rule.key_groups) - 1, -1, -1):
                    key_group = rule.key_groups[i]
                    if (
                        key_type in key_group
                        and getattr(key_group, key_type) is not None
                    ):
                        updated_keys = [
                            k
                            for k in flatten(getattr(key_group, key_type))
                            if k not in keys_to_remove
                        ]
                        if updated_keys:
                            setattr(key_group, key_type, updated_keys)
                        else:
                            delattr(key_group, key_type)

                    if not key_group:
                        del rule.key_groups[i]

        OmegaConf.save(config_data, sops_file_override)
        messages.append(
            f"Successfully updated sops config! Keys removed: {list(keys_to_remove)}"
        )

    except Exception as e:
        errors.append(f"Failed to update sops config file: {e}")
    return messages, errors


def decrypt_secrets(
    secrets_file: str, sops_file: str, config, context: SecretsContext
) -> str:
    """Decrypts a secrets file using SOPS and the active environment context.

    Delegates decryption to a resolved secret provider plugin if available;
    otherwise, it falls back to directly invoking the SOPS CLI tool.

    Args:
        secrets_file (str): The path to the encrypted secrets file.
        sops_file (str): The path to the SOPS configuration file.
        config (dict | DictConfig): The global chaos configuration.
        context (SecretsContext): The secrets context detailing ephemeral settings.

    Returns:
        str: The raw decrypted text content.

    Raises:
        EnvironmentError: If the 'sops' CLI tool is missing.
        PermissionError: If Vault authentication fails.
        RuntimeError: If the SOPS decryption process fails.
        FileNotFoundError: If 'sops' cannot be found in the system PATH.
    """
    import subprocess

    from chaos.lib.secret_backends.crypto import check_vault_auth, is_vault_in_use
    from chaos.lib.utils import checkDep

    if not checkDep("sops"):
        raise EnvironmentError("The 'sops' CLI tool is required but not found in PATH.")

    provider = _resolveProvider(context, config)

    if is_vault_in_use(sops_file):
        is_authed, message = check_vault_auth()
        if not is_authed:
            raise PermissionError(message)

    try:
        if provider:
            sopsDecryptResult = provider.decrypt(secrets_file, sops_file)
        else:
            sopsDecryptResult = subprocess.run(
                ["sops", "--config", sops_file, "--decrypt", secrets_file],
                check=True,
                capture_output=True,
                text=True,
            ).stdout

        return sopsDecryptResult
    except subprocess.CalledProcessError as e:
        details = e.stderr if e.stderr else "No output."
        raise RuntimeError(f"SOPS decryption failed.\nDetails: {details}") from e
    except FileNotFoundError as e:
        raise FileNotFoundError(
            "'sops' command not found. Please ensure sops is installed and in your PATH."
        ) from e
