import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import cast

from chaos.lib.args.dataclasses import (
    RambleEncryptPayload,
    SecretsContext,
)
from chaos.lib.secret_backends.crypto import check_vault_auth, is_vault_in_use
from chaos.lib.secret_backends.utils import (
    _getProvider,
    _handle_provider_arg,
    decrypt_secrets,
)

"""
Module for managing ramble journals and pages.

Yeah, it's like a personal wiki or knowledge base, weird for a DevOps tool right? LMAO
Amazing for keeping track of random knowledge, scripts, concepts, and ideas related to chaos engineering and system administration.
Also, great for documenting secrets management strategies, configurations, and best practices.
"""


def _get_ramble_dir(team) -> Path:
    """
    Validates and returns the ramble directory with the support for teams.
    """
    if team:
        if "." not in team:
            raise ValueError("Must set a company for your team. (company.team.person)")

        parts = team.split(".")
        if len(parts) != 3:
            raise ValueError("Must set a person for your team. (company.team.person)")

        company, team, person = parts

        if ".." in person or person.startswith("/"):
            raise ValueError(f"Invalid person name '{person}'.")

        if ".." in company or company.startswith("/"):
            raise ValueError(f"Invalid company name '{company}'.")

        if ".." in team or team.startswith("/"):
            raise ValueError(f"Invalid team name '{team}'.")

        team_ramble_path = Path(
            os.path.expanduser(f"~/.local/share/chaos/teams/{company}/{team}/")
        )

        if not team_ramble_path.exists():
            raise FileNotFoundError(
                f"Team ramble directory for '{team}' not found at {team_ramble_path}."
            )
        team_ramble_path = team_ramble_path / "ramblings" / person
        return team_ramble_path
    return Path(os.path.expanduser("~/.local/share/chaos/ramblings"))


def is_safe_path(target_path: Path, team) -> bool:
    """
    Validates that the target path is within the ramble directory to prevent path traversal.
    """
    try:
        base_dir = _get_ramble_dir(team).resolve(strict=False)
        resolved_target = target_path.resolve(strict=False)

        if not str(resolved_target).startswith(str(base_dir)):
            raise PermissionError("Path traversal detected. Aborting.")
        return True
    except FileNotFoundError as e:
        raise FileNotFoundError("Ramble directory not found.") from e
    except Exception as e:
        raise RuntimeError(f"Secure validation failed: {e}") from e


def _read_ramble_content(ramble_path, sops_config, context, global_config):
    """
    Reads the content of a ramble file, handling decryption if necessary.
    """
    is_safe_path(ramble_path, context.team)

    if not ramble_path.exists():
        raise FileNotFoundError(f"Ramble page not found: {ramble_path}")

    try:
        from omegaconf import OmegaConf

        data = OmegaConf.load(ramble_path)
        is_encrypted = "sops" in data

        if is_encrypted:
            if not sops_config:
                raise ValueError(
                    "This ramble appears to be encrypted, but no sops configuration was found.\n"
                    "   Provide one with '[cyan]-ss /path/to/.sops.yml[/cyan]' or set a default with '[cyan]chaos set sops /path/to/.sops.yml[/cyan]'."
                )

            if is_vault_in_use(sops_config):
                is_authed, message = check_vault_auth()
                if not is_authed:
                    raise PermissionError(message)

            decrypted_text = None

            new_context = SecretsContext(
                team=context.team,
                sops_file_override=context.sops_file_override,
                secrets_file_override=str(ramble_path),
                provider_config=context.provider_config,
                i_know_what_im_doing=context.i_know_what_im_doing,
            )

            decrypted_text = decrypt_secrets(
                str(ramble_path), sops_config, global_config, new_context
            )

            ramble_data = OmegaConf.create(decrypted_text)
            return ramble_data, decrypted_text
        else:
            ramble_data = data
            with open(ramble_path, "r") as f:
                text = f.read()
            return ramble_data, text

    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Ramble decryption with sops failed.\n{e.stderr}") from e
    except FileNotFoundError as e:
        raise FileNotFoundError(
            "File not found or `sops` command not found. Please check the path and that sops is installed."
        ) from e
    except Exception as e:
        raise RuntimeError(
            f"Could not read or parse ramble file: {ramble_path}\n{e}"
        ) from e


