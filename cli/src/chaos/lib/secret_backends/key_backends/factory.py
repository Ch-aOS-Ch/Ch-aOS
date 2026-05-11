from __future__ import annotations

import importlib

from chaos.lib.secret_backends.key_backends.backend import KeyBackend


def get_key_backend(key_type: str) -> KeyBackend:
    """
    Dynamically imports and instantiates the backend only when requested.
    Args:
        key_type (str): The type of the key backend to retrieve.
    Returns:
        KeyBackend: An instance of the requested key backend.
    """
    try:
        if key_type == "gpg":
            key_type = "pgp"

        module = importlib.import_module(
            f"chaos.lib.secret_backends.key_backends.{key_type}"
        )

        class_name = f"{key_type.capitalize()}Backend"
        backend_class = getattr(module, class_name)

        if not issubclass(backend_class, KeyBackend):
            raise ValueError(
                f"Class '{class_name}' in '{key_type}' module does not implement KeyBackend interface."
            )

        return backend_class()
    except ImportError as e:
        raise ValueError(f"Module for key type '{key_type}' not found.") from e

    except AttributeError as e:
        raise ValueError(
            f"Class '{class_name}' not found in '{key_type}' module."
        ) from e
