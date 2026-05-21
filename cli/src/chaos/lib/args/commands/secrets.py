import sys
from contextlib import contextmanager

from chaos.lib.args.dataclasses import ResultPayload


@contextmanager
def interactive_ephemeral_file(key_type: str):
    """Opens a secure, RAM-based temporary file in the user's editor.

    Args:
        key_type (str): The type of key being requested (e.g., 'age', 'vault').

    Yields:
        str: The path to the ephemeral file.
    """
    import os
    import platform
    import subprocess
    import sys
    import tempfile
    from contextlib import ExitStack
    from pathlib import Path

    from chaos.lib.secret_backends.utils import mac_ram_disk

    is_mac = platform.system() == "Darwin"

    with ExitStack() as stack:
        if is_mac:
            ram_dir = stack.enter_context(mac_ram_disk())
            temp_dir = stack.enter_context(
                tempfile.TemporaryDirectory(dir=ram_dir, prefix="chaos-export-")
            )
        else:
            shm_dir = "/dev/shm"
            if not os.path.exists(shm_dir) or not os.access(shm_dir, os.W_OK):
                raise RuntimeError("Shared memory (/dev/shm) is not available.")
            temp_dir = stack.enter_context(
                tempfile.TemporaryDirectory(dir=shm_dir, prefix="chaos-export-")
            )

        temp_path = Path(temp_dir) / f"{key_type}_key.txt"
        temp_path.touch(mode=0o600)

        content = f"""\n
# ---- Ch-aOS Interactive Export ----
# Please paste your {key_type.upper()} key above this footer.
# Save and exit your editor when done.
# This file exists entirely in volatile memory (RAM).
"""

        if not sys.stdin.isatty():
            content = f"{sys.stdin.read()}\n{content}"

        with open(temp_path, "w") as f:
            f.write(content)

        if not sys.stdin.isatty():
            editor = os.getenv("EDITOR", "nano")
            try:
                subprocess.run([editor, str(temp_path)], check=True)
            except subprocess.CalledProcessError:
                raise RuntimeError("Editor was closed with an error.")

        yield str(temp_path)


