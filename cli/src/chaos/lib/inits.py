from omegaconf import OmegaConf as oc
from chaos.lib.plugDiscovery import loadList
from rich.console import Console
from pathlib import Path
from rich.prompt import Prompt, Confirm
from rich.panel import Panel

import shutil
import yaml
import time
import subprocess
import tempfile
import sys
import os

console = Console()

def initChobolo(keys):
    finalConf = oc.create()
    addedKeys = set()

    for k in keys.values():
        lis = loadList(k)

        if isinstance(lis, list):
            for v in lis:
                newCfg = oc.create(v)

                for rootKey in newCfg.keys():
                    if rootKey in addedKeys:
                        console.print(f"[yellow]Warning:[/] Plugin conflict detected. The key '[bold]{rootKey}[/]' is being redefined via '{k}'. Merging, but verify priority.")
                    else:
                        addedKeys.add(rootKey)

                addedKeys.add(v)

                finalConf = oc.merge(finalConf, newCfg)
        elif lis is not None:
            console.print(f"[yellow]Warning:[/] Spec '{k}' did not return a list. Skipped.")

    path = os.path.expanduser("~/.config/chaos/ch-obolo_template.yml")
    oc.save(finalConf, path)


# -------------- SECRET INITING -------------


def checkDep(bin):
    path = shutil.which(bin)
    if path is None:
        return False
    return True

def setupAge():
    ageDir = Path(os.path.expanduser("~/.config/chaos"))
    ageFile = ageDir / "keys.txt"
    if not checkDep('age-keygen'):
        console.print(f"[bold red]ERROR:[/] age-keygen not installed, please install it to use sops+age.")
        sys.exit(1)
    console.print(f"[cyan]Info:[/] checking for age keys in [dim]{ageDir}[/]")
    pubkey = None
    if ageFile.exists():
        console.print(f"[cyan]Info:[/] Existing key found.")
        if not Confirm.ask("Do you wish to use this existing key?", default=True):
            console.print("[cyan]Info:[/] Moving this key to a backup and creating a new age file.")
            timestamp = int(time.time())
            try:
                subprocess.run(["mv", str(ageFile), f"{str(ageFile)}.{timestamp}.bak"])
            except subprocess.CalledProcessError as e:
                console.print(f"[bold red]ERROR:[/] Could not backup existing key: {e}")
                sys.exit(1)
            try:
                with open(ageFile, 'w') as f:
                    subprocess.run(['age-keygen'], stdout=f, check=True)
                proc = subprocess.run(['age-keygen', '-y', str(ageFile)], capture_output=True, text=True, check=True)
                pubkey = proc.stdout.strip()
                console.print(f"[bold green]Success![/] generated new age key!")
            except subprocess.CalledProcessError as e:
                console.print(f"[bold red]ERROR:[/] failed to generate new age key: {e}")
                sys.exit(1)

        try:
            proc = subprocess.run(['age-keygen', '-y', str(ageFile)], capture_output=True, text=True, check=True)
            pubkey = proc.stdout.strip()
        except subprocess.CalledProcessError as e:
            console.print(f"[bold red]ERROR:[/] failed to generate new age key: {e}")
            sys.exit(1)

    else:
        console.print("[cyan]Info:[/] No key found, generating a new one.")
        console.print(f"[bold yellow]WARNING:[/] THIS FILE: {ageFile} IS EXTREMELY IMPORTANT, if you lose it, you lose all your files forever. Do not commit it.")
        ageDir.mkdir(parents=True, exist_ok=True)
        try:
            with open(ageFile, 'w') as f:
                subprocess.run(['age-keygen'], stdout=f, check=True)
            proc = subprocess.run(['age-keygen', '-y', str(ageFile)], capture_output=True, text=True, check=True)
            pubkey = proc.stdout.strip()
            console.print(f"[bold green]Success![/] generated new age key!")
        except subprocess.CalledProcessError as e:
            console.print(f"[bold red]ERROR:[/] failed to generate new age key: {e}")
            sys.exit(1)

    return "age", pubkey

