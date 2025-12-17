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

def checkDep(bin):
    path = shutil.which(bin)
    if path is None:
        return False
    return True

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

def setupSshToAge():
    if not checkDep('ssh-to-age'):
        console.print("[bold red]ERROR:[/] ssh-to-age is not installed. Please install it to use this feature.")
        sys.exit(1)

    console.print("[cyan]Info:[/] Looking for SSH public keys in ~/.ssh")
    ssh_dir = Path(os.path.expanduser("~/.ssh"))
    public_keys = list(ssh_dir.glob("*.pub"))

    if not public_keys:
        console.print("[bold red]ERROR:[/] No SSH public keys found in ~/.ssh. Cannot use ssh-to-age.")
        sys.exit(1)

    key_choices = [str(k) for k in public_keys]
    selected_key_path = Prompt.ask("Choose an SSH public key to use", choices=key_choices, default=key_choices[0])

    console.print(f"[cyan]Info:[/] Using SSH key: {selected_key_path}")
    console.print("[bold yellow]WARNING:[/] Your secrets will be tied to this SSH key. If you lose it, you will lose access to your secrets.")

    try:
        proc = subprocess.run(
            ['ssh-to-age', '-i', selected_key_path],
            capture_output=True, text=True, check=True
        )
        pubkey = proc.stdout.strip()
        console.print("[bold green]Success![/] Derived age public key from your SSH key.")
        return "age", pubkey
    except subprocess.CalledProcessError as e:
        console.print(f"[bold red]ERROR:[/] Failed to convert SSH key to age key: {e.stderr.strip()}")
        sys.exit(1)

