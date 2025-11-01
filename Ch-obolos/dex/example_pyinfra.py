#!/usr/bin/env python3

from pyinfra.api import State, Config, Inventory, connect
from pyinfra.connectors.local import LocalConnector
from pyinfra.facts.server import Command
from pyinfra.api.exceptions import PyinfraError


def fetch_local_packages():
    """
    Usa o pyinfra como biblioteca para coletar o Fact PacmanPackages localmente.
    """

    print("Iniciando coleta do Fact PacmanPackages via pyinfra...")

    state = None  # garante que existe para o finally

    try:
        # 1. Criar Inventário com suporte à API nova do pyinfra
        inventory = Inventory(
            names_data=(["@local"], {}),    # dados de nomes não usados aqui
        )

        # 2. Criar configuração e o estado, incluindo o conector local
        config = Config()
        config.connectors = {"@local": (LocalConnector, {})}
        state = State(
            inventory,
            config,
        )

        # 3. Conectar ao host
        print("Conectando ao host local...")
        connect.connect_all(state)

        # 4. Obter o host do inventário
        host = state.inventory.get_host("@local")

        # 5. Coletar dados via 'pacman -Qqen'
        print("Coletando pacotes instalados (via pacman -Qqen)...")

        raw_output_string = host.get_fact(Command, "LC_ALL=C pacman -Qqen")

        if not raw_output_string:
            print("Nenhum pacote encontrado.")
            return

        # 6. Exibir resultado
        print(f"\n--- Pacotes Nativos e Explícitos (-Qqen) ---")

        # TRANSFORMAR A STRING EM LISTA:
        # .strip() remove newlines extras no início/fim
        # .splitlines() quebra a string em uma lista de linhas
        package_list = raw_output_string.strip().splitlines()

        # Agora 'package_list' é uma lista ['pkg1', 'pkg2', ...]
        # E podemos ordená-la
        package_list.sort()

        print(f"Total: {len(package_list)}\n")
        for pkg_name in package_list:
            print(pkg_name)

    except PyinfraError as e:
        print(f"[ERRO pyinfra] {e}")
    except Exception as e:
        print(f"[ERRO inesperado] {e}")
    finally:
        if state:
            print("\nDesconectando...")
            connect.disconnect_all(state)
            print("Conexão finalizada.")


if __name__ == "__main__":
    fetch_local_packages()