def _print_ramble(
    ramble_path,
    sops_config,
    target_name,
    no_pretty,
    json,
    values,
    context,
    global_config,
):
    """
    Prints the ramble content in a formatted manner.

    Utilizes rich with markdown and syntax highlighting. The Panel is intentionally not that wide, in order to promote pagination.
    """
    ramble_data, _ = _read_ramble_content(
        ramble_path, sops_config, context, global_config
    )
    if no_pretty:
        from omegaconf import OmegaConf

        if values:
            for value in values:
                p_value = OmegaConf.select(ramble_data, value)
                if not p_value:
                    continue
                print(p_value)
            return
        if not json:
            print(OmegaConf.to_yaml(ramble_data))
            return
        import json as js

        print(js.dumps(OmegaConf.to_container(ramble_data, resolve=True), indent=2))
        return

    from rich.align import Align
    from rich.console import Group
    from rich.markdown import Markdown
    from rich.padding import Padding
    from rich.panel import Panel
    from rich.syntax import Syntax

    renderables = []
    standard_keys = {"title", "concept", "what", "why", "how", "scripts", "sops"}
    from rich.text import Text

    if "concept" in ramble_data and ramble_data.concept:
        renderables.append(Markdown(f"# Concept: {ramble_data.concept}"))
        renderables.append(Text("\n"))
    if "what" in ramble_data and ramble_data.what:
        renderables.append(Markdown("**What is it?**"))
        renderables.append(Padding.indent(Markdown(ramble_data.what), 4))
        renderables.append(Text("\n"))
    if "why" in ramble_data and ramble_data.why:
        renderables.append(Markdown("**Why use it?**"))
        renderables.append(Padding.indent(Markdown(ramble_data.why), 4))
        renderables.append(Text("\n"))
    if "how" in ramble_data and ramble_data.how:
        renderables.append(Markdown("**How it works:**"))
        renderables.append(Padding.indent(Markdown(ramble_data.how), 4))
        renderables.append(Text("\n"))

    scripts = ramble_data.get("scripts")
    if scripts:
        renderables.append(Markdown("**Scripts:**"))
        from omegaconf import DictConfig

        if isinstance(scripts, DictConfig):
            knownLangs = [
                "python",
                "c",
                "java",
                "javascript",
                "rust",
                "bash",
                "go",
                "c++",
                "json",
            ]
            for lang, code in scripts.items():
                if lang in knownLangs and code:
                    renderables.append(
                        Padding.indent(
                            Syntax(
                                code,
                                lang,
                                line_numbers=True,
                                theme="monokai",
                                word_wrap=True,
                            ),
                            5,
                        )
                    )
        else:
            renderables.append(
                Padding.indent(
                    Syntax(scripts, "bash", line_numbers=True, theme="monokai"), 5
                )
            )
        renderables.append(Text("\n"))

    other_keys = [k for k in ramble_data.keys() if k not in standard_keys]
    if other_keys:
        for key in other_keys:
            renderables.append(Markdown(f"**{key.replace('_', ' ').title()}:**"))
            content = ramble_data.get(key)

            formatted_content = ""
            if content is None:
                formatted_content = "null"
            elif isinstance(content, str):
                formatted_content = content
            elif isinstance(content, (dict, list)):
                from omegaconf import DictConfig, OmegaConf

                formatted_content = OmegaConf.to_yaml(content).strip()
            else:
                formatted_content = str(content)

            renderables.append(Padding.indent(Markdown(formatted_content), 5))
            renderables.append(Text("\n"))

    title = ramble_data.get("title", target_name)
    from rich.console import Console

    console = Console()
    console.print(
        Align.center(
            Panel(
                Group(*renderables),
                title=f"[bold green]Ramble for '{title}'[/]",
                border_style="green",
                expand=False,
                width=120,
            )
        )
    )


