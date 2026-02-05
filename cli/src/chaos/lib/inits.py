import os
import subprocess
import tempfile
import time
from pathlib import Path

import yaml
from omegaconf import OmegaConf as oc
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

from chaos.lib.plugDiscovery import loadList
from chaos.lib.secret_backends.utils import setup_pipe
from chaos.lib.utils import checkDep

console = Console()

"""
Scripts for initializing various parts of Ch-aOS, including Chobolo configurations and secret management.
"""


def initChobolo(keys, args):
    "Script to initialize Chobolo configuration based on provided keys (check plugDiscovery.py)."
    finalConf = oc.create()
    addedKeys = set()

    for k in keys.values():
        lis = loadList(k)

        if isinstance(lis, list):
            for v in lis:
                newCfg = oc.create(v)

                for rootKey in newCfg.keys():
                    if rootKey in addedKeys:
                        console.print(
                            f"[yellow]Warning:[/] Plugin conflict detected. The key '[bold]{rootKey}[/]' is being redefined via '{k}'. Merging, but verify priority."
                        )
                    else:
                        addedKeys.add(rootKey)

                finalConf = oc.merge(finalConf, newCfg)
        elif lis is not None:
            console.print(
                f"[yellow]Warning:[/] Spec '{k}' did not return a list. Skipped."
            )

    if not args.template:
        path = os.path.expanduser("~/.config/chaos/ch-obolo_template.yml")
        oc.save(finalConf, path)
    else:
        if args.human:
            print(oc.to_yaml(finalConf, resolve=True))
        else:
            print(finalConf)


# -------------- SECRET INITING -------------


def checkForSsh():
    """Checks for SSH public keys in ~/.ssh directory."""
    ssh_dir = Path(os.path.expanduser("~/.ssh"))
    public_keys = list(ssh_dir.glob("*.pub"))
    return public_keys


def setupSshToAge():
    """
    Setup age keys using ssh-to-age conversion.

    Deps: ssh-to-age
    """
    if not checkDep("ssh-to-age"):
        raise EnvironmentError(
            "ssh-to-age is not installed. Please install it to use this feature."
        )

    console.print("[cyan]Info:[/] Looking for SSH public keys in ~/.ssh")

    public_keys = checkForSsh()

    if not public_keys:
        raise FileNotFoundError(
            "No SSH public keys found in ~/.ssh. Cannot use ssh-to-age."
        )

    key_choices = [str(k) for k in public_keys]
    selected_key_path = Prompt.ask(
        "Choose an SSH public key to use", choices=key_choices, default=key_choices[0]
    )

    console.print(f"[cyan]Info:[/] Using SSH key: {selected_key_path}")
    passphrase = Prompt.ask(
        "Please enter the passphrase for your SSH key. Leave blank if it doesn't have any passhphrase.",
        password=True,
    )
    r_ssh = setup_pipe(passphrase)
    console.print(
        "[bold yellow]WARNING:[/] Your secrets will be tied to this SSH key. If you lose it, you will lose access to your secrets."
    )
    env = os.environ.copy()
    prefix = (
        f"read SSH_TO_AGE_PASSPHRASE </dev/fd/{r_ssh}; export SSH_TO_AGE_PASSPHRASE;"
    )
    private_cmd = f"ssh-to-age -i {selected_key_path.replace('.pub', '')} -private-key"
    full_cmd = f"{prefix} {private_cmd}"

    try:
        proc = subprocess.run(
            ["ssh-to-age", "-i", selected_key_path],
            capture_output=True,
            text=True,
            check=True,
        )
        pubkey = proc.stdout.strip()
        console.print(
            "[bold green]Success![/] Derived age public key from your SSH key."
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"Failed to convert SSH key to age key: {e.stderr.strip()}"
        ) from e

    try:
        proc = subprocess.run(
            full_cmd,
            env=env,
            check=True,
            pass_fds=(r_ssh,),
            capture_output=True,
            text=True,
            shell=True,
        )
        private_key = proc.stdout.strip()
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"Failed to derive private age key from SSH key: {e.stderr.strip()}"
        ) from e

    if not pubkey or not private_key:
        raise RuntimeError("Failed to derive age keys from SSH key.")

    ageDir = Path(os.path.expanduser("~/.config/chaos"))
    ageFile = ageDir / "keys.txt"
    ageDir.mkdir(parents=True, exist_ok=True)
    if ageFile.exists():
        console.print(
            f"[cyan]Info:[/] An existing age key file was found at {ageFile}, it will be overwritten."
        )
        confirm = Confirm.ask("Do you wish to continue?", default=True)
        console.print(
            "[cyan]Info:[/] Moving this key to a backup and creating a new age file."
        )
        if confirm:
            timestamp = int(time.time())
            try:
                subprocess.run(
                    ["mv", str(ageFile), f"{str(ageFile)}.{timestamp}.bak"], check=True
                )
            except subprocess.CalledProcessError as e:
                raise RuntimeError(f"Could not backup existing key: {e}") from e
    with open(ageFile, "w") as f:
        f.write(f"# created: {time.strftime('%Y-%m-%dT%H:%M:%S%z')}\n")
        f.write(f"# public key: {pubkey}\n")
        f.write(private_key + "\n")

    return "age", pubkey