def setupAge():
    ageDir = Path(os.path.expanduser("~/.config/chaos"))
    ageFile = ageDir / "keys.txt"

    if not checkDep('age-keygen'):
        console.print(f"[bold red]ERROR:[/] age-keygen not installed, please install it to use sops+age.")
        sys.exit(1)

    method_choices = ['generate']
    if checkDep('ssh-to-age'):
        method_choices.append('ssh')

    method = 'generate'
    if len(method_choices) > 1:
        method = Prompt.ask("Choose age key source", choices=method_choices, default='generate')

    if method == 'ssh':
        return setupSshToAge()

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
                "key_groups" : [
                    {
                        key: keyValue
                    }
                ]
            },
            {
                "path_regex": ".*\\.local/share/chaos/ramblings/.*\\.yml$",
                "key_groups" : [
                    {
                        key: keyValue
                    }
                ]
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
        console.print("[dim]Hint: Use chaos secrets edit/chaos check s to both check your secrets and edit your secrets\nchaos check s will print your secrets to your screen to help with automation.[/]")
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

# ------------- team-secret initing --------------

def initTeam(args):
    hasAge = checkDep('age-keygen')
    hasSops = checkDep('sops')
    hasPgp = checkDep('gpg')
    hasVault = checkDep('vault')

    if not hasSops:
        console.print("[bold red]CRITICAL:[/] sops is not installed. It is required for this software.")
        sys.exit(1)

    if not hasVault:
        console.print("[bold red]CRITICAL:[/] vault is not installed. It is required for this functionality.")
        sys.exit(1)

    if not (hasAge or hasPgp):
        console.print("[bold red]CRITICAL:[/] Neither gpg nor age are installed. At least one is required for this functionality.")
        sys.exit(1)

    choices = []

    if hasAge:
        choices.append('age')
    if hasPgp:
        choices.append('gpg')
    if hasPgp and hasAge:
        choices.append('both')

    batch = args.target

    if not '.' in batch:
        Console().print("[bold red]ERROR:[/] Must set a company for your team. (company.team.group)")
        sys.exit(1)

    parts = batch.split('.')
    company = parts[0]
    team = parts[1]
    person = parts[2] if len(parts) == 3 else None

    if not team or not company:
        console.print("[bold red]ERROR:[/] Must pass both team and company.")
        sys.exit(1)

    if person:
        if ".." in person or person.startswith("/"):
            console.print(f"[bold red]ERROR:[/] Invalid group name '{person}'.")
            sys.exit(1)

    if ".." in company or company.startswith("/"):
         console.print(f"[bold red]ERROR:[/] Invalid company name '{company}'.")
         sys.exit(1)

    if ".." in team or team.startswith("/"):
         console.print(f"[bold red]ERROR:[/] Invalid team name '{team}'.")
         sys.exit(1)


    teamDir = Path(os.path.expanduser(f"~/.local/share/chaos/teams/{company}/{team}"))
    teamDir.mkdir(parents=True, exist_ok=True)

    rambleTeamDir = teamDir / f"ramblings/{person}" if person else teamDir / "ramblings"
    rambleTeamDir.mkdir(parents=True, exist_ok=True)

    secretsTeamDir = teamDir / "secrets"
    devSecs = secretsTeamDir / "dev"
    devSecs.mkdir(parents=True, exist_ok=True)
    prodSecs = secretsTeamDir / "prod"
    prodSecs.mkdir(parents=True, exist_ok=True)

    sops_file = teamDir / "sops-config.yml"

    if sops_file.exists():
        if not Confirm.ask(f"A sops configuration already exists at [dim]{sops_file}[/]. Overwrite?", default=False):
            console.print("[yellow]Operation cancelled. Keeping existing config.[/]")
            sys.exit(0)

    default="age" if hasAge else "gpg"
    console.print(Panel("Chaos uses [bold]SOPS[/] for encryption.\nYou need to choose a backend engine to handle the keys.", title="Secrets Initialization", border_style="green"))
    engine = Prompt.ask("Choose encryption engine", choices=choices, default=default)

    sopsContent = {}
    match engine:
        case "age":
            rules = [
                {
                    "path_regex": "(.*)?secrets/dev/.*\\.(ya?ml|json|env)",
                    "shamir_threshold": 3,
                    "key_groups": [
                        { "hc_vault": [ "VAULT-TEAM-URI-INSTANCE." ] },
                        { "hc_vault": [ "VAULT-COMPANY-URI-INSTANCE" ] },
                        { "age": [ "YOUR-TEAM-UNIFIED-AGE-KEYS" ] },
                        { "age": [ "BACKUP-AGE-KEYS" ] }
                    ]
                },
                {
                    "path_regex": "(.*)?secrets/prod/.*\\.(ya?ml|json|env)",
                    "shamir_threshold": 4,
                    "key_groups" : [
                        { "hc_vault": [ "VAULT-TEAM-URI-INSTANCE." ] },
                        { "hc_vault": [ "VAULT-COMPANY-URI-INSTANCE" ] },
                        { "hc_vault": [ "VAULT-SECURITY-TEAM-URI-INSTANCE" ] },
                        { "hc_vault": [ "VAULT-COMPLIANCE-TEAM-URI-INSTANCE" ] },
                        { "age": [ "EACH-OF-YOUR-TEAM-MEMBERS-AGE-KEYS" ] },
                        { "age": [ "BACKUP-AGE-KEYS" ] }
                    ]
                }
            ]
            if person:
                rules.append({
                    "path_regex": f".*ramblings/{person}/.*\\.(ya?ml|json|env)",
                    "shamir_threshold": 3,
                    "key_groups" : [
                        { "hc_vault": [ "VAULT-TEAM-URI-INSTANCE." ] },
                        { "hc_vault": [ "VAULT-COMPANY-URI-INSTANCE" ] },
                        { "age": [ f"YOUR-TEAM-MEMBER-AGE-KEY" ] },
                        { "age": [ "BACKUP-AGE-KEYS" ] }
                    ]
                })
            sopsContent = {"creation_rules": rules}

        case "gpg":
            rules = [
                {
                    "path_regex": "(.*)?secrets/dev/.*\\.(ya?ml|json|env)",
                    "shamir_threshold": 3,
                    "key_groups": [
                        { "hc_vault": [ "VAULT-TEAM-URI-INSTANCE." ] },
                        { "hc_vault": [ "VAULT-COMPANY-URI-INSTANCE" ] },
                        { "pgp": [ "YOUR-TEAM-UNIFIED-PGP-KEYS" ] },
                        { "pgp": [ "BACKUP-PGP-KEYS" ] }
                    ]
                },
                {
                    "path_regex": "(.*)?secrets/prod/.*\\.(ya?ml|json|env)",
                    "shamir_threshold": 4,
                    "key_groups" : [
                        { "hc_vault": [ "VAULT-TEAM-URI-INSTANCE." ] },
                        { "hc_vault": [ "VAULT-COMPANY-URI-INSTANCE" ] },
                        { "hc_vault": [ "VAULT-SECURITY-TEAM-URI-INSTANCE" ] },
                        { "hc_vault": [ "VAULT-COMPLIANCE-TEAM-URI-INSTANCE" ] },
                        { "pgp": [ "EACH-OF-YOUR-TEAM-MEMBERS-PGP-KEYS" ] },
                        { "pgp": [ "BACKUP-PGP-KEYS" ] }
                    ]
                }
            ]
            if person:
                rules.append({
                    "path_regex": f".*ramblings/{person}/.*\\.(ya?ml|json|env)",
                    "shamir_threshold": 3,
                    "key_groups" : [
                        { "hc_vault": [ "VAULT-TEAM-URI-INSTANCE." ] },
                        { "hc_vault": [ "VAULT-COMPANY-URI-INSTANCE" ] },
                        { "pgp": [ f"YOUR-TEAM-MEMBER-PGP-KEY" ] },
                        { "pgp": [ "BACKUP-PGP-KEYS" ] }
                    ]
                })
            sopsContent = {"creation_rules": rules}

        case "both":
            rules = [
                {
                    "path_regex": "(.*)?secrets/dev/.*\\.(ya?ml|json|env)",
                    "shamir_threshold": 3,
                    "key_groups": [
                        { "hc_vault": [ "VAULT-TEAM-URI-INSTANCE." ] },
                        { "hc_vault": [ "VAULT-COMPANY-URI-INSTANCE" ] },
                        { "pgp": [ "YOUR-TEAM-UNIFIED-PGP-KEYS" ] },
                        { "pgp": [ "BACKUP-PGP-KEYS" ] },
                        { "age": [ "YOUR-TEAM-UNIFIED-AGE-KEYS" ] },
                        { "age": [ "BACKUP-AGE-KEYS" ] }
                    ]
                },
                {
                    "path_regex": "(.*)?secrets/prod/.*\\.(ya?ml|json|env)",
                    "shamir_threshold": 4,
                    "key_groups" : [
                        { "hc_vault": [ "VAULT-TEAM-URI-INSTANCE." ] },
                        { "hc_vault": [ "VAULT-COMPANY-URI-INSTANCE" ] },
                        { "hc_vault": [ "VAULT-SECURITY-TEAM-URI-INSTANCE" ] },
                        { "hc_vault": [ "VAULT-COMPLIANCE-TEAM-URI-INSTANCE" ] },
                        { "pgp": [ "EACH-OF-YOUR-TEAM-MEMBERS-PGP-KEYS" ] },
                        { "pgp": [ "BACKUP-PGP-KEYS" ] },
                        { "age": [ "EACH-OF-YOUR-TEAM-MEMBERS-AGE-KEYS" ] },
                        { "age": [ "BACKUP-AGE-KEYS" ] }
                    ]
                }
            ]
            if person:
                rules.append({
                    "path_regex": f".*ramblings/{person}/.*\\.(ya?ml|json|env)",
                    "shamir_threshold": 3,
                    "key_groups" : [
                        { "hc_vault": [ "VAULT-TEAM-URI-INSTANCE." ] },
                        { "hc_vault": [ "VAULT-COMPANY-URI-INSTANCE" ] },
                        { "pgp": [ f"YOUR-TEAM-MEMBER-PGP-KEY" ] },
                        { "pgp": [ "BACKUP-PGP-KEYS" ] },
                        { "age": [ f"YOUR-TEAM-MEMBER-AGE-KEY" ] },
                        { "age": [ "BACKUP-AGE-KEYS" ] }
                    ]
                })
            sopsContent = {"creation_rules": rules}
        case _:
            console.print("Unsuported. Exiting.")
            sys.exit(1)

    try:
        with open(sops_file, 'w') as f:
            yaml.dump(sopsContent, f, default_flow_style=False)

        console.print(f"[bold green]Success![/] SOPS configuration generated at: [dim]{sops_file}[/]")

    except Exception as e:
        console.print(f"[bold red]ERROR:[/] Failed to write config file: {e}")
        sys.exit(1)