def _process_ramble_target(
    target, sops_file_override, no_pretty, json, values, context, global_config
):
    """
    Handles the ambiguity of ramble targets, allowing for listing pages or reading specific pages.
    """
    from rich.align import Align
    from rich.panel import Panel
    from rich.table import Table

    if ".." in target or "/" in target:
        raise ValueError("Invalid format for ramble.")

    CONFIG_DIR = _get_ramble_dir(context.team)
    parts = target.split(".", 1)
    journal = parts[0]
    path = CONFIG_DIR / journal

    is_list_request = (len(parts) > 1 and parts[1] == "list") or len(parts) == 1

    if is_list_request:
        is_safe_path(path, context.team)
        try:
            from rich.console import Console

            console = Console()
            entries = sorted([f.name for f in path.iterdir() if f.is_file()])
            if not entries:
                console.print(f"[yellow]No pages found in the '{journal}' journal.[/]")
                return

            table = Table(show_lines=True)
            table.add_column("Index", style="cyan")
            table.add_column(f"Pages in {journal}", style="green")
            for i, e in enumerate(entries, start=1):
                table.add_row(str(i), Path(e).stem)
            console.print(
                Align.center(
                    Panel(
                        table,
                        expand=False,
                        border_style="green",
                        title=f"Journal: [cyan]{journal}[/]",
                    )
                )
            )

            inp = console.input("Which page do you want to read? (index) ")
            if not inp:
                console.print("No page selected. Exiting.")
                return

            try:
                indx = int(inp)
                if 1 <= indx <= len(entries):
                    selected_file_name = entries[indx - 1]
                    file_to_read = path / selected_file_name
                    _print_ramble(
                        file_to_read,
                        sops_file_override,
                        Path(selected_file_name).stem,
                        no_pretty,
                        json,
                        values,
                        context,
                        global_config,
                    )
                else:
                    raise IndexError
            except (IndexError, ValueError):
                raise ValueError(f"Invalid index: '{inp}'")

        except FileNotFoundError:
            raise FileNotFoundError(f"Journal not found: {path}.")

    else:
        page = parts[1]
        if not page:
            raise ValueError(f"No page passed for journal '{journal}'.")
        full_path = path / f"{page}.yml"
        _print_ramble(
            full_path,
            sops_file_override,
            target,
            no_pretty,
            json,
            values,
            context,
            global_config,
        )


def handleCreateRamble(payload):
    """
    Creates a new ramble journal or page, and opens it in the user's editor.

    If the ramble passed does not include a dot, the journal name is used for both the journal and page.
    """
    ramble = payload.target
    team = payload.context.team
    CONFIG_DIR = _get_ramble_dir(team)
    shouldEncrypt = payload.encrypt

    if "." in ramble:
        parts = ramble.split(".", 1)
        directory = parts[0]
        page = parts[1]
        if not page or ".." in directory or "/" in directory:
            raise ValueError("Invalid format for journal.page")
        path = CONFIG_DIR / directory
        CONFIG_FILE_PATH = path / f"{page}.yml"

        is_safe_path(CONFIG_FILE_PATH, team)

        baseText = f"""title: {page}
concept:
what:
why:
how:
scripts:
"""
        if not path.exists():
            from rich.console import Console

            console = Console()
            path.mkdir(parents=True, exist_ok=True)
            console.print(f"[yellow]Created new journal: {directory}![/]")

        try:
            from rich.console import Console

            console = Console()
            with open(CONFIG_FILE_PATH, "x") as f:
                f.write(baseText)
            console.print(
                f"[bold green][italic]Page {page} created![/][/] [dim]{directory}.{page}[/]"
            )
        except FileExistsError:
            from rich.console import Console

            console = Console()
            ask = console.input(
                f"[bold yellow]WARNING:[/] page {page} already exists!\n Do you want to go write on it? (y/N) "
            )
            if not ask.lower() == "y":
                return

        editor = os.getenv("EDITOR", "nano")
        try:
            subprocess.run([editor, CONFIG_FILE_PATH], check=True)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Ramble editing failed: {e}") from e

        if shouldEncrypt:
            encrypt_payload = RambleEncryptPayload(
                target=ramble, keys=payload.keys, context=payload.context
            )
            handleEncryptRamble(encrypt_payload)

    else:
        if ".." in ramble or "/" in ramble:
            raise ValueError("Invalid format for journal")

        path = CONFIG_DIR / ramble
        fullPath = path / f"{ramble}.yml"

        is_safe_path(fullPath, team)

        baseText = f"""title: {ramble}
concept:
what:
why:
how:
scripts:
"""
        try:
            from rich.console import Console

            console = Console()
            path.mkdir(parents=True, exist_ok=True)
            console.print(f'[bold green]Journal "{ramble}" created![/]')
            try:
                with open(fullPath, "x") as f:
                    f.write(baseText)
                console.print(
                    f"[bold green][italic]Page {ramble} created![/][/] [dim]{ramble}.{ramble}[/]"
                )
            except FileExistsError:
                ask = console.input(
                    f"[bold yellow]WARNING:[/] page {ramble} already exists!\n Do you want to go write on it? (y/N) "
                )
                if not ask.lower() == "y":
                    return

        except FileExistsError:
            from rich.console import Console

            console = Console()
            console.print(f"[yellow]Journal '{ramble}' already exists.[/]")

            editor = os.getenv("EDITOR", "nano")
            try:
                subprocess.run([editor, fullPath], check=True)
            except subprocess.CalledProcessError as e:
                raise RuntimeError(f"Ramble editing failed: {e}") from e
        if shouldEncrypt:
            encrypt_payload = RambleEncryptPayload(
                target=f"{ramble}.{ramble}", keys=payload.keys, context=payload.context
            )
            handleEncryptRamble(encrypt_payload)
    return


