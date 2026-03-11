from chaos.lib.args.dataclasses import (
    ApplyPayload,
    DataGatherPayload,
    DataGatherRequest,
    ResultPayload,
)
from chaos.lib.roles.role import Role


def handle_verbose(payload: ApplyPayload) -> None:
    """Handle verbosity levels for logging"""
    import logging

    log_level = None
    if payload.verbose:
        if payload.verbose == 1:
            log_level = logging.WARNING
        elif payload.verbose == 2:
            log_level = logging.INFO
        elif payload.verbose == 3:
            log_level = logging.DEBUG
    elif payload.v == 1:
        log_level = logging.WARNING
    elif payload.v == 2:
        log_level = logging.INFO
    elif payload.v == 3:
        log_level = logging.DEBUG

    if log_level:
        logging.basicConfig(level=log_level, format="%(levelname)s: %(message)s")


def gather_apply(
    payload: ApplyPayload,
) -> tuple[DataGatherRequest | None, ResultPayload | None]:

    i_know, sudo_password = _handle_password(payload, payload.i_know_what_im_doing)
    request = DataGatherRequest(name="apply", fields=[])
    result = ResultPayload(success=True, message=[], error=[], data={})
    if not sudo_password:
        request.fields.append(
            DataGatherPayload(
                prompt="Please, enter your sudo password:",
                name="sudo_password",
                input_type="secret",
                required=True,
            )
        )
    else:
        result.data["sudo_password"] = sudo_password

    try:
        loaded_roles = _load_role_eps(payload.tags)
    except ValueError as e:
        result.success = False
        result.error.append(str(e))
        return None, result

    for role in payload.tags:
        if role not in loaded_roles:
            result.success = False
            result.error.append(f"Role '{role}' could not be loaded.")
            continue

        role_class = loaded_roles[role]

        # caching the role class for later use
        # (avoid double import and loading, since we will be applying the same role later, this is just the gathering phase.)
        result.data[role] = role_class

        if role_class.needs_secrets and not i_know:
            if not role_class.necessary_secret_dict_keys:
                result.success = False
                result.error.append(
                    f"Role '{role}' requires secrets but does not specify necessary_secret_dict_keys."
                )
                continue

            request.fields.append(
                DataGatherPayload(
                    prompt=f"Role '{role}' is asking for the secrets:\n{role_class.necessary_secret_dict_keys}\nDo you want to proceed? (y/n)",
                    default=False,
                    name=f"{role}_confirm",
                    input_type="boolean",
                )
            )

    return request, result


def _handle_password(payload: ApplyPayload, ikwid: bool) -> tuple[bool, str | None]:
    import sys
    from pathlib import Path

    from .utils import validate_path

    sudo_password = None
    i_know = ikwid
    if payload.sudo_password_file:
        validate_path(payload.sudo_password_file)

        sudo_file = Path(payload.sudo_password_file)
        if not sudo_file.exists():
            raise FileNotFoundError(f"Sudo password file not found: {sudo_file}")

        if not sudo_file.is_file():
            raise ValueError(f"Sudo password file path is not a file: {sudo_file}")

        with open(sudo_file, "r") as f:
            sudo_password = f.read().strip()

    if payload.password:
        if not sys.stdin.isatty():
            sudo_password = sys.stdin.read().strip()
            ikwid = True
        else:
            sudo_password = payload.password
    elif payload.password is not None:
        sudo_password = payload.password.strip()

    return i_know, sudo_password


def _load_role_eps(role_names: list[str]) -> dict[str, Role]:
    from chaos.lib.utils import get_roleEps

    role_eps = get_roleEps()
    loaded_roles = {}
    for role_name in role_names:
        matching_eps = [ep for ep in role_eps if ep.name == role_name]
        if not matching_eps:
            raise ValueError(f"Role '{role_name}' not found among available plugins.")
        elif len(matching_eps) > 1:
            raise ValueError(
                f"Multiple plugins found for role '{role_name}'. Please specify a unique name."
            )
        else:
            loaded_roles[role_name] = matching_eps[0].load()
    return loaded_roles
