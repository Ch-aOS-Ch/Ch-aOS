import os
import shutil
from pathlib import Path
from typing import TYPE_CHECKING, cast

from ..utils import validate_path
from .providers.base import Provider

if TYPE_CHECKING:
    from .providers.base import Provider

"""
Now now, I KNOW this is way too big of a file, but bear with me here
"""


def _resolveProvider(args, global_config):
    if hasattr(args, "provider") and args.provider is not None:
        args = _handle_provider_arg(args, global_config)

    return _getProvider(args, global_config)


def _getProvider(args, global_config):
    """Returns the appropriate secret provider based on the command-line arguments."""
    from chaos.lib.utils import get_providerEps

    provider_eps = get_providerEps()

    if not provider_eps:
        return None

    for ep in provider_eps:
        ProviderClass = ep.load()
        providerFlag, _ = ProviderClass.get_cli_name()

        if hasattr(args, providerFlag) and getattr(args, providerFlag):
            return ProviderClass(args, global_config)

    return None


def _getProviderByName(provider_subcommand_name: str, args, global_config) -> Provider:
    from chaos.lib.utils import get_providerEps

    provider = None
    provider_eps = get_providerEps()
    if not provider_eps:
        raise ValueError("No secret providers available for exporting secrets.")

    for ep in provider_eps:
        ProviderClass = ep.load()
        _, providerCliName = ProviderClass.get_cli_name()
        if providerCliName == provider_subcommand_name:
            provider = ProviderClass(args, global_config)

            if not isinstance(provider, Provider) or not hasattr(
                provider, "export_secrets"
            ):
                raise TypeError(
                    f"The provider '{providerCliName}' does not support exporting secrets."
                )
            break

    if not provider or provider is None:
        raise ValueError(f"No secret provider found for '{provider_subcommand_name}'.")
    return provider


def setup_gpg_keys(gnupghome) -> None:
    """
    Sets up a TEMPORARY gnupghome in order to keep imported gpg keys ephemeral
    """
    import subprocess

    from rich.console import Console

    console = Console()
    actualGnupgHome_path = Path(os.getenv("GNUPGHOME", str(Path.home() / ".gnupg")))
    temp_gnupg_path = Path(gnupghome.name)

    if not actualGnupgHome_path.exists():
        return

    srcPriv = actualGnupgHome_path / "private-keys-v1.d"
    detstPriv = temp_gnupg_path / "private-keys-v1.d"

    try:
        shutil.copytree(srcPriv, detstPriv, dirs_exist_ok=True)
        os.chmod(detstPriv, 0o700)

    except Exception as e:
        console.print(
            f"[bold yellow]Warning:[/] Could not fully prepare temporary GPG directory: {e}"
        )

    pubKeyDump = temp_gnupg_path / "host_pubkeys.gpg"

    try:
        with open(pubKeyDump, "wb") as f:
            subprocess.run(
                ["gpg", "--export"], stdout=f, check=True, stderr=subprocess.DEVNULL
            )

    except subprocess.CalledProcessError as e:
        console.print(f"[bold yellow]Warning:[/] Could not export public GPG keys: {e}")
        return

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
    except subprocess.CalledProcessError as e:
        console.print(
            f"[bold yellow]Warning:[/] Could not import public GPG keys into temporary GNUPGHOME: {e}"
        )
        return

    src_trust = actualGnupgHome_path / "trustdb.gpg"
    if src_trust.exists():
        try:
            shutil.copy2(src_trust, temp_gnupg_path / "trustdb.gpg")
        except Exception:
            pass


def conc_age_keys(secKey: str) -> str:
    """
    Concatenates existing age keys with imported ones
    """
    sops_file_env = os.getenv("SOPS_AGE_KEY_FILE")
    if not sops_file_env or not Path(sops_file_env).exists():
        return secKey

    with open(sops_file_env, "r") as f:
        existing_keys_content = f.read()

    concResult = existing_keys_content.strip() + "\n" + secKey

    return concResult


def is_valid_fp(fp):
    """
    Checks for gpg fingerprint validity
    """
    import re

    clean_fingerprint = fp.replace(" ", "").replace("\n", "")
    if re.fullmatch(r"^[0-9A-Fa-f]{40}$", clean_fingerprint):
        return True
    else:
        return False