def handleEditRamble(payload):
    """Edits an existing ramble journal or page, handling decryption if necessary."""
    from omegaconf import DictConfig, OmegaConf
    from rich.align import Align
    from rich.panel import Panel
    from rich.table import Table

    ramble = payload.target
    if ".." in ramble or "/" in ramble:
        raise ValueError("Invalid format for ramble.")

    team = payload.context.team
    CONFIG_DIR = _get_ramble_dir(team)

    GLOBAL_CONFIG_DIR = os.path.expanduser("~/.config/chaos")
    GLOBAL_CONFIG_FILE_PATH = os.path.join(GLOBAL_CONFIG_DIR, "config.yml")
    global_config = OmegaConf.create()
    if os.path.exists(GLOBAL_CONFIG_FILE_PATH):
        global_config = OmegaConf.load(GLOBAL_CONFIG_FILE_PATH) or OmegaConf.create()

    global_config = cast(DictConfig, global_config)

    context = _handle_provider_arg(payload.context, global_config)

    sops_file_override = payload.context.sops_file_override or global_config.get(
        "sops_file"
    )

    def edit_file(path, selected_file_name, edit_sops_file):
        file_path = None
        if edit_sops_file:
            if not sops_file_override:
                raise ValueError(
                    "The --sops flag was used, but no sops configuration file was found.\n"
                    "   Provide one with '[cyan]-ss /path/to/.sops.yml[/cyan]' or set a default with '[cyan]chaos set sops /path/to/.sops.yml[/cyan]'."
                )
            file_path = Path(sops_file_override)
        else:
            file_path = path / selected_file_name

        if not edit_sops_file:
            is_safe_path(file_path, team)

        is_encrypted = False
        try:
            data = OmegaConf.load(file_path)
            if "sops" in data:
                is_encrypted = True
        except Exception:
            pass

        if is_encrypted:
            if not sops_file_override:
                raise ValueError(
                    "This ramble appears to be encrypted, but no sops configuration was found.\n"
                    "   Provide one with '[cyan]-ss /path/to/.sops.yml[/cyan]' or set a default with '[cyan]chaos set sops /path/to/.sops.yml[/cyan]'."
                )

            if is_vault_in_use(sops_file_override):
                is_authed, message = check_vault_auth()
                if not is_authed:
                    raise PermissionError(message)

            provider = _getProvider(context, global_config)

            try:
                if provider:
                    provider.edit(str(file_path), sops_file_override)
                else:
                    subprocess.run(
                        ["sops", "--config", sops_file_override, str(file_path)],
                        check=True,
                    )
            except FileNotFoundError:
                raise FileNotFoundError(
                    "The `sops` command was not found. Please install sops to edit encrypted rambles."
                )
            except subprocess.CalledProcessError as e:
                if e.returncode != 200:
                    raise RuntimeError(f"Ramble editing with sops failed: {e}") from e
        else:
            editor = os.getenv("EDITOR", "nano")
            try:
                subprocess.run([editor, str(file_path)], check=True)
            except FileNotFoundError:
                raise FileNotFoundError(
                    f"Editor `{editor}` not found. Please set your EDITOR environment variable."
                )
            except subprocess.CalledProcessError as e:
                raise RuntimeError(f"Ramble editing failed: {e}") from e

    if "." in ramble:
        parts = ramble.split(".", 1)
        directory = parts[0]
        page = parts[1] if parts[1] else directory

        path = CONFIG_DIR / directory
        CONFIG_FILE_PATH = path / f"{page}.yml"

        if not CONFIG_FILE_PATH.exists():
            is_safe_path(path, team)
            raise FileNotFoundError(f"Ramble page not found: {CONFIG_FILE_PATH}")

        edit_file(path, f"{page}.yml", payload.edit_sops_file)
        return

    path = CONFIG_DIR / ramble
    is_safe_path(path, team)

    try:
        entries = sorted([f.name for f in path.iterdir() if f.is_file()])
    except FileNotFoundError:
        raise FileNotFoundError(f"Journal not found: {path}.")

    if not entries:
        from rich.console import Console

        console = Console()
        console.print(f"[yellow]No pages found in the '{ramble}' journal.[/]")
        return

    table = Table(show_lines=True)
    table.add_column("Index", style="cyan")
    table.add_column(f"Pages in {ramble}", style="green")
    for i, e in enumerate(entries, start=1):
        table.add_row(str(i), Path(e).stem)

    from rich.console import Console

    console = Console()
    console.print(
        Align.center(
            Panel(
                table,
                expand=False,
                border_style="green",
                title=f"Journal: [cyan]{ramble}[/]",
            )
        )
    )
    inp = console.input("Which page do you want to edit? (index) ")

    if inp:
        try:
            indx = int(inp)
            if 1 <= indx <= len(entries):
                selected_file_name = entries[indx - 1]
                edit_file(path, selected_file_name, payload.edit_sops_file)
            else:
                raise IndexError
        except (IndexError, ValueError):
            raise ValueError(f"Invalid index: '{inp}'")
    else:
        console.print("No page selected. Exiting.")


