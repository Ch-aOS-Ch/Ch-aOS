import os
import sys
from typing import cast


def render_ramble(ramble_data, target_name, no_pretty, json, values):
    import json as js

    from omegaconf import OmegaConf
    from rich.align import Align
    from rich.console import Console, Group
    from rich.markdown import Markdown
    from rich.padding import Padding
    from rich.panel import Panel
    from rich.syntax import Syntax
    from rich.text import Text

    if no_pretty:
        if values:
            for value in values:
                p_value = OmegaConf.select(OmegaConf.create(ramble_data), value)
                if not p_value:
                    continue
                print(p_value)
            return
        if not json:
            print(OmegaConf.to_yaml(ramble_data))
            return
        print(js.dumps(ramble_data, indent=2))
        return

    renderables = []
    standard_keys = {"title", "concept", "what", "why", "how", "scripts", "sops"}

    if ramble_data.get("concept"):
        renderables.append(Markdown(f"# Concept: {ramble_data['concept']}"))
        renderables.append(Text("\n"))
    if ramble_data.get("what"):
        renderables.append(Markdown("**What is it?**"))
        renderables.append(Padding.indent(Markdown(ramble_data["what"]), 4))
        renderables.append(Text("\n"))
    if ramble_data.get("why"):
        renderables.append(Markdown("**Why use it?**"))
        renderables.append(Padding.indent(Markdown(ramble_data["why"]), 4))
        renderables.append(Text("\n"))
    if ramble_data.get("how"):
        renderables.append(Markdown("**How it works:**"))
        renderables.append(Padding.indent(Markdown(ramble_data["how"]), 4))
        renderables.append(Text("\n"))

    scripts = ramble_data.get("scripts")
    if scripts:
        renderables.append(Markdown("**Scripts:**"))
        if isinstance(scripts, dict):
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
                formatted_content = OmegaConf.to_yaml(content).strip()
            else:
                formatted_content = str(content)
            renderables.append(Padding.indent(Markdown(formatted_content), 5))
            renderables.append(Text("\n"))

    title = ramble_data.get("title", target_name)
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