def genBatchGpg(name, email):
    batch = f"""
Key-Type: EdDSA
Key-Curve: ed25519
Subkey-Type: ECDH
Subkey-Curve: cv25519
Name-Real: {name}
Name-Email: {email}
Expire-Date: 0
%commit
"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp:
        tmp.write(batch)
        tmpPath=tmp.name

    try:
        console.print("[cyan]Info:[/] Requesting GPG key generation\n[yellow]Attention:[/] A Pinentry prompt should appear asking for a [italic]Passphrase.[/]")
        subprocess.run(['gpg', '--batch', '--generate-key', tmpPath], check=True)

        proc = subprocess.run(['gpg', '--list-secret-keys', '--with-colons', email], capture_output=True, text=True, check=True)

        fingerprint = None
        for line in proc.stdout.splitlines():
            parts = line.split(':')
            if parts[0] == 'fpr':
                fingerprint = parts[9]
                break

        if not fingerprint:
            raise Exception("Key generation finished, but fingerprint not found.")

        return fingerprint

    except subprocess.CalledProcessError as e:
        console.print("[bold red]ERROR:[/] GPG generation failed or was cancelled.")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]ERROR:[/] {e}")
        sys.exit(1)
    finally:
        if os.path.exists(tmpPath):
            os.unlink(tmpPath)

def genGpgManual():
    try:
        proc = subprocess.run(['gpg', '--list-secret-keys', '--keyid-format', 'LONG'], capture_output=True, text=True)
        output = proc.stdout

    except subprocess.CalledProcessError:
        console.print("[bold red]ERROR:[/] Failed to list GPG keys.")
        sys.exit(1)

    if "sec" not in output:
        console.print("[bold yellow]No GPG secret keys found.[/]")
        console.print("Please generate a GPG key manually using [bold]gpg --full-generate-key[/] or use [bold]age[/].")
        sys.exit(1)

    console.print(Panel(output, title="Available GPG Keys", border_style="cyan"))
    fingerprint = Prompt.ask("Enter the [bold]Fingerprint[/] (long hex string) of the key you want to use")
    fingerprint = fingerprint.replace(" ", "")

    if len(fingerprint) < 40:
        console.print("[bold red]ERROR:[/] Invalid fingerprint length.")
        sys.exit(1)

    return "pgp", fingerprint

def setupGpg():
    if not checkDep('gpg'):
        console.print("[bold red]ERROR:[/] Could not find gpg binary, please install gnupg and try again.")
        sys.exit(1)

    console.print("[bold yellow]WARNING:[/] ALL your secrets are tied to your ~/.gnupg folder. DO NOT lose it or commit it, or you'll lose your secrets forever.")
    proc = subprocess.run(['gpg', '--list-secret-keys', '--with-colons'], capture_output=True, text=True)
    hasKeys = "sec" in proc.stdout
    if hasKeys:
        console.print("[yellow]Existing GPG keys detected.[/]")
        if Confirm.ask("Do you want to use an existing key?", default=False):
            return genGpgManual()

    console.print(Panel("No keys selected. Let's generate one automatically.", border_style="green"))
    name = Prompt.ask("Enter your [bold]Full Name[/]")
    email = Prompt.ask("Enter your [bold]Email[/]")

    if Confirm.ask(f"Generate key for [cyan]{name} <{email}>[/]?", default=True):
        fingerprint = genBatchGpg(name, email)
        console.print(f"[green]Success:[/] Generated key [bold]{fingerprint}[/]")

        return "pgp", fingerprint
    else:
        console.print("[cyan]Please, create a key manually then try again.[/]")
        sys.exit(1)

def initSecrets():
    if not checkDep('sops'):
        console.print("[bold red]CRITICAL:[/] sops is not installed. It is required for this software.")
        sys.exit(1)

    hasAge = checkDep('age-keygen')
    hasGpg = checkDep('gpg')

    if not hasAge and not hasGpg:
        console.print("[bold red]CRITICAL:[/] Neither gpg nor age installed, both are needed for secure secret handling.")
        sys.exit(1)

    choices = []
    if hasAge:
        choices.append('age')
    if hasGpg:
        choices.append('gpg')

    default="gpg" if hasGpg else "age"
    console.print(Panel("Chaos uses [bold]SOPS[/] for encryption.\nYou need to choose a backend engine to handle the keys.", title="Secrets Initialization", border_style="green"))
    engine = Prompt.ask("Choose encryption engine", choices=choices, default=default)

    key = ""
    keyValue = ""

    if engine == "age":
        key, keyValue = setupAge()
    elif engine == "gpg":
        key, keyValue = setupGpg()

    configDir = Path(os.path.expanduser("~/.config/chaos"))
    configDir.mkdir(parents=True, exist_ok=True)
    sops_file = configDir / "sops-config.yml"
    sec_file = configDir / "secrets.yml"

    if sops_file.exists():
        if not Confirm.ask(f"A sops configuration already exists at [dim]{sops_file}[/]. Overwrite?", default=False):
            console.print("[yellow]Operation cancelled. Keeping existing config.[/]")
            sys.exit(0)

    sops_content = {
        "creation_rules": [
            {
                "path_regex": "(.*)?secrets.*\\.yml$",
                key: keyValue
            },
            {
                "path_regex": ".*\\.local/share/chaos/ramblings/.*\\.yml$",
                key: keyValue
            },
        ]
    }

    sec_content = {
        "user_secrets":{
            "your_user": {
                "password": "your_password"
            }
        }
    }

    try:
        with open(sops_file, 'w') as f:
            yaml.dump(sops_content, f, default_flow_style=False)

        if not sec_file.exists():
            with open(sec_file, 'w') as f:
                yaml.dump(sec_content, f, default_flow_style=False)

        console.print("[cyan]Info:[/] Encrypting initial secrets file...")
        console.print("[dim]Hint: Use chaos -es/chaos check s to both check your secrets and edit your secrets\nchaos check s will print your secrets to your screen to help with automation.[/]")
        subprocess.run([
            'sops',
            '--config', str(sops_file),
            '--encrypt',
            '--in-place',
            str(sec_file)
        ], check=True)

        console.print(f"[bold green]Success![/] SOPS configuration generated at: [dim]{sops_file}[/]")

        global_conf_path = configDir / "config.yml"
        conf = oc.load(global_conf_path) if global_conf_path.exists() else oc.create()
        conf.sops_file = str(sops_file)
        oc.save(conf, global_conf_path)
        console.print(f"[cyan]Info:[/] Updated global chaos config 'sops_file' path.")


    except subprocess.CalledProcessError as e:
        console.print(f"Could not encrypt file {sec_file}: {e}")
    except Exception as e:
        console.print(f"[bold red]ERROR:[/] Failed to write config file: {e}")
        console.print("[dim]Hint: Check if your GPG key is imported or if age keys are correct.[/]")
        sys.exit(1)