def handleEncryptRamble(payload):
    """
    Encrypts specified keys in a ramble page using sops.

    If -k not passed, encrypts everything except base keys.
    The tags key is never encrypted, helping to optimize searching.
    """
    from omegaconf import DictConfig, OmegaConf

    GLOBAL_CONFIG_DIR = os.path.expanduser("~/.config/chaos")
    GLOBAL_CONFIG_FILE_PATH = os.path.join(GLOBAL_CONFIG_DIR, "config.yml")
    global_config = OmegaConf.create()
    if os.path.exists(GLOBAL_CONFIG_FILE_PATH):
        global_config = OmegaConf.load(GLOBAL_CONFIG_FILE_PATH) or OmegaConf.create()
    global_config = cast(DictConfig, global_config)

    sops_file_override = payload.context.sops_file_override or global_config.get(
        "sops_file"
    )

    if not sops_file_override:
        raise ValueError(
            "You need a sops configuration for encryption to work.\n"
            "   Provide one with '[cyan]-ss /path/to/.sops.yml[/cyan]' or set a default with '[cyan]chaos set sops /path/to/.sops.yml[/cyan]'."
        )

    if is_vault_in_use(sops_file_override):
        is_authed, message = check_vault_auth()
        if not is_authed:
            raise PermissionError(message)

    ramble = payload.target
    if ".." in ramble or "/" in ramble:
        raise ValueError("Invalid format for ramble.")

    keys = payload.keys or []
    team = payload.context.team
    CONFIG_DIR = _get_ramble_dir(team)

    if "." not in ramble:
        raise ValueError(
            "You must pass a specific page to be encrypted (e.g., diary.page)."
        )

    parts = ramble.split(".", 1)
    directory = parts[0]
    page = parts[1]
    path = CONFIG_DIR / directory
    fullPath = path / f"{page}.yml"

    is_safe_path(fullPath, team)

    if not fullPath.exists():
        raise FileNotFoundError(f"Ramble page not found: {fullPath}")

    try:
        data = OmegaConf.load(fullPath)
    except Exception as e:
        raise RuntimeError(f"Could not read ramble file: {e}") from e

    keysInData = data.keys()
    baseKeys = ["title", "concept", "sops", "tags"]
    if not keys:
        keys = [str(key) for key in keysInData if key not in baseKeys]

    if not keys:
        from rich.console import Console

        console = Console()
        console.print("[yellow]No new keys to encrypt. Exiting.[/]")
        return

    joinKeys = "|".join(keys)
    regex = f"^({joinKeys})$"
    from rich.console import Console

    console = Console()
    console.print(f"[italic][yellow]Encrypting these keys:[/][cyan] {keys}[/][/]")

    try:
        if "sops" in data:
            new_context = SecretsContext(
                team=payload.context.team,
                sops_file_override=payload.context.sops_file_override,
                secrets_file_override=str(fullPath),
                provider_config=payload.context.provider_config,
                i_know_what_im_doing=payload.context.i_know_what_im_doing,
            )
            result = decrypt_secrets(
                str(fullPath), sops_file_override, global_config, new_context
            )

            with tempfile.NamedTemporaryFile(
                mode="w", delete=False, dir="/dev/shm", suffix=".yml"
            ) as tmp:
                os.chmod(tmp.name, 0o600)
                tmp.write(result)
                tmpPath = tmp.name

            subprocess.run(
                [
                    "sops",
                    "--config",
                    sops_file_override,
                    "--encrypt",
                    "--in-place",
                    "--encrypted-regex",
                    regex,
                    str(tmpPath),
                ],
                check=True,
            )
            shutil.move(tmpPath, fullPath)
        else:
            subprocess.run(
                [
                    "sops",
                    "--config",
                    sops_file_override,
                    "--encrypt",
                    "--in-place",
                    "--encrypted-regex",
                    regex,
                    str(fullPath),
                ],
                check=True,
            )

        console.print(f"[bold green]Successfully encrypted keys in {ramble}[/]")
    except FileNotFoundError:
        raise FileNotFoundError(
            "The `sops` command was not found. Please install sops to encrypt rambles."
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Ramble encryption/decryption failed: {e}") from e


def handleReadRamble(payload):
    """
    Handles the display of the ramble content.
    """
    from omegaconf import DictConfig, OmegaConf

    GLOBAL_CONFIG_DIR = os.path.expanduser("~/.config/chaos")
    GLOBAL_CONFIG_FILE_PATH = os.path.join(GLOBAL_CONFIG_DIR, "config.yml")
    global_config = OmegaConf.create()
    if os.path.exists(GLOBAL_CONFIG_FILE_PATH):
        global_config = OmegaConf.load(GLOBAL_CONFIG_FILE_PATH) or OmegaConf.create()
    global_config = cast(DictConfig, global_config)

    sops_file_override = payload.context.sops_file_override or global_config.get(
        "sops_file"
    )

    for target in payload.targets:
        _process_ramble_target(
            target,
            sops_file_override,
            payload.no_pretty,
            payload.json,
            payload.values,
            payload.context,
            global_config,
        )


def handleFindRamble(payload):
    """
    Searches for rambles containing a specific term, optionally filtered by tag.

    If nothing passed, lists all rambles.
    """
    from omegaconf import DictConfig, OmegaConf

    team = payload.context.team
    RAMBLE_DIR = _get_ramble_dir(team)
    search_term = payload.find_term
    required_tag = payload.tag
    results = []

    GLOBAL_CONFIG_DIR = os.path.expanduser("~/.config/chaos")
    GLOBAL_CONFIG_FILE_PATH = os.path.join(GLOBAL_CONFIG_DIR, "config.yml")
    global_config = {}
    if os.path.exists(GLOBAL_CONFIG_FILE_PATH):
        global_config = OmegaConf.load(GLOBAL_CONFIG_FILE_PATH) or OmegaConf.create()
    global_config = cast(DictConfig, global_config)

    sops_file_override = payload.context.sops_file_override or global_config.get(
        "sops_file"
    )

    for ramble_file in RAMBLE_DIR.rglob("*.yml"):
        try:
            if search_term and required_tag:
                data, text = _read_ramble_content(
                    ramble_file, sops_file_override, payload.context, global_config
                )

                if required_tag:
                    tags = data.get("tags", [])
                    if required_tag not in tags:
                        continue

                if search_term and search_term.lower() not in text.lower():
                    continue

            elif search_term:
                data, text = _read_ramble_content(
                    ramble_file, sops_file_override, payload.context, global_config
                )

                if search_term and search_term.lower() not in text.lower():
                    continue

            elif required_tag:
                data = cast(DictConfig, OmegaConf.load(ramble_file))
                tags = data.get("tags", [])
                if required_tag not in tags:
                    continue

            ramble = ramble_file.parent.name
            page = ramble_file.stem
            results.append(f"{ramble}.{page}")
        except Exception as e:
            from rich.console import Console

            console = Console()
            console.print(
                f"[bold yellow]Skipping {ramble_file.relative_to(RAMBLE_DIR)} due to error: {e}[/]"
            )
            continue

    if not results:
        from rich.console import Console

        console = Console()
        console.print("Could not find any rambles.")
        return

    if payload.no_pretty:
        if payload.json:
            import json as js

            print(
                js.dumps(
                    OmegaConf.to_container(OmegaConf.create(results), resolve=True),
                    indent=2,
                )
            )
            return
        print(OmegaConf.to_yaml(OmegaConf.create(results)))
        return

    title = "[italic][green]Found ramblings:[/][/]"
    from chaos.lib.display_utils import render_list_as_table

    render_list_as_table(results, title)


def handleMoveRamble(payload):
    "Moves or renames a ramble journal or page."
    team = payload.context.team
    RAMBLE_DIR = _get_ramble_dir(team)
    old = payload.old
    new = payload.new

    if ".." in old or "/" in old or ".." in new or "/" in new:
        raise ValueError("Invalid format for ramble.")

    old_is_dir = "." not in old
    new_is_dir = "." not in new

    try:
        source_path = (
            RAMBLE_DIR / old
            if old_is_dir
            else RAMBLE_DIR / old.split(".", 1)[0] / f"{old.split('.', 1)[1]}.yml"
        )
    except IndexError:
        raise ValueError(f"Invalid source format: '{old}'")

    is_safe_path(source_path, team)

    dest_dir_path = (
        RAMBLE_DIR / new if new_is_dir else RAMBLE_DIR / new.split(".", 1)[0]
    )
    dest_file_path = (
        None if new_is_dir else dest_dir_path / f"{new.split('.', 1)[1]}.yml"
    )

    is_safe_path(dest_dir_path, team)
    if dest_file_path:
        is_safe_path(dest_file_path, team)

    if not source_path.exists():
        raise FileNotFoundError(f"No such journal or page: {source_path}")

    if dest_file_path is None or dest_dir_path is None:
        raise ValueError("Destination path could not be determined.")

    if old_is_dir and new_is_dir:
        if dest_dir_path.exists():
            raise FileExistsError(
                f"Destination journal (directory) already exists: {dest_dir_path}"
            )
        from rich.console import Console

        console = Console()
        shutil.move(str(source_path), str(dest_dir_path))
        console.print(f"[green]Successfully moved journal '{old}' to '{new}'[/]")

    elif not old_is_dir and not new_is_dir:
        if dest_file_path.exists():
            raise FileExistsError(
                f"Destination page (file) already exists: {dest_file_path}"
            )

        dest_file_path.parent.mkdir(parents=True, exist_ok=True)

        shutil.move(str(source_path), str(dest_file_path))
        from rich.console import Console

        console = Console()
        console.print(f"[green]Successfully moved page '{old}' to '{new}'[/]")

    elif old_is_dir and not new_is_dir:
        raise ValueError("Cannot move a directory to a singular file.")

    elif not old_is_dir and new_is_dir:
        final_dest_file = dest_dir_path / source_path.name
        is_safe_path(final_dest_file, team)
        if final_dest_file.exists():
            raise FileExistsError(
                f"Page (file) '{source_path.name}' already exists in journal '{new}'"
            )
        dest_dir_path.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source_path), str(final_dest_file))
        new_ramble_name = f"{new}.{source_path.stem}"
        from rich.console import Console

        console = Console()
        console.print(
            f"[green]Successfully moved page '{old}' to '{new_ramble_name}'[/]"
        )