def pgp_exists(fp):
    """
    Checks for gpg fp existence
    """
    import subprocess

    try:
        subprocess.run(
            ["gpg", "--list-keys", fp],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except subprocess.CalledProcessError:
        return False


def is_valid_age_key(pubKey: str) -> bool:
    """
    Validates public age keys
    """
    import re

    isValid = False
    testPub = re.fullmatch(r"age1[a-z0-9]{58}", pubKey)
    if testPub:
        isValid = True
    return isValid


def is_valid_age_secret_key(secKey: str) -> bool:
    """
    Validates private age keys
    """
    import re

    isValid = False
    testSec = re.fullmatch(r"AGE-SECRET-KEY-1[A-Za-z0-9]{58}", secKey)
    if testSec:
        isValid = True
    return isValid


def setup_vault_keys(vaultAddr: str, keyPath: Path) -> str:
    """
    Sets up the vault keys for exporting, validating them on the way
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
    """
    Creates a pipe for passing inside a FD
    """
    r, w = os.pipe()
    os.write(w, token.encode())
    os.fchmod(w, 0o600)
    os.close(w)
    return r


def _is_valid_vault_key(key):
    """
    checks if vault key is valid
    """
    import hvac  # type: ignore
    import requests.exceptions

    try:
        client = hvac.Client(url=key)
        seal_status = client.sys.read_seal_status()
        if not seal_status:
            return (
                False,
                f"Vault URI '{key}' did not return a valid seal status or Vault server is unreachable.",
            )
        if "sealed" in seal_status["data"]:
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


def extract_age_keys(key_content: str) -> tuple[str | None, str | None]:
    """
    extracts age private and public keys
    """
    pubKey, secKey = None, None
    for line in key_content.splitlines():
        line = line.strip()
        if line.strip().startswith("# public key:"):
            pubKey = line.split(":", 1)[1].strip()
        if line.strip().startswith("AGE-SECRET-KEY-"):
            secKey = line
    return pubKey, secKey


def extract_gpg_keys(fingerprints: list[str]) -> str:
    """
    Extracts gpg private and public keys (note that chaos exported gpg keys use the chaos compress and decompress methods.)
    """
    import subprocess

    try:
        result = subprocess.run(
            ["gpg", "--export-secret-keys"] + fingerprints,
            capture_output=True,
            check=True,
        )
        gpg_key: bytes = result.stdout
        if not gpg_key:
            raise ValueError(
                "No output from 'gpg --export-secret-keys'. Is the fingerprint correct?"
            )
        encoded_gpg: str = compress(gpg_key)
        key_content = f"""# fingerprints: {fingerprints}
-----BEGIN PGP PRIVATE KEY BLOCK-----
{encoded_gpg}
-----END PGP PRIVATE KEY BLOCK-----"""

        return key_content

    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"Failed to export GPG secret key: {e.stderr.strip()}"
        ) from e
    except FileNotFoundError:
        raise RuntimeError(
            "The 'gpg' CLI tool is not installed or not found in PATH."
        ) from None
    except Exception as e:
        raise RuntimeError(f"Unexpected error exporting GPG key: {str(e)}") from e


def compress(data: bytes) -> str:
    """
    Compression/Decompression for gpg keys. This is the only way they can fit inside a bw notes
    """
    import base64
    import zlib

    try:
        compressed_data = zlib.compress(data, level=9)
        encoded_data = base64.b85encode(compressed_data).decode("utf-8")
    except Exception as e:
        raise RuntimeError(f"Failed to compress and encode data: {e}") from e
    return encoded_data


def decompress(encoded_data: str) -> bytes:
    import base64
    import zlib

    try:
        compressed_data = base64.b85decode(encoded_data.encode("utf-8"))
        data = zlib.decompress(compressed_data)
        return data
    except Exception as e:
        raise RuntimeError(f"Failed to decode and decompress data: {e}") from e


def get_sops_files(sops_file_override, secrets_file_override, team):
    """
    Gets sops files, secrets files and config files
    """
    from omegaconf import DictConfig, OmegaConf
    from rich.console import Console

    console = Console()
    secretsFile = secrets_file_override
    sopsFile = sops_file_override

    CONFIG_DIR = os.path.expanduser("~/.config/chaos")
    CONFIG_FILE_PATH = os.path.join(CONFIG_DIR, "config.yml")

    global_config = {}
    if os.path.exists(CONFIG_FILE_PATH):
        global_config = OmegaConf.load(CONFIG_FILE_PATH) or OmegaConf.create()

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
            os.path.expanduser(f"~/.local/share/chaos/teams/{company}/{team_name}")
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
                    import sys

                    console.print("[bold red]ERROR:[/] Path traversal detected.")
                    sys.exit(1)
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
            except Exception as e:
                import sys

                print(
                    f"WARNING: Could not load Chobolo fallback '{ChOboloPath}': {e}",
                    file=sys.stderr,
                )

    validate_path(secretsFile)
    validate_path(sopsFile)

    return secretsFile, sopsFile, global_config


def flatten(items):
    """
    Turns a concatenated list into a singular list
    """
    from omegaconf import ListConfig

    for i in items:
        if isinstance(i, (list, ListConfig)):
            yield from flatten(i)
        else:
            yield i


def _save_to_config(backend: str, data_to_save: dict) -> None:
    """
    Saves provider-specific data to the chaos config file.
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


def handleUpdateAllSecrets(args):
    """
    The rest of the functions should be auto explicative.
    """
    import subprocess

    from omegaconf import OmegaConf
    from rich.console import Console

    from chaos.lib.checkers import check_vault_auth, is_vault_in_use

    console = Console()
    console.print("\n[bold cyan]Starting key update for all secret files...[/]")

    sops_file_override = getattr(args, "sops_file_override", None)
    secrets_file_override = getattr(args, "secrets_file_override", None)
    team = getattr(args, "team", None)

    main_secrets_file, sops_file_path, global_config = get_sops_files(
        sops_file_override, secrets_file_override, team
    )

    if is_vault_in_use(sops_file_path):
        is_authed, message = check_vault_auth()
        if not is_authed:
            raise PermissionError(message)

    if not sops_file_path:
        console.print(
            "[bold yellow]Warning:[/] No sops config file found for main secrets. Skipping main secrets file update."
        )
    elif main_secrets_file and Path(main_secrets_file).exists():
        try:
            data = OmegaConf.load(main_secrets_file)
            if "sops" in data:
                console.print(
                    f"Updating keys for main secrets file: [cyan]{main_secrets_file}[/]"
                )

                provider = _resolveProvider(args, global_config)

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
                console.print("[green]Keys updated successfully.[/green]")
        except subprocess.CalledProcessError as e:
            console.print(
                f"[bold red]ERROR:[/] Failed to update keys for {main_secrets_file}: {e.stderr}"
            )
        except Exception as e:
            console.print(
                f"[bold red]ERROR:[/] Could not process file {main_secrets_file}: {e}"
            )
    else:
        console.print(
            "[dim]Main secrets file not found or not configured. Skipping.[/dim]"
        )

    console.print("\n[bold cyan]Updating ramble files...[/]")
    from chaos.lib.ramble import handleUpdateEncryptRamble

    handleUpdateEncryptRamble(args)


def _handle_provider_arg(args, config):
    from chaos.lib.utils import get_providerEps

    if not hasattr(args, "provider") or args.provider is None:
        return args

    if not config or "secret_providers" not in config:
        raise FileNotFoundError(
            "Could not find 'secret_providers' in ~/.config/chaos/config.yml."
        )

    providers_config = config.secret_providers
    provider_name = args.provider

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

            setattr(args, providerFlag, value_to_set)
            provider_found = True
            break

    if not provider_found:
        raise ValueError(
            f"No installed provider plugin matched the backend '{backend}'."
        )

    args.provider = None
    return args


def _generic_handle_add(key_type: str, args, sops_file_override: str, valids: set):
    from omegaconf import DictConfig, OmegaConf
    from rich.console import Console

    console = Console()
    if not valids:
        console.print("No valid keys. Returning.")
        return

    try:
        create = args.create
        config_data = OmegaConf.load(sops_file_override)
        config_data = cast(DictConfig, config_data)
        creation_rules = config_data.get("creation_rules", [])
        if not creation_rules:
            raise ValueError(
                f"No 'creation_rules' found in {sops_file_override}. Cannot add keys."
            )

        rule_index = getattr(args, "index", None)
        rules_to_process = creation_rules
        if rule_index is not None:
            if not (0 <= rule_index < len(creation_rules)):
                raise ValueError(
                    f"Invalid rule index {rule_index}. Must be between 0 and {len(creation_rules) - 1}."
                )
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
                console.print(
                    f"[yellow]All provided keys are already in the relevant sops config '{key_type}' sections, or no '{key_type}' sections were found. No changes made.[/]"
                )
                return

            OmegaConf.save(config_data, sops_file_override)
            console.print(
                f"[bold green]Successfully updated sops config![/] New keys added: {list(total_added_keys)}"
            )
        else:
            for rule in rules_to_process:
                new_group = OmegaConf.create({key_type: list(valids)})
                if "key_groups" in rule and rule.key_groups is not None:
                    rule.key_groups.append(new_group)
                else:
                    rule.key_groups = [new_group]

            OmegaConf.save(config_data, sops_file_override)
            console.print(
                f"[bold green]Successfully updated sops config![/] New {key_type.upper()} key group created with keys: {list(valids)}"
            )

    except Exception as e:
        raise RuntimeError(
            f"Failed to load or save sops config file {sops_file_override}: {e}"
        ) from e


def _generic_handle_rem(
    key_type: str, args, sops_file_override: str, keys_to_remove: set
):
    from omegaconf import DictConfig, OmegaConf
    from rich.console import Console

    console = Console()
    rule_index = getattr(args, "index", None)
    ikwid = getattr(args, "i_know_what_im_doing", False)

    if not keys_to_remove:
        console.print("No keys to remove. Exiting.")
        return

    try:
        config_data = OmegaConf.load(sops_file_override)
        config_data = cast(DictConfig, config_data)
        creation_rules = config_data.get("creation_rules", [])
        if not creation_rules:
            console.print(
                "[bold yellow]Warning:[/] No 'creation_rules' found in the sops config. Nothing to do."
            )
            return

        if not ikwid:
            console.print("Keys to remove:")
            for key in keys_to_remove:
                console.print(f"  {key}")

        rules_to_process = creation_rules
        if rule_index is not None:
            if not (0 <= rule_index < len(creation_rules)):
                raise ValueError(
                    f"Invalid rule index {rule_index}. Must be between 0 and {len(creation_rules) - 1}."
                )
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
        console.print(
            f"[bold green]Successfully updated sops config![/] Keys removed: {list(keys_to_remove)}"
        )

    except Exception as e:
        raise RuntimeError(f"Failed to update sops config file: {e}") from e


def decrypt_secrets(secrets_file: str, sops_file: str, config, args) -> str:
    import subprocess

    from chaos.lib.checkers import check_vault_auth, is_vault_in_use
    from chaos.lib.utils import checkDep

    if not checkDep("sops"):
        raise EnvironmentError("The 'sops' CLI tool is required but not found in PATH.")

    provider = _resolveProvider(args, config)

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


def _import_age_keys(key_content: str) -> None:
    from rich.console import Console
    from rich.prompt import Confirm

    console = Console()
    currentPathAgeFile = Path.cwd() / "keys.txt"

    if currentPathAgeFile.exists():
        console.print(
            "[yellow]WARNING:[/] A 'keys.txt' file already exists in the current directory. It will be overwritten."
        )
        confirm = Confirm.ask("Do you want to proceed?", default=False)

        if not confirm:
            console.print("Operation cancelled by user.")
            return

    with currentPathAgeFile.open("w") as f:
        sanitized_content = "\n".join(
            line.lstrip() for line in key_content.splitlines()
        )
        f.write(sanitized_content)
        if not sanitized_content.endswith("\n"):
            f.write("\n")


def _import_gpg_keys(secKey: str) -> None:
    import subprocess

    from rich.console import Console

    console = Console()
    decompressedKey = decompress(secKey)

    try:
        import_cmd = ["gpg", "--batch", "--import"]
        subprocess.run(
            import_cmd,
            input=decompressedKey,
            check=True,
            capture_output=True,
        )
        console.print(
            "[green]GPG key imported into your local GPG keyring successfully.[/green]"
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Error importing GPG key: {e.stderr.strip()}") from e


def _import_vault_keys(key_content: str) -> None:
    currentPathVaultFile = Path.cwd() / "vault_key.txt"

    with currentPathVaultFile.open("w") as f:
        f.write(key_content)
