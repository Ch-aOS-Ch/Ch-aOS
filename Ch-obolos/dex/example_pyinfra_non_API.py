localhost = ["@local"]

# deploy.py
from types import prepare_class
from pyinfra.operations import server

pacman_pkg = server.shell(
    name="Listar pacotes nativos",
    commands=["pacman -Qqen"],
)

aur_pkg = server.shell(
    name="Listar pacotes AUR",
    commands=["pacman -Qqem"],
)