def handleDelRamble(payload):
    "Deletes a ramble journal or page after confirmation."
    team = payload.context.team
    RAMBLE_DIR = _get_ramble_dir(team)
    ramble = payload.ramble

    if ".." in ramble or "/" in ramble:
        raise ValueError("Invalid format for ramble.")

    if "." in ramble:
        parts = ramble.split(".", 1)
        journal = parts[0]
        page = parts[1]
        rambleFile = RAMBLE_DIR / journal / f"{page}.yml"
        is_safe_path(rambleFile, team)
        if not rambleFile.exists():
            raise FileNotFoundError(f"{rambleFile} does not exist.")

        from rich.console import Console
        from rich.prompt import Confirm

        console = Console()
        if Confirm.ask(
            f"Are you [red][italic]sure[/][/] you want to delete {ramble}?",
            default=False,
        ):
            console.print(f"[bold red]Removing {ramble}.[/]")
            os.remove(rambleFile)
        else:
            console.print("[green]Alright![/] Aborting.")
    else:
        ramblePath = RAMBLE_DIR / ramble
        is_safe_path(ramblePath, team)
        if not ramblePath.exists():
            raise FileNotFoundError(f"{ramblePath} does not exist.")

        from rich.console import Console
        from rich.prompt import Confirm

        console = Console()

        if Confirm.ask(
            f"Are you [red][italic]sure[/][/] you want to delete the entire journal '{ramble}'?",
            default=False,
        ):
            console.print(f"[bold red]Removing {ramble}.[/]")
            shutil.rmtree(ramblePath)
        else:
            console.print("[green]Alright![/] Aborting.")


