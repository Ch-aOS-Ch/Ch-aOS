from omegaconf import ListConfig
from pathlib import Path
from chaos.lib.checkers import is_vault_in_use, check_vault_auth
from rich.console import Console
import sys
import os
from omegaconf import OmegaConf
import subprocess


console = Console()

def get_sops_files(sops_file_override, secrets_file_override, team):
    secretsFile = secrets_file_override
    sopsFile = sops_file_override

    CONFIG_DIR = os.path.expanduser("~/.config/chaos")
    CONFIG_FILE_PATH = os.path.join(CONFIG_DIR, "config.yml")

    global_config = {}
    if os.path.exists(CONFIG_FILE_PATH):
        global_config = OmegaConf.load(CONFIG_FILE_PATH) or OmegaConf.create()

    if team:
        if not '.' in team:
            Console().print("[bold red]ERROR:[/] Must set a company for your team. (company.team.group)")
            sys.exit(1)

        parts = team.split('.')
        company = parts[0]
        team = parts[1]
        group = parts[2] if len(parts) > 2 else None

        if not company:
            console.print(f"[bold red]ERROR:[/] Company name cannot be empty in '{team}'.")
            sys.exit(1)
        if not team:
            console.print(f"[bold red]ERROR:[/] Team name cannot be empty in '{team}'.")
            sys.exit(1)
        if group is not None and not group:
            console.print(f"[bold red]ERROR:[/] Group name cannot be empty in '{team}'.")
            sys.exit(1)

        if ".." in company or company.startswith("/"):
             console.print(f"[bold red]ERROR:[/] Invalid company name '{company}'.")
             sys.exit(1)

        if ".." in team or team.startswith("/"):
             console.print(f"[bold red]ERROR:[/] Invalid team name '{team}'.")
             sys.exit(1)

        teamPath = Path(os.path.expanduser(f'~/.local/share/chaos/teams/{company}/{team}'))

        if teamPath.exists():
            sopsFile = teamPath / "sops-config.yml"
            default_secrets_filename = "secrets/secrets.yml"
            if group:
                groupPath = f"secrets/{group}"
                if not (teamPath / groupPath).exists():
                    console.print(f"[bold red]ERROR:[/] Group directory for '{group}' not found at {teamPath / groupPath}.")
                    sys.exit(1)
                default_secrets_filename = f"{groupPath}/secrets.yml"
            secretsFile = teamPath / default_secrets_filename


            if sops_file_override:
                if '..' in sops_file_override or sops_file_override.startswith('/'):
                    console.print(f"[bold red]ERROR:[/] Invalid team sops file override '{sops_file_override}'.")
                    sys.exit(1)
                sopsFile = teamPath / sops_file_override

            if secrets_file_override:
                if '..' in secrets_file_override or secrets_file_override.startswith('/'):
                    console.print(f"[bold red]ERROR:[/] Invalid team secrets file override '{secrets_file_override}'.")
                    sys.exit(1)
                if not group:
                    secrets_temp = teamPath / "secrets" / secrets_file_override

                else:
                    secretsFile = teamPath / "secrets" / group / secrets_file_override

            return str(secretsFile), str(sopsFile)
        else:
            console.print(f"[bold red]ERROR:[/] Team directory for '{team}' not found at {teamPath}.")
            sys.exit(1)

    if not secretsFile:
        secretsFile = global_config.get('secrets_file')
    if not sopsFile:
        sopsFile = global_config.get('sops_file')

    if not secretsFile or not sopsFile:
        ChOboloPath = global_config.get('chobolo_file', None)
        if ChOboloPath:
            try:
                ChObolo = OmegaConf.load(ChOboloPath)
                secrets_config = ChObolo.get('secrets', None)
                if secrets_config:
                    if not secretsFile:
                        secretsFile = secrets_config.get('sec_file')
                    if not sopsFile:
                        sopsFile = secrets_config.get('sec_sops')
            except Exception as e:
                print(f"WARNING: Could not load Chobolo fallback '{ChOboloPath}': {e}", file=sys.stderr)

    return secretsFile, sopsFile

def flatten(items):
    for i in items:
        if isinstance(i, (list, ListConfig)):
            yield from flatten(i)
        else:
            yield i

def handleUpdateAllSecrets(args):
    console.print("\n[bold cyan]Starting key update for all secret files...[/]")

    sops_file_override = getattr(args, 'sops_file_override', None)
    secrets_file_override = getattr(args, 'secrets_file_override', None)
    team = getattr(args, 'team', None)

    main_secrets_file, sops_file_path = get_sops_files(sops_file_override, secrets_file_override, team)

    if is_vault_in_use(sops_file_path):
        is_authed, message = check_vault_auth()
        if not is_authed:
            console.print(message)
            sys.exit(1)

    if not sops_file_path:
        console.print("[bold yellow]Warning:[/] No sops config file found for main secrets. Skipping main secrets file update.")
    elif main_secrets_file and Path(main_secrets_file).exists():
        try:
            data = OmegaConf.load(main_secrets_file)
            if "sops" in data:
                console.print(f"Updating keys for main secrets file: [cyan]{main_secrets_file}[/]")
                result = subprocess.run(
                    ['sops', '--config', sops_file_path, 'updatekeys', main_secrets_file],
                    check=True, input="y", text=True, capture_output=True
                )
                console.print("[green]Keys updated successfully.[/green]")
        except subprocess.CalledProcessError as e:
            console.print(f'[bold red]ERROR:[/] Failed to update keys for {main_secrets_file}: {e.stderr}')
        except Exception as e:
            console.print(f'[bold red]ERROR:[/] Could not process file {main_secrets_file}: {e}')
    else:
        console.print("[dim]Main secrets file not found or not configured. Skipping.[/dim]")

    console.print("\n[bold cyan]Updating ramble files...[/]")
    from chaos.lib.ramble import handleUpdateEncryptRamble
    handleUpdateEncryptRamble(args)
