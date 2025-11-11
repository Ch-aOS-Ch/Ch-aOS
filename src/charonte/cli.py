#!/usr/bin/env python3
import logging
import argparse
import getpass
from pyinfra.api.inventory import Inventory
from pyinfra.api.config import Config
from pyinfra.api.connect import connect_all, disconnect_all
from pyinfra.api.state import StateStage, State
from pyinfra.api.operations import run_ops
from pyinfra.context import ctx_state

from charonte.roles.pkgs.tasks import pkgs as pkgs_role
from charonte.roles.users.tasks import users as users_role
from charonte.roles.repos.tasks import repos as repos_role

ROLE_ALIASES = {
    "pkgs": "packages",
    "usr": "users",
    "repos": "repositories",
}

ROLES_DISPATCHER = {
    "packages": pkgs_role.run_all_pkg_logic,
    "users": users_role.run_user_logic,
    "repositories": repos_role.run_repo_logic,
}

def main():
    parser = argparse.ArgumentParser(description="Ch-aronte orquestrator.")
    parser.add_argument('tags', nargs='+', help=f"The tag(s) for the role(s) to be executed(usable: users, packages, repositories).\nAvailable aliases: usr, pkgs, repos ")
    parser.add_argument('-e', '--chobolo', required=True, help="Path to Ch-obolo to be used.")
    parser.add_argument('-ikwid', '-y', '--i-know-what-im-doing', action='store_true', help="I Know What I'm Doing mode, basically skips confirmations, only leaving sudo calls")
    parser.add_argument('--dry', '-d', action='store_true', help="Execute in dry mode.")
    parser.add_argument('-v', action='count', default=0, help="Increase verbosity level. -v for WARNING, -vvv for DEBUG.")
    parser.add_argument('--verbose', type=int, choices=[1, 2, 3], help="Set log level directly. 1=WARNING, 2=INFO, 3=DEBUG.")
    parser.add_argument(
        '--secrets-file',
        '-sf',
        dest='secrets_file_override',
        help="Path to the sops-encrypted secrets file (overrides secrets.sec_file value in ch-obolo)."
    )
    parser.add_argument(
        '--sops-file',
        '-ss',
        dest='sops_file_override',
        help="Path to the .sops.yaml config file (overrides secrets.sec_sops value in ch-obolo)."
    )
    args = parser.parse_args()

    log_level = None
    if args.verbose:
        if args.verbose == 1:
            log_level = logging.WARNING
        elif args.verbose == 2:
            log_level = logging.INFO
        elif args.verbose == 3:
            log_level = logging.DEBUG
    elif args.v == 1:
        log_level = logging.WARNING
    elif args.v == 2:
        log_level = logging.INFO
    elif args.v == 3:
        log_level = logging.DEBUG

    if log_level:
        logging.basicConfig(level=log_level, format="%(levelname)s: %(message)s")

    chobolo_path = args.chobolo
    ikwid = args.i_know_what_im_doing
    dry = args.dry

    hosts = ["@local"]
    inventory = Inventory((hosts, {}))
    config = Config()
    state = State(inventory, config)
    state.current_stage = StateStage.Prepare
    ctx_state.set(state)

    config.SUDO_PASSWORD = getpass.getpass("Sudo password: ")

    skip = ikwid

    print("Connecting to localhost...")
    connect_all(state)
    host = state.inventory.get_host("@local")
    print("Connection established.")
    # -----------------------------------------

    # ----- args -----
    commonArgs = (state, host, chobolo_path, skip)
    secArgs = (
        state,
        host,
        chobolo_path,
        skip,
        args.secrets_file_override,
        args.sops_file_override
    )
    SEC_HAVING_ROLES={'users','secrets'}
    # --- Role orchestration ---
    for tag in args.tags:
        normalized_tag = ROLE_ALIASES.get(tag,tag)
        if normalized_tag in ROLES_DISPATCHER:
            print(f"\n--- Executing {normalized_tag} role with Ch-obolo: {chobolo_path} ---\n")
            if normalized_tag in SEC_HAVING_ROLES:
                ROLES_DISPATCHER[normalized_tag](*secArgs)
            else:
                ROLES_DISPATCHER[normalized_tag](*commonArgs)
            print(f"\n--- '{normalized_tag}' role finalized. ---")
        else:
            print(f"\nWARNING: Unknown tag '{normalized_tag}'. Skipping.")

    if not dry:
        run_ops(state)
    else:
        print(f"dry mode active, skipping.")
    # --- Disconnection ---
    print("\nDisconnecting...")
    disconnect_all(state)
    print("Finalized.")

if __name__ == "__main__":
    main()
