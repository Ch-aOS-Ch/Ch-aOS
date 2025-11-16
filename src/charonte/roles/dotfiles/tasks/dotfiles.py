#!/usr/bin/env python3
import os
import yaml
from io import StringIO
from omegaconf import OmegaConf

from pyinfra.api.state import State
from pyinfra.api.operation import add_op
from pyinfra.operations import server, git, files, pacman
from pyinfra.facts.server import Command, Home
from pyinfra.facts.files import File, Link, Directory, FindFiles

def processDotfileRepo(state: State, host, user: str, config: dict, skip: bool):
    repo_url = config.get('repo')
    if not repo_url:
        return

    user_home = host.get_fact(Home, user=user)
    repo_base_name = repo_url.split('/')[-1].replace('.git', '')
    repo_path = os.path.join(user_home, '.dotfiles', repo_base_name)

    add_op(
        state,
        git.repo,
        name=f"Clone/update dotfiles repo for {user}: {repo_base_name}",
        src=repo_url,
        dest=repo_path,
        branch=config.get('version', 'main'),
        pull=True,
        user=user,
        ssh_keyscan=True,
    )

    manager = config.get('manager')
    install_command = config.get('install_command')

    if manager == 'stow':
        add_op(
            state,
            server.shell,
            name=f"Run stow for {user}",
            commands=[f"stow --target={user_home} --dir={repo_path} *"],
            user=user,
            chdir=repo_path,
        )
    elif manager == 'yadm':
         print("yadm manager not implemented yet in pyinfra role.")
    elif manager == 'charonte':
        links = config.get('links', [{}])
        runCharonteManager(state, host, user, repo_path, links)
    elif install_command:
        add_op(
            state,
            server.shell,
            name=f"Run custom install command for {user}",
            commands=[install_command],
            user=user,
            chdir=repo_path,
        )
    else:
        install_sh_path = os.path.join(repo_path, 'install.sh')
        if host.get_fact(File, path=install_sh_path):
            add_op(
                state,
                server.shell,
                name=f"Run install.sh for {user}",
                commands=["bash install.sh"],
                user=user,
                chdir=repo_path,
            )

def runCharonteManager(state: State, host, user: str, repo_path: str, links: list):
    # TODO:
    # 1. Define state file path
    # 2. Load previous state
    # 3. Build desired state from `links`
    # 4. Calculate delta (add, remove, update) using sets
    # 5. Implement removal of old links
    # 6. Implement creation of new links (handle open:true/false)
    # 7. Save new state
    pass

def run_dotfiles(state: State, host, chobolo_path, skip):
    chobolo = OmegaConf.load(chobolo_path)
    dotfiles_configs = chobolo.get('dotfiles', [])
    if not dotfiles_configs:
        print("No dotfiles configurations found.")
        return

    add_op(
        state,
        pacman.packages,
        name="Ensure git and stow are installed",
        packages=["git", "stow"],
        present=True,
        _sudo=True
    )

    users_raw = host.get_fact(Command, "awk -F: '($3>=1000){print $1}' /etc/passwd")
    system_users = set(users_raw.strip().splitlines()) if users_raw else set()

    for config in dotfiles_configs:
        user = config.get('user')
        if not user or user not in system_users:
            print(f"Skipping dotfiles for invalid or undefined user: {user}")
            continue

        processDotfileRepo(state, host, user, config, skip)