def handleUpdateEncryptRamble(payload):
    "Updates encryption keys for all encrypted rambles in the ramble directory."
    from omegaconf import DictConfig, OmegaConf

    team = payload.context.team
    RAMBLE_DIR = _get_ramble_dir(team)
    GLOBAL_CONFIG_DIR = os.path.expanduser("~/.config/chaos")
    GLOBAL_CONFIG_FILE_PATH = os.path.join(GLOBAL_CONFIG_DIR, "config.yml")
    global_config = {}
    updated_count = 0

    if os.path.exists(GLOBAL_CONFIG_FILE_PATH):
        global_config = OmegaConf.load(GLOBAL_CONFIG_FILE_PATH) or OmegaConf.create()
    global_config = cast(DictConfig, global_config)

    sops_file_override = payload.context.sops_file_override or global_config.get(
        "sops_file"
    )

    if sops_file_override and is_vault_in_use(sops_file_override):
        is_authed, message = check_vault_auth()
        if not is_authed:
            raise PermissionError(message)

    context = _handle_provider_arg(payload.context, global_config)
    provider = _getProvider(context, global_config)

    for ramble_file in RAMBLE_DIR.rglob("*.yml"):
        is_safe_path(ramble_file, team)
        try:
            data = OmegaConf.load(ramble_file)
            if "sops" in data:
                if not sops_file_override:
                    raise ValueError(
                        "An encrypted ramble was found, but no sops configuration was provided.\n"
                        "   Provide one with '[cyan]-ss /path/to/.sops.yml[/cyan]' or set a default with '[cyan]chaos set sops /path/to/.sops.yml[/cyan]'."
                    )

                from rich.console import Console

                console = Console()
                console.print(
                    f"Checking for key updates in [cyan]{ramble_file.relative_to(RAMBLE_DIR)}[/]..."
                )
                if provider:
                    provider.updatekeys(str(ramble_file), sops_file_override)
                else:
                    subprocess.run(
                        [
                            "sops",
                            "--config",
                            sops_file_override,
                            "updatekeys",
                            "-y",
                            str(ramble_file),
                        ],
                        capture_output=True,
                        text=True,
                        check=True,
                    )
                updated_count += 1
        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"Ramble key update with sops failed for {ramble_file}.\n{e.stderr}"
            ) from e
        except FileNotFoundError:
            raise FileNotFoundError(
                "`sops` command not found. Please ensure sops is installed and in your PATH."
            )
        except Exception:
            from rich.console import Console

            console = Console()
            console.print(
                f"[bold yellow]Warning:[/] Could not read or parse ramble file: {ramble_file}. Skipping."
            )
            continue

    if updated_count > 0:
        from rich.console import Console

        console = Console()
        console.print(
            f"\n[bold green]Processed {updated_count} encrypted ramble(s).[/]"
        )
    else:
        from rich.console import Console

        console = Console()
        console.print("[yellow]No encrypted ramble files found to update.[/]")
