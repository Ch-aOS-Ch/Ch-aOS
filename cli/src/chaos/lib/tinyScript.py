import os
from pathlib import Path
import subprocess
from omegaconf import OmegaConf
import sys

from rich.console import Console

def _get_sops_files(sops_file_override, secrets_file_override, team):
    secretsFile = secrets_file_override
    sopsFile = sops_file_override

    CONFIG_DIR = os.path.expanduser("~/.config/chaos")
    CONFIG_FILE_PATH = os.path.join(CONFIG_DIR, "config.yml")

    global_config = {}
    if os.path.exists(CONFIG_FILE_PATH):
        global_config = OmegaConf.load(CONFIG_FILE_PATH) or OmegaConf.create()

    if team:
        if not '.' in team:
            Console().print("[bold red]ERROR:[/] Must set a company for your team. (company.team)")
            sys.exit(1)

        parts = team.split('.')
        company = parts[0]
        team = parts[1]
        teamPath = Path(os.path.expanduser(f'~/.local/share/chaos/teams/{company}/{team}'))

        if teamPath.exists():

            teamSops = teamPath / sops_file_override if sops_file_override else teamPath / "sops-config.yml"
            teamSec = teamPath / f'secrets/{secrets_file_override}' if secrets_file_override else teamPath / "secrets/secrets.yml"

            secretsHelp = secretsFile
            sopsHelp = sopsFile

            sopsFile = teamSops if teamSops.exists() else sopsFile
            secretsFile = teamSec if teamSec.exists() else secretsFile

            if secrets_file_override and ('..' in secrets_file_override or secrets_file_override.startswith('/')):
                Console().print("[bold yellow]WARNING:[/]Team secrets file is invalid. Skipping.")
                secretsFile = secretsHelp
            if sops_file_override and ('..' in sops_file_override or sops_file_override.startswith('/')):
                Console().print("[bold yellow]WARNING:[/]Team sops file is invalid. Skipping.")
                sopsFile = sopsHelp

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

def runSopsCheck(sops_file_override, secrets_file_override, args):
    team = args.team
    secretsFile, sopsFile = _get_sops_files(sops_file_override, secrets_file_override, team)

    if not secretsFile or not sopsFile:
        print("ERROR: SOPS check requires both secrets file and sops config file paths.", file=sys.stderr)
        print("       Configure them using 'chaos -sec' and 'chaos -sops', or pass them with '-sf' and '-ss'.", file=sys.stderr)
        sys.exit(1)

    try:
        subprocess.run(['sops', '--config', sopsFile, '--decrypt', secretsFile], check=True)
    except subprocess.CalledProcessError as e:
        print("ERROR: SOPS decryption failed.")
        print("Details:", e.stderr.decode() if e.stderr else "No output.")
        sys.exit(1)
    except FileNotFoundError:
        print("ERROR: 'sops' command not found. Please ensure sops is installed and in your PATH.", file=sys.stderr)
        sys.exit(1)

def runSopsEdit(sops_file_override, secrets_file_override):
    secretsFile, sopsFile = _get_sops_files(sops_file_override, secrets_file_override)

    if not secretsFile or not sopsFile:
        print("ERROR: SOPS check requires both secrets file and sops config file paths.", file=sys.stderr)
        print("       Configure them using 'chaos -sec' and 'chaos -sops', or pass them with '-sf' and '-ss'.", file=sys.stderr)
        sys.exit(1)

    try:
        subprocess.run(['sops', '--config', sopsFile, secretsFile], check=True)
    except subprocess.CalledProcessError as e:
        if e.returncode == 200:
            print("File has not changed, exiting.")
            sys.exit(0)
        else:
            print(f"ERROR: SOPS editing failed with exit code {e.returncode}.", file=sys.stderr)
            sys.exit(1)
    except FileNotFoundError:
        print("ERROR: 'sops' command not found. Please ensure sops is installed and in your PATH.", file=sys.stderr)
        sys.exit(1)

def runChoboloEdit(chobolo_path):
    editor = os.getenv('EDITOR', 'nano')
    if not chobolo_path:
        CONFIG_DIR = os.path.expanduser("~/.config/chaos")
        CONFIG_FILE_PATH = os.path.join(CONFIG_DIR, "config.yml")
        cfg = OmegaConf.load(CONFIG_FILE_PATH)
        chobolo_path = cfg.get('chobolo_file', None)
    if chobolo_path:
        try:
            subprocess.run(
                [editor, chobolo_path],
                check=True
            )
        except subprocess.CalledProcessError as e:
            print("ERROR: Ch-obolo editing failed.")
            print("Details: Editor exited with error code", e.returncode)
            sys.exit(1)
        except FileNotFoundError:
            print(f"ERROR: Editor '{editor}' not found. Please ensure it is installed and in your PATH.", file=sys.stderr)
            sys.exit(1)
    else:
        print("ERROR: No Ch-obolo file configured to edit.", file=sys.stderr)
        sys.exit(1)