def handleRamble(args):
    from rich.console import Console

    console = Console()

    from ...utils import get_providerEps
    from ..dataclasses import (
        ProviderConfigPayload,
        RambleCreatePayload,
        RambleDeletePayload,
        RambleEditPayload,
        RambleEncryptPayload,
        RambleFindPayload,
        RambleMovePayload,
        RambleReadPayload,
        RambleUpdateEncryptPayload,
        SecretsContext,
    )

    team = getattr(args, "team", None)
    sops_file_override = getattr(args, "sops_file_override", None)

    try:
        provider_eps = get_providerEps()

    except Exception as e:
        console.print(f"[bold red]ERROR:[/] Failed to load providers: {e}")
        sys.exit(1)

    provider_classes = [ep.load() for ep in provider_eps] if provider_eps else []

    ephemeral_provider_args = {}
    for provider_class in provider_classes:
        flag_name, _ = provider_class.get_cli_name()
        if flag_name and hasattr(args, flag_name):
            value = getattr(args, flag_name, None)
            if value:
                ephemeral_provider_args[flag_name] = value

    provider_config = ProviderConfigPayload(
        provider=getattr(args, "provider", None),
        ephemeral_provider_args=ephemeral_provider_args,
    )

    ramble_context = SecretsContext(
        team=team,
        sops_file_override=sops_file_override,
        secrets_file_override=None,
        provider_config=provider_config,
        i_know_what_im_doing=False,
    )

    match args.ramble_commands:
        case "read":
            from ...ramble import gatherReadRamble, handleReadRamble

            payload = RambleReadPayload(
                targets=args.targets,
                no_pretty=getattr(args, "no_pretty", False),
                json=getattr(args, "json", False),
                values=getattr(args, "values", None),
                context=ramble_context,
            )

            try:
                request = gatherReadRamble(payload)

            except (ValueError, FileNotFoundError) as e:
                console.print(f"[bold red]ERROR:[/] {e}")
                sys.exit(1)

            if request:
                new_targets = []
                for target in payload.targets:
                    if "." in target:
                        new_targets.append(target)
                        continue

                    field = next(
                        (f for f in request.fields if f.name == f"read_{target}"),
                        None,
                    )
                    if field and field.input_type == "choice":
                        from rich.console import Console

                        console = Console()
                        if not field.choices:
                            console.print(
                                f"[bold red]ERROR:[/] No choices available for '{target}'."
                            )
                            sys.exit(1)

                        from rich.panel import Panel
                        from rich.prompt import Prompt
                        from rich.table import Table

                        table = Table(
                            show_header=True,
                            header_style="bold magenta",
                            border_style="green",
                            show_lines=True,
                        )

                        table.add_column("Index", style="dim", width=6)
                        table.add_column("Ramblings", style="cyan")

                        selected = ""

                        for i in range(len(field.choices)):
                            table.add_row(str(i), field.choices[i])
                        console.print(
                            Panel(table, title=f"Ramble: {payload.targets}"),
                            justify="center",
                        )

                        while (
                            not selected.isdigit()
                            or int(selected) < 0
                            or int(selected) >= len(field.choices)
                        ):
                            selected = Prompt.ask(
                                f"Select a choice for '{target}' (By index)",
                            )
                            if (
                                not selected.isdigit()
                                or int(selected) < 0
                                or int(selected) >= len(field.choices)
                            ):
                                console.print(
                                    f"[bold red]ERROR:[/] Invalid selection. Please enter a number between 0 and {len(field.choices) - 1}."
                                )

                        choice = field.choices[int(selected)]

                        new_targets.append(f"{target}.{choice}")
                payload.targets = new_targets

            result = handleReadRamble(payload)

            if not result.success:
                for err in result.error:
                    console.print(f"[bold red]ERROR:[/] {err}")
                sys.exit(1)

            if result.data is None:
                console.print("[yellow]No data found for the given targets.[/]")
                sys.exit(0)

            for target, data in result.data.items():
                render_ramble(
                    data, target, payload.no_pretty, payload.json, payload.values
                )

        case "create":
            from ...ramble import gatherCreateRamble, handleCreateRamble

            payload = RambleCreatePayload(
                target=args.target,
                encrypt=getattr(args, "encrypt", False),
                keys=getattr(args, "keys", None),
                context=ramble_context,
            )

            try:
                request = gatherCreateRamble(payload)
            except (ValueError, FileNotFoundError) as e:
                console.print(f"[bold red]ERROR:[/] {e}")
                sys.exit(1)

            if request:
                from rich.prompt import Confirm

                # We already know there's only one field here, so we can directly access it
                # Also, we already know that it is a confirmation prompt, so we can skip checking the input type
                field = request.fields[0]
                if Confirm.ask(cast(str, field.prompt), default=field.default):
                    payload.confirmed = True
                else:
                    sys.exit(0)

            result = handleCreateRamble(payload)

            if not result.success:
                for err in result.error:
                    console.print(f"[bold red]ERROR:[/] {err}")
                sys.exit(1)

            for msg in result.message:
                console.print(f"[green]{msg}[/]")

            data = result.data
            if not data or "file_to_edit" not in data:
                console.print(
                    "[bold red]ERROR:[/] No file to edit returned from ramble creation."
                )
                sys.exit(1)
            editor = os.getenv("EDITOR", "nano")
            import subprocess

            try:
                subprocess.run([editor, data["file_to_edit"]], check=True)

            except subprocess.CalledProcessError as e:
                console.print(f"[bold red]ERROR:[/] Ramble editing failed: {e}")
                sys.exit(1)

            if data["should_encrypt"]:
                from ...ramble import handleEncryptRamble

                encrypt_payload = RambleEncryptPayload(
                    target=data["target"],
                    keys=payload.keys,
                    context=payload.context,
                )

                enc_result = handleEncryptRamble(encrypt_payload)

                if enc_result:
                    if not enc_result.success:
                        for err in enc_result.error:
                            console.print(f"[bold red]ERROR:[/] {err}")
                        sys.exit(1)

                    for msg in enc_result.message:
                        console.print(f"[green]{msg}[/]")

        case "edit":
            from ...ramble import gatherEditRamble, handleEditRamble

            payload = RambleEditPayload(
                target=args.target,
                edit_sops_file=getattr(args, "sops", False),
                context=ramble_context,
            )

            try:
                request = gatherEditRamble(payload)
            except (ValueError, FileNotFoundError) as e:
                console.print(f"[bold red]ERROR:[/] {e}")
                sys.exit(1)

            if request:
                from rich.prompt import Prompt

                field = request.fields[0]
                choice = Prompt.ask(cast(str, field.prompt), choices=field.choices)
                payload.target = f"{payload.target}.{choice}"

            result = handleEditRamble(payload)

            if not result.success:
                for err in result.error:
                    console.print(f"[bold red]ERROR:[/] {err}")
                sys.exit(1)

            data = result.data
            if (
                not data
                or "file_path" not in data
                or "is_encrypted" not in data
                or "sops_config" not in data
                or "edit_sops_file" not in data
            ):
                console.print(
                    "[bold red]ERROR:[/] Incomplete data returned from ramble edit."
                )
                sys.exit(1)

            file_path = data["file_path"]
            is_encrypted = data["is_encrypted"]
            sops_config = data["sops_config"]
            edit_sops_file = data["edit_sops_file"]

            target_file = sops_config if edit_sops_file else file_path

            if is_encrypted or edit_sops_file:
                if not sops_config:
                    console.print(
                        "[bold red]ERROR:[/] No sops configuration found for editing encrypted file."
                    )
                    sys.exit(1)

                from chaos.lib.secret_backends.crypto import (
                    check_vault_auth,
                    is_vault_in_use,
                )

                try:
                    if is_vault_in_use(sops_config):
                        is_authed, message = check_vault_auth()
                        if not is_authed:
                            console.print(f"[bold red]ERROR:[/] {message}")
                            sys.exit(1)
                except Exception as e:
                    console.print(f"[bold red]ERROR:[/] Vault check failed: {e}")
                    sys.exit(1)

                from omegaconf import OmegaConf

                from chaos.lib.secret_backends.utils import (
                    _getProvider,
                    _handle_provider_arg,
                )

                GLOBAL_CONFIG_DIR = os.path.expanduser("~/.config/chaos")
                GLOBAL_CONFIG_FILE_PATH = os.path.join(GLOBAL_CONFIG_DIR, "config.yml")
                global_config = (
                    OmegaConf.load(GLOBAL_CONFIG_FILE_PATH)
                    if os.path.exists(GLOBAL_CONFIG_FILE_PATH)
                    else {}
                )

                context = _handle_provider_arg(payload.context, global_config)
                provider = _getProvider(context, global_config)

                import subprocess

                try:
                    if provider:
                        with provider.edit(str(target_file), sops_config) as (
                            cmd,
                            env,
                            pass_fds,
                        ):
                            subprocess.run(
                                cmd,
                                check=True,
                                env=env,
                                pass_fds=pass_fds,
                                shell=True,
                            )
                    else:
                        subprocess.run(
                            ["sops", "--config", sops_config, str(target_file)],
                            check=True,
                        )
                except subprocess.CalledProcessError as e:
                    if e.returncode != 200:
                        console.print(f"[bold red]ERROR:[/] Sops editing failed: {e}")
                        sys.exit(1)
                except FileNotFoundError:
                    console.print(
                        "[bold red]ERROR:[/] `sops` command not found. Please install sops."
                    )
                    sys.exit(1)
            else:
                editor = os.getenv("EDITOR", "nano")
                import subprocess

                try:
                    subprocess.run([editor, str(target_file)], check=True)
                except subprocess.CalledProcessError as e:
                    console.print(f"[bold red]ERROR:[/] Ramble editing failed: {e}")
                    sys.exit(1)
                except FileNotFoundError:
                    console.print(
                        f"[bold red]ERROR:[/] Editor `{editor}` not found. Please set your EDITOR environment variable."
                    )
                    sys.exit(1)

        case "encrypt":
            from ...ramble import handleEncryptRamble

            payload = RambleEncryptPayload(
                target=args.target,
                keys=getattr(args, "keys", None),
                context=ramble_context,
            )

            result = handleEncryptRamble(payload)
            if not result.success:
                for err in result.error:
                    console.print(f"[bold red]ERROR:[/] {err}")
                sys.exit(1)

            for msg in result.message:
                console.print(f"[green]{msg}[/]")

        case "find":
            from ...ramble import handleFindRamble

            payload = RambleFindPayload(
                find_term=getattr(args, "find_term", None),
                tag=getattr(args, "tag", None),
                no_pretty=getattr(args, "no_pretty", False),
                json=getattr(args, "json", False),
                context=ramble_context,
            )

            result = handleFindRamble(payload)

            if result.message:
                for msg in result.message:
                    console.print(f"[cyan]INFO:[/] {msg}")

            if result.error:
                for err in result.error:
                    console.print(f"[bold yellow]WARNING:[/] {err}")

            if result.success and result.data:
                from omegaconf import OmegaConf

                results = result.data
                if payload.no_pretty:
                    if payload.json:
                        import json as js

                        print(
                            js.dumps(
                                OmegaConf.to_container(
                                    OmegaConf.create(results), resolve=True
                                ),
                                indent=2,
                            )
                        )
                    else:
                        print(OmegaConf.to_yaml(OmegaConf.create(results)))

                else:
                    from chaos.lib.display_utils import render_list_as_table

                    title = "[italic][green]Found ramblings:[/][/]"
                    render_list_as_table(results, title)

            elif not result.error:
                console.print("[yellow]Could not find any rambles.[/]")

        case "move":
            from ...ramble import handleMoveRamble

            payload = RambleMovePayload(
                old=args.old,
                new=args.new,
                context=ramble_context,
            )

            result = handleMoveRamble(payload)
            if not result.success:
                for err in result.error:
                    console.print(f"[bold red]ERROR:[/] {err}")
                sys.exit(1)

            for msg in result.message:
                console.print(f"[green]{msg}[/]")

        case "delete":
            from ...ramble import gatherDelRamble, handleDelRamble

            payload = RambleDeletePayload(
                ramble=args.ramble,
                context=ramble_context,
            )
            try:
                request = gatherDelRamble(payload)
            except (ValueError, FileNotFoundError) as e:
                console.print(f"[bold red]ERROR:[/] {e}")
                sys.exit(1)

            if request:
                from rich.prompt import Confirm

                field = request.fields[0]
                if Confirm.ask(cast(str, field.prompt), default=False):
                    payload.confirmed = True
                else:
                    console.print("[green]Alright![/] Aborting.")
                    sys.exit(0)

            result = handleDelRamble(payload)

            if not result.success:
                for err in result.error:
                    console.print(f"[bold red]ERROR:[/] {err}")
                sys.exit(1)

            for msg in result.message:
                console.print(f"[bold red]{msg}[/]")

        case "update":
            from ...ramble import handleUpdateEncryptRamble

            payload = RambleUpdateEncryptPayload(
                context=ramble_context,
            )

            result = handleUpdateEncryptRamble(payload)

            if not result.success:
                for err in result.error:
                    console.print(f"[bold red]ERROR:[/] {err}")
                sys.exit(1)

            if result.message:
                for msg in result.message:
                    console.print(f"[green]{msg}[/]")
            if result.error:
                for err in result.error:
                    console.print(f"[bold yellow]WARNING:[/] {err}")
        case _:
            console.print("Unsupported ramble subcommand.")