def setupAge():
    """
    Setup Age keys for Sops encryption.

    deps: age-keygen
    """
    ageDir = Path(os.path.expanduser("~/.config/chaos"))
    ageFile = ageDir / "keys.txt"

    if not checkDep("age-keygen"):
        raise EnvironmentError(
            "age-keygen not installed, please install it to use sops+age."
        )
    method_choices = ["generate"]
    if checkDep("ssh-to-age"):
        method_choices.append("ssh")

    method = "generate"
    if len(method_choices) > 1:
        method = Prompt.ask(
            "Choose age key source", choices=method_choices, default="generate"
        )

    if method == "ssh":
        return setupSshToAge()

    console.print(f"[cyan]Info:[/] checking for age keys in [dim]{ageDir}[/]")
    pubkey = None
    if ageFile.exists():
        console.print("[cyan]Info:[/] Existing key found.")
        if not Confirm.ask("Do you wish to use this existing key?", default=True):
            console.print(
                "[cyan]Info:[/] Moving this key to a backup and creating a new age file."
            )
            timestamp = int(time.time())
            try:
                subprocess.run(
                    ["mv", str(ageFile), f"{str(ageFile)}.{timestamp}.bak"], check=True
                )
            except subprocess.CalledProcessError as e:
                raise RuntimeError(f"Could not backup existing key: {e}") from e
            try:
                with open(ageFile, "w") as f:
                    subprocess.run(["age-keygen"], stdout=f, check=True)
                proc = subprocess.run(
                    ["age-keygen", "-y", str(ageFile)],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                pubkey = proc.stdout.strip()
                console.print("[bold green]Success![/] generated new age key!")
            except subprocess.CalledProcessError as e:
                raise RuntimeError(f"Failed to generate new age key: {e}") from e

        try:
            proc = subprocess.run(
                ["age-keygen", "-y", str(ageFile)],
                capture_output=True,
                text=True,
                check=True,
            )
            pubkey = proc.stdout.strip()
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to generate new age key: {e}") from e

    else:
        console.print("[cyan]Info:[/] No key found, generating a new one.")
        console.print(
            f"[bold yellow]WARNING:[/] THIS FILE: {ageFile} IS EXTREMELY IMPORTANT, if you lose it, you lose all your files forever. Do not commit it."
        )
        ageDir.mkdir(parents=True, exist_ok=True)
        try:
            with open(ageFile, "w") as f:
                subprocess.run(["age-keygen"], stdout=f, check=True)
            proc = subprocess.run(
                ["age-keygen", "-y", str(ageFile)],
                capture_output=True,
                text=True,
                check=True,
            )
            pubkey = proc.stdout.strip()
            console.print("[bold green]Success![/] generated new age key!")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to generate new age key: {e}") from e

    return "age", pubkey


def genBatchGpg(name, email):
    """
    Generate GPG key in batch mode using provided name and email.

    Uses the best practices for key generation with EdDSA and Curve25519.

    deps: gnupg
    """
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
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmp:
        tmp.write(batch)
        tmpPath = tmp.name

    try:
        console.print(
            "[cyan]Info:[/] Requesting GPG key generation\n[yellow]Attention:[/] A Pinentry prompt should appear asking for a [italic]Passphrase.[/]"
        )
        subprocess.run(["gpg", "--batch", "--generate-key", tmpPath], check=True)

        proc = subprocess.run(
            ["gpg", "--list-secret-keys", "--with-colons", email],
            capture_output=True,
            text=True,
            check=True,
        )

        fingerprint = None
        for line in proc.stdout.splitlines():
            parts = line.split(":")
            if parts[0] == "fpr":
                fingerprint = parts[9]
                break

        if not fingerprint:
            raise RuntimeError("Key generation finished, but fingerprint not found.")

        return fingerprint

    except subprocess.CalledProcessError as e:
        raise RuntimeError("GPG generation failed or was cancelled.") from e
    except Exception as e:
        raise e
    finally:
        if os.path.exists(tmpPath):
            os.unlink(tmpPath)


def genGpgManual():
    """
    Lists all existing GPG secret keys and prompts user to select one by fingerprint.
    """
    try:
        proc = subprocess.run(
            ["gpg", "--list-secret-keys", "--keyid-format", "LONG"],
            capture_output=True,
            text=True,
            check=True,
        )
        output = proc.stdout

    except subprocess.CalledProcessError as e:
        raise RuntimeError("Failed to list GPG keys.") from e

    if "sec" not in output:
        raise ValueError(
            "No GPG secret keys found. Please generate a GPG key manually using 'gpg --full-generate-key' or use 'age'."
        )

    console.print(Panel(output, title="Available GPG Keys", border_style="cyan"))
    fingerprint = Prompt.ask(
        "Enter the [bold]Fingerprint[/] (long hex string) of the key you want to use"
    )
    fingerprint = fingerprint.replace(" ", "")

    if len(fingerprint) < 40:
        raise ValueError("Invalid fingerprint length.")

    return "pgp", fingerprint


def setupGpg():
    "Setup GPG keys for Sops encryption."
    if not checkDep("gpg"):
        raise EnvironmentError(
            "Could not find gpg binary, please install gnupg and try again."
        )

    console.print(
        "[bold yellow]WARNING:[/] ALL your secrets are tied to your ~/.gnupg folder. DO NOT lose it or commit it, or you'll lose your secrets forever."
    )
    proc = subprocess.run(
        ["gpg", "--list-secret-keys", "--with-colons"], capture_output=True, text=True
    )
    hasKeys = "sec" in proc.stdout
    if hasKeys:
        console.print("[yellow]Existing GPG keys detected.[/]")
        if Confirm.ask("Do you want to use an existing key?", default=False):
            return genGpgManual()

    console.print(
        Panel(
            "No keys selected. Let's generate one automatically.", border_style="green"
        )
    )
    name = Prompt.ask("Enter your [bold]Full Name[/]")
    email = Prompt.ask("Enter your [bold]Email[/]")

    if Confirm.ask(f"Generate key for [cyan]{name} <{email}>[/]?", default=True):
        fingerprint = genBatchGpg(name, email)
        console.print(f"[green]Success:[/] Generated key [bold]{fingerprint}[/]")

        return "pgp", fingerprint
    else:
        raise RuntimeError("Operation cancelled by user.")


def setupSsh():
    """Setup SSH key for Sops encryption."""
    amount = None
    public_keys = checkForSsh()
    if public_keys:
        amount = len(public_keys)
        want_existing_ssh = Confirm.ask(
            f"{len(public_keys)} ssh keys found, do you wish to use one of them?",
            default=True,
        )
        if want_existing_ssh:
            key_choices = [str(k) for k in public_keys]
            selected_key_path = Prompt.ask(
                "Choose a SSH public key to use",
                choices=key_choices,
                default=key_choices[0],
            )

            with open(selected_key_path, "r") as f:
                ssh_key = f.read()

            if not ssh_key:
                raise ValueError("Selected key does not contain a ssh key.")

            return "age", ssh_key

    email = Prompt.ask(
        'Please, insert your email(s), if more than one, sepparate them with "," (like: email1,email2): '
    )
    while True:
        password = Prompt.ask(
            "Please, insert your password, input will be hidden: ", password=True
        )
        check = Prompt.ask("Please, insert it again: ", password=True)
        if password == check:
            break
        console.print("Passwords don't match.")

    loc = Path(os.path.expanduser("~/.ssh/id_ed25519"))

    subprocess.run(
        [
            "ssh-keygen",
            "-B",
            "-t",
            "ed25519",
            "-C",
            email,
            "-N",
            password,
            "-f",
            f"{loc}_{amount}" if amount else f"{loc}",
        ]
    )
    with open(f"{loc}.pub", "r") as f:
        pub_key = f.read()

    return "age", pub_key


def initSecrets():
    "Main Entry point for initializing secrets management with SOPS."
    if not checkDep("sops"):
        raise EnvironmentError(
            "sops is not installed. It is required for this software."
        )

    hasAge = checkDep("age-keygen")
    hasSsh = checkDep("ssh-keygen")
    hasGpg = checkDep("gpg")

    if not hasAge and not hasGpg:
        raise EnvironmentError(
            "Neither gpg nor age installed, both are needed for secure secret handling."
        )

    choices = []
    if hasAge:
        choices.append("age")
        if hasSsh:
            choices.append("pure-ssh")
    if hasGpg:
        choices.append("gpg")

    default = "gpg" if hasGpg else "ssh" if hasSsh else "age"
    console.print(
        Panel(
            "Chaos uses [bold]SOPS[/] for encryption.\nYou need to choose a backend engine to handle the keys.",
            title="Secrets Initialization",
            border_style="green",
        )
    )
    engine = Prompt.ask("Choose an encryption engine", choices=choices, default=default)

    key = ""
    keyValue = ""

    if engine == "age":
        key, keyValue = setupAge()
    elif engine == "gpg":
        key, keyValue = setupGpg()
    elif engine == "pure-ssh":
        key, keyValue = setupSsh()

    configDir = Path(os.path.expanduser("~/.config/chaos"))
    configDir.mkdir(parents=True, exist_ok=True)
    sops_file = configDir / "sops-config.yml"
    sec_file = configDir / "secrets.yml"

    if sops_file.exists():
        if not Confirm.ask(
            f"A sops configuration already exists at [dim]{sops_file}[/]. Overwrite?",
            default=False,
        ):
            console.print("[yellow]Operation cancelled. Keeping existing config.[/]")
            return

    sops_content = {
        "creation_rules": [
            {"path_regex": "(.*)?secrets.*\\.yml$", "key_groups": [{key: [keyValue]}]},
            {
                "path_regex": ".*\\.local/share/chaos/ramblings/.*\\.yml$",
                "key_groups": [{key: [keyValue]}],
            },
        ]
    }

    sec_content = {"user_secrets": {"your_user": {"password": "your_password"}}}

    try:
        with open(sops_file, "w") as f:
            yaml.dump(sops_content, f, default_flow_style=False)

        if not sec_file.exists():
            with open(sec_file, "w") as f:
                yaml.dump(sec_content, f, default_flow_style=False)

        console.print("[cyan]Info:[/] Encrypting initial secrets file...")
        console.print(
            "[dim]Hint: Use chaos secrets edit/chaos check s to both check your secrets and edit your secrets\nchaos check s will print your secrets to your screen to help with automation.[/]"
        )
        subprocess.run(
            [
                "sops",
                "--config",
                str(sops_file),
                "--encrypt",
                "--in-place",
                str(sec_file),
            ],
            check=True,
        )

        console.print(
            f"[bold green]Success![/] SOPS configuration generated at: [dim]{sops_file}[/]"
        )

        global_conf_path = configDir / "config.yml"
        conf = oc.load(global_conf_path) if global_conf_path.exists() else oc.create()
        conf.sops_file = str(sops_file)
        oc.save(conf, global_conf_path)
        console.print("[cyan]Info:[/] Updated global chaos config 'sops_file' path.")

    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Could not encrypt file {sec_file}: {e}") from e
    except Exception as e:
        raise RuntimeError(
            f"Failed to write config file: {e}\nHint: Check if your GPG key is imported or if age keys are correct."
        ) from e
