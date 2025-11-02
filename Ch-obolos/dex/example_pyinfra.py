#!/usr/bin/env python3
from omegaconf import OmegaConf
import getpass
import logging
from pyinfra.api import State, Config, Inventory
from pyinfra.api.connect import connect_all, disconnect_all
from pyinfra.api.operation import add_op
from pyinfra.api.operations import run_ops
from pyinfra.operations import server
from pyinfra.facts.server import Command
from pyinfra.api.state import StateStage
from pyinfra.context import ctx_state
from pyinfra.operations import pacman

logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")
# ------------------- NECESSARY FOR PYINFRA -----------------------
hosts = ["@local"]
inventory = Inventory((hosts, {}))
config = Config()
state = State(inventory,config)

state.current_stage = StateStage.Prepare
ctx_state.set(state)

connect_all(state)
host = state.inventory.get_host("@local")

ChObolo = OmegaConf.load("custom-plug-dex.yml")
basePkgs = list(ChObolo.pacotes
                + ChObolo.pacotes_base_override
                + [ChObolo.bootloader]
                + ChObolo.aur_helpers
                + [ChObolo.users[0].shell])

wntNotNatPkgs = ChObolo.aur_pkgs

native = host.get_fact(Command, "pacman -Qqen").strip().splitlines()
dependencies = host.get_fact(Command, "pacman -Qqdn").strip().splitlines()
aur = host.get_fact(Command, "pacman -Qqem").strip().splitlines()
aurDependencies= host.get_fact(Command, "pacman -Qqdm").strip().splitlines()

toRemoveNative = sorted(set(native) - set(basePkgs))
toRemoveAur = sorted(set(aur) - set(wntNotNatPkgs))

toAddNative = sorted(set(basePkgs) - set(native) - set(dependencies))
toAddAur = sorted(set(wntNotNatPkgs) - set(aur) - set(aurDependencies))


if toAddNative or toRemoveNative:
    print("--- Pacotes nativos a remover ---")
    for pkg in toRemoveNative:
        print(pkg)

    print("\n--- Pacotes nativos a adicionar ---")
    for pkg in toAddNative:
        print(pkg)

    confirm = input("Is This correct? (Y/n)")
    if confirm.lower() in ["y", "yes", "", "s", "sim"]:
        passwd = getpass.getpass(prompt="Senha do sudo: ")
        print("\nIniciando operações com pacotes nativos...")
        if toAddNative:
            add_op(
                state,
                pacman.packages,
                name="Instalando pacotes",
                packages=toAddNative,
                present=True,
                update=True,
                _sudo_password=passwd,
                _sudo=True
            )
        if toRemoveNative:
            add_op(
                state,
                pacman.packages,
                name="Desinstalando pacotes",
                packages=toRemoveNative,
                present=False,
                update=True,
                _sudo_password=passwd,
                _sudo=True
            )
        run_ops(state)
else:
    print("Sem pacotes Nativos para gerenciar.")


if toAddAur or toRemoveAur:
    print("\n--- Pacotes AUR a remover ---")
    for pkg in toRemoveAur:
        print(pkg)

    print("\n--- Pacotes AUR a adicionar ---")
    for pkg in toAddAur:
        print(pkg)

    confirmAur = input("Is This correct? (Y/n)")
    if confirmAur.lower() in ["y", "yes", "", "s", "sim"]:
        passwd = getpass.getpass(prompt="Senha do sudo: ")
        aur_helper = ChObolo.aur_helpers[0]

        if toAddAur:
            packagesStr = " ".join(toAddAur)
            fullCommand = f"{aur_helper} -S --noconfirm --answerdiff None --answerclean All --removemake {packagesStr}"
            add_op(
                state,
                server.shell,
                commands=[fullCommand],
                name="Instalando pacotes AUR",
                _sudo_password=passwd
            )
        if toRemoveAur:
            packagesRmvStr = " ".join(toRemoveAur)
            fullRemoveCommand = f"{aur_helper} -Rns --noconfirm {packagesRmvStr}"
            add_op(
                state,
                server.shell,
                commands=[fullRemoveCommand],
                name="Instalando pacotes AUR",
                _sudo_password=passwd
            )
        run_ops(state)
else:
    print("Sem Pacotes AUR para gerenciar.")

disconnect_all(state)