def handleSecrets(args):  # noqa: C901
    from rich.console import Console

    console = Console()
    try:
        from chaos.lib.args.dataclasses import (
            ProviderConfigPayload,
            SecretsCatPayload,
            SecretsContext,
            SecretsEditPayload,
            SecretsExportPayload,
            SecretsImportPayload,
            SecretsListPayload,
            SecretsPrintPayload,
            SecretsRotatePayload,
            SecretsSetShamirPayload,
        )
        from chaos.lib.secret_backends.utils import get_sops_files
        from chaos.lib.utils import get_providerEps

        team = getattr(args, "team", None)
        sops_file_override = getattr(args, "sops_file_override", None)
        secrets_file_override = getattr(args, "secrets_file_override", None)

        _, _, global_config = get_sops_files(
            sops_file_override, secrets_file_override, team
        )

        provider_eps = get_providerEps()
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

        context = SecretsContext(
            team=team,
            sops_file_override=sops_file_override,
            secrets_file_override=secrets_file_override,
            provider_config=provider_config,
            i_know_what_im_doing=getattr(args, "i_know_what_im_doing", False),
        )

        match args.secrets_commands:
            case "export":
                import time
                from contextlib import ExitStack

                from ...secrets import handleExportSec

                key_file_val = getattr(args, "key_file", None)
                fingerprints = getattr(args, "fingerprints", None)

                with ExitStack() as stack:
                    if args.key_type == "age":
                        if not key_file_val:
                            console.print(
                                "[yellow]No key file provided. Opening a secure RAM-based file to paste your AGE key...[/]"
                            )
                            time.sleep(1)
                            key_file_val = stack.enter_context(
                                interactive_ephemeral_file("age")
                            )

                    if args.key_type == "vault":
                        if not key_file_val:
                            console.print(
                                "[yellow]No token file provided. Opening a secure RAM-based file to paste your Vault token...[/]"
                            )
                            time.sleep(1)
                            key_file_val = stack.enter_context(
                                interactive_ephemeral_file("vault")
                            )

                    if args.key_type == "gpg":
                        if not getattr(args, "fingerprints", None):
                            console.print(
                                "[yellow]No fingerprints provided. Opening a secure RAM-based file to paste your fingerprints...[/]"
                            )
                            fingerprints = []
                            time.sleep(1)
                            file_fps = stack.enter_context(
                                interactive_ephemeral_file("gpg")
                            )
                            with open(file_fps, "r") as f:
                                lines = f.readlines()

                            for line in lines:
                                if not line.startswith("#"):
                                    line = line.strip()
                                    if line:
                                        fingerprints.append(line)

                    provider_name = args.export_commands
                    provider_class = None
                    if provider_eps:
                        for ep in provider_eps:
                            p_class = ep.load()
                            _, p_cli_name = p_class.get_cli_name()
                            if p_cli_name == provider_name:
                                provider_class = p_class
                                break

                    if not provider_class:
                        raise ValueError(f"Provider '{provider_name}' not found.")

                    export_arg_names = provider_class.get_export_arg_names()
                    kwargs = {
                        name: getattr(args, name)
                        for name in export_arg_names
                        if hasattr(args, name)
                    }

                    provider_specific_args = provider_class.build_export_args(**kwargs)

                    payload = SecretsExportPayload(
                        provider_name=args.export_commands,
                        key_type=args.key_type,
                        no_import=getattr(args, "no_import", False),
                        save_to_config=getattr(args, "save_to_config", False),
                        item_name=getattr(args, "item_name", None),
                        keys=key_file_val,
                        vault_addr=getattr(args, "vault_addr", None),
                        fingerprints=fingerprints,
                        provider_specific_args=provider_specific_args,
                    )

                    result = handleExportSec(payload, global_config)

                    if result.message:
                        for msg in result.message:
                            console.print(msg)

                    if result.error:
                        for err in result.error:
                            console.print(f"[bold red]ERROR:[/] {err}")

                    if not result.success:
                        sys.exit(1)

            case "import":
                from ...secrets import gatherImportSec, handleImportSec

                provider_name = args.import_commands
                provider_class = None
                if provider_eps:
                    for ep in provider_eps:
                        p_class = ep.load()
                        _, p_cli_name = p_class.get_cli_name()
                        if p_cli_name == provider_name:
                            provider_class = p_class
                            break

                if not provider_class:
                    raise ValueError(f"Provider '{provider_name}' not found.")

                import_arg_names = provider_class.get_import_arg_names()
                kwargs = {
                    name: getattr(args, name)
                    for name in import_arg_names
                    if hasattr(args, name)
                }

                provider_specific_args = provider_class.build_import_args(**kwargs)

                payload = SecretsImportPayload(
                    provider_name=args.import_commands,
                    key_type=args.key_type,
                    item_id=getattr(args, "item_id", None),
                    provider_specific_args=provider_specific_args,
                )

                request = gatherImportSec(payload)
                if request:
                    from rich.prompt import Confirm

                    field = request.fields[0]
                    if Confirm.ask(str(field.prompt), default=field.default):
                        payload.confirmed = True
                    else:
                        console.print("[green]Alright![/] Aborting.")
                        return

                result = handleImportSec(payload, global_config)

                if result.message:
                    for msg in result.message:
                        console.print(msg)

                if result.error:
                    for err in result.error:
                        console.print(f"[bold red]ERROR:[/] {err}")

                if not result.success:
                    sys.exit(1)

            case "rotate-add":
                from ...secrets import gatherRotateAdd, handleRotateAdd

                payload = SecretsRotatePayload(
                    type=args.type,
                    keys=args.key_file,
                    context=context,
                    index=getattr(args, "index", None),
                    pgp_server=getattr(args, "pgp_server", None),
                    create=getattr(args, "create", False),
                )

                request = gatherRotateAdd(payload)
                if request:
                    from rich.prompt import Confirm

                    for field in request.fields:
                        if field.name == "update_confirmed":
                            if Confirm.ask(str(field.prompt), default=field.default):
                                payload.update_confirmed = True

                result = handleRotateAdd(payload)

                if not result.success and result.error:
                    for err in result.error:
                        console.print(f"[bold red]ERROR:[/] {err}")
                    for msg in result.message:
                        console.print(msg)
                    sys.exit(1)

                if result.error:
                    for err in result.error:
                        console.print(f"[bold red]ERROR:[/] {err}")

                if result.message:
                    for msg in result.message:
                        console.print(msg)

            case "rotate-rm":
                from ...secrets import gatherRotateRemove, handleRotateRemove

                payload = SecretsRotatePayload(
                    type=args.type,
                    keys=args.key_file,
                    context=context,
                    index=getattr(args, "index", None),
                )

                request = gatherRotateRemove(payload)
                if request:
                    from rich.prompt import Confirm

                    for field in request.fields:
                        if field.name == "update_confirmed":
                            if Confirm.ask(str(field.prompt), default=field.default):
                                payload.update_confirmed = True

                result = handleRotateRemove(payload)
                if result.message:
                    for msg in result.message:
                        console.print(msg)
                if result.error:
                    for err in result.error:
                        console.print(f"[bold red]ERROR:[/] {err}")
                if not result.success:
                    sys.exit(1)

            case "list":
                from ...secrets import listFp

                payload = SecretsListPayload(
                    type=args.type,
                    context=context,
                    no_pretty=getattr(args, "no_pretty", False),
                    json=getattr(args, "json", False),
                    value=getattr(args, "value", False),
                )

                result: ResultPayload = listFp(payload)
                results = result.data

                if result.error:
                    for error in result.message:
                        console.print(f"[bold red][italic]ERROR:[/] {error}")
                        return

                if results:
                    if payload.no_pretty:
                        if payload.value:
                            print("\n".join(results))
                            return

                        elif payload.json:
                            import json

                            print(json.dumps(list(results), indent=2))
                            return

                        else:
                            from omegaconf import OmegaConf

                            print(OmegaConf.to_yaml(list(results)))
                            return

                    from chaos.lib.display_utils import render_list_as_table

                    title = f"[italic][green]Found {payload.type} Keys:[/][/]"
                    render_list_as_table(list(results), title)
                else:
                    from rich.console import Console

                    console = Console()
                    console.print(f"[cyan]INFO:[/] No {payload.type} keys to be shown.")

            case "edit":
                from ...secrets import handleSecEdit

                payload = SecretsEditPayload(
                    context=context, edit_sops_file=getattr(args, "sops", False)
                )

                result = handleSecEdit(payload)

                if result.error:
                    for err in result.error:
                        console.print(f"[bold red]ERROR:[/] {err}")

                    if result.message:
                        for msg in result.message:
                            console.print(msg)

                    sys.exit(1)

                import os
                import subprocess

                if result.data is None:
                    raise ValueError("No data returned for sops file path.")

                if not result.data.get("sops_file") or not result.data.get(
                    "secrets_file"
                ):
                    raise ValueError("Missing required data for editing secrets.")

                try:
                    if payload.edit_sops_file:
                        editor = os.getenv("EDITOR", "nano")

                        subprocess.run([editor, result.data["sops_file"]], check=True)

                    elif result.data["provider"]:
                        with result.data["provider"].edit(
                            result.data["secrets_file"], result.data["sops_file"]
                        ) as (cmd, env, pass_fds):
                            subprocess.run(
                                cmd,
                                check=True,
                                env=env,
                                pass_fds=pass_fds,
                                shell=True,
                            )

                    else:
                        subprocess.run(
                            [
                                "sops",
                                "--config",
                                result.data["sops_file"],
                                result.data["secrets_file"],
                            ],
                            check=True,
                        )

                except subprocess.CalledProcessError as e:
                    from rich.console import Console

                    console = Console()
                    if e.returncode == 200:  # sops exit code for no changes
                        return
                    else:
                        raise RuntimeError(
                            f"SOPS editing failed with exit code {e.returncode}."
                        ) from e
                except FileNotFoundError as e:
                    raise FileNotFoundError(
                        "'sops' command not found. Please ensure sops is installed and in your PATH."
                    ) from e

            case "set-shamir":
                from ...secrets import gatherSetShamir, handleSetShamir

                payload = SecretsSetShamirPayload(
                    index=args.index, share=args.share, context=context
                )

                request = gatherSetShamir(payload)
                if request:
                    from rich.prompt import Confirm

                    for field in request.fields:
                        if field.name == "confirmed":
                            if Confirm.ask(str(field.prompt), default=field.default):
                                payload.confirmed = True
                            else:
                                console.print("[green]Alright![/] Aborting.")
                                sys.exit(0)
                        elif field.name == "update_confirmed":
                            if Confirm.ask(str(field.prompt), default=field.default):
                                payload.update_confirmed = True

                result = handleSetShamir(payload)
                if result.message:
                    for msg in result.message:
                        console.print(msg)
                if result.error:
                    for err in result.error:
                        console.print(f"[bold red]ERROR:[/] {err}")
                if not result.success:
                    sys.exit(1)

            case "print":
                from ...secret_backends.utils import zero_out
                from ...secrets import handleSecPrint

                payload = SecretsPrintPayload(
                    context=context,
                    print_sops_file=getattr(args, "sops", False),
                    as_json=getattr(args, "json", False),
                )

                result = handleSecPrint(payload)

                if result.error:
                    for err in result.error:
                        console.print(f"[bold red]ERROR:[/] {err}")
                    sys.exit(1)

                if not result.data or not result.data.get("dec"):
                    console.print("[cyan]INFO:[/] No secrets found to print.")
                    return
                decrypted_output = result.data.get("dec", "")

                if payload.as_json:
                    import json

                    from omegaconf import OmegaConf

                    decrypted_output = json.dumps(
                        OmegaConf.to_container(
                            OmegaConf.create(decrypted_output), resolve=True
                        ),
                        indent=2,
                    )
                    return

                print(decrypted_output)
                zero_out(decrypted_output)

            case "cat":
                from ...secrets import handleSecCat

                payload = SecretsCatPayload(
                    keys=args.keys,
                    context=context,
                    cat_sops_file=getattr(args, "sops", False),
                    as_json=getattr(args, "json", False),
                    value_only=getattr(args, "value", False),
                )

                result = handleSecCat(payload)

                if not result.success:
                    if result.error:
                        for err in result.error:
                            console.print(f"[bold red]ERROR:[/] {err}")

                for result_msg in result.message:
                    console.print(result_msg)

                for error in result.error:
                    console.print(f"[bold red]ERROR:[/] {error}")

                import json

                from omegaconf import DictConfig, ListConfig, OmegaConf

                if not result.data or not result.data.get("values"):
                    console.print("[cyan]INFO:[/] No secrets found to show.")
                    return
                for key, value in result.data["values"]:
                    if payload.value_only:
                        print(value)
                        continue

                    if not payload.as_json:
                        if isinstance(value, (DictConfig, ListConfig)):
                            container = OmegaConf.create({key: value})
                            print(f"{OmegaConf.to_yaml(container)}")
                        else:
                            output_value = str(value)
                            print(f"{key}: {output_value}")
                    else:
                        print(
                            json.dumps(
                                OmegaConf.to_container(OmegaConf.create({key: value})),
                                indent=2,
                            )
                        )

            case _:
                console.print("Unsupported secrets subcommand.")
    except (
        ValueError,
        FileNotFoundError,
        PermissionError,
        RuntimeError,
        EnvironmentError,
    ) as e:
        console.print(f"[bold red]ERROR:[/] {e}")
        sys.exit(1)
