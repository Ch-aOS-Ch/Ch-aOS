import subprocess
from typing import cast

from omegaconf import DictConfig, OmegaConf
from rich.console import Console

from chaos.lib.secret_backends.utils import (
    _generic_handle_add,
    _generic_handle_rem,
    flatten,
    is_valid_fp,
    pgp_exists,
)

console = Console()

"""
GPG specific handlers for add/rem/list
"""


def listPgp(sops_file_override):
    try:
        sops_config = OmegaConf.load(sops_file_override)
        sops_config = cast(DictConfig, sops_config)
        creation_rules = sops_config.get("creation_rules")
        if not creation_rules:
            console.print(
                "[bold yellow]Warning:[/] No 'creation_rules' found in the sops config. Nothing to do."
            )
            return

        all_pgp_keys_in_config = set()
        for rule in creation_rules:
            for key_group in rule.get("key_groups", []):
                if "pgp" in key_group and key_group.pgp is not None:
                    all_pgp_keys_in_config.update(flatten(key_group.pgp))

        if not all_pgp_keys_in_config:
            console.print("[cyan]INFO:[/] No keys to be shown.")

        return all_pgp_keys_in_config

    except Exception as e:
        raise RuntimeError(f"Failed to update sops config file: {e}") from e


def handlePgpAdd(payload, sops_file_override, keys):
    server = payload.pgp_server
    valids = set()
    for key in keys:
        clean_key = key.replace(" ", "")
        if len(clean_key) < 40:
            console.print(
                f"[bold yellow]WARNING:[/] Unsafe PGP key fingerprint: {key}. Skipping."
            )
            console.print(
                "[cyan]INFO:[/] To list your GPG keys, run: [italic]gpg --list-secret-keys --keyid-format LONG[/]"
            )
            continue

        if not is_valid_fp(clean_key):
            console.print(
                f"[bold red]ERROR:[/] Invalid PGP fingerprint: {key}. Skipping."
            )
            console.print(
                "[cyan]INFO:[/] To list your GPG keys, run: [italic]gpg --list-secret-keys --keyid-format LONG[/]"
            )
            continue

        if not pgp_exists(clean_key):
            console.print(
                f"[bold yellow]WARNING:[/] PGP fingerprint {key} does not exist locally."
            )
            if not server:
                console.print(
                    f"[bold red]ERROR:[/] PGP fingerprint {key} does not exist locally and no server was passed. Skipping"
                )
                console.print(
                    "[cyan]INFO:[/] To list your GPG keys, run: [italic]gpg --list-secret-keys --keyid-format LONG[/]"
                )
                continue
            try:
                subprocess.run(
                    ["gpg", "--keyserver", server, "--recv-keys", clean_key], check=True
                )
                console.print(
                    f"[green]Fingerprint {key} was successfully imported from {server}"
                )
            except subprocess.SubprocessError as e:
                console.print(
                    f"[bold red]ERROR:[/] Could not import {key} from {server}: {e}.\nSkipping."
                )
                continue
        valids.add(clean_key)
    _generic_handle_add("pgp", payload, sops_file_override, valids)


def handlePgpRem(payload, sops_file_override, keys):
    try:
        config_data = OmegaConf.load(sops_file_override)
        config_data = cast(DictConfig, config_data)
        creation_rules = config_data.get("creation_rules", [])
        if not creation_rules:
            console.print(
                "[bold yellow]Warning:[/] No 'creation_rules' found in the sops config. Nothing to do."
            )
            return

        all_pgp_keys_in_config = set()
        for rule in creation_rules:
            for key_group in rule.get("key_groups", []):
                if "pgp" in key_group and key_group.pgp is not None:
                    all_pgp_keys_in_config.update(flatten(key_group.pgp))

        keys_to_remove = set()
        for key_to_check in keys:
            clean_key = key_to_check.replace(" ", "")
            if not is_valid_fp(clean_key):
                console.print(
                    f"[bold red]ERROR:[/] Invalid PGP fingerprint: {key_to_check}. Skipping."
                )
                continue

            if clean_key in all_pgp_keys_in_config:
                keys_to_remove.add(clean_key)
            else:
                console.print(
                    f"[cyan]INFO:[/] Fingerprint: {key_to_check} not found in sops config. Skipping."
                )
        _generic_handle_rem("pgp", payload, sops_file_override, keys_to_remove)

    except Exception as e:
        raise RuntimeError(f"Failed to update sops config file: {e}") from e
