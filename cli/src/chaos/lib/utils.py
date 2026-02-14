from functools import lru_cache


def validate_path(path: str):
    """Validates given file system path."""
    import os

    if (
        ".." in path
        or "//" in path
        or (path.startswith("/") and not path.startswith(os.path.expanduser("~")))
    ):
        raise ValueError(f"Invalid file path {path}.")


def checkDep(bin):
    """This just checks if a SHELL COMMAND exists in the system PATH."""
    import shutil

    path = shutil.which(bin)
    if path is None:
        return False
    return True


@lru_cache(maxsize=None)
def get_providerEps():
    from importlib.metadata import EntryPoint

    from chaos.lib.plugDiscovery import get_plugins

    providers = get_plugins()[4]
    provider_eps = []
    if providers:
        for name, value in providers.items():
            provider_eps.append(
                EntryPoint(name=name, value=value, group="chaos.providers")
            )
    return provider_eps
