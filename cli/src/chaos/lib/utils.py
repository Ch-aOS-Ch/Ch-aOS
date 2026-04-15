"""General utility functions for path validation, dependency checking, and plugin entrypoint retrieval."""

from functools import lru_cache


def validate_path(path: str):
    """Validates given file system path.

    Args:
        path (str): The file system path to check.

    Raises:
        ValueError: If the path contains relative directory jumping commands or invalid multiple slashes.
    """
    if ".." in path or "//" in path:
        raise ValueError(f"Invalid file path {path}.")


def checkDep(bin: str) -> bool:
    """Checks if a shell command exists in the system PATH.

    Args:
        bin (str): The name of the binary/executable to look for.

    Returns:
        bool: True if the binary is accessible in the PATH, False otherwise.
    """
    import shutil

    safe_path = "/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:/opt/homebrew/bin"

    path = shutil.which(bin, path=safe_path)
    if path is None:
        return False
    return True


@lru_cache(maxsize=None)
def get_providerEps():
    """Retrieves and caches the provider EntryPoints registered under the 'chaos.providers' group.

    Returns:
        list[EntryPoint]: A list of entry point objects matching external provider plugins.
    """
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


@lru_cache(maxsize=None)
def get_roleEps():
    """Retrieves and caches the role EntryPoints registered under the 'chaos.roles' group.

    Returns:
        list[EntryPoint]: A list of entry point objects matching external role plugins.
    """
    from importlib.metadata import EntryPoint

    from chaos.lib.plugDiscovery import get_plugins

    roles = get_plugins()[0]
    role_eps = []
    if roles:
        for name, value in roles.items():
            role_eps.append(EntryPoint(name=name, value=value, group="chaos.roles"))
    return role_eps
