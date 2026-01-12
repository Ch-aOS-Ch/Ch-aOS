# Provider Plugin Development

A "Provider" plugin integrates Ch-aOS with an external secret manager, enabling the secure storage and retrieval of master encryption keys. This guide details how to build a custom provider plugin.

## Core Concepts

A provider plugin is a Python package that:
1.  Implements the `Provider` abstract base class from `chaos.lib.secret_backends.base`.
2.  Registers itself using the `chaos.providers` entry point and the Provider required functions.

The `Provider` class defines a standard interface for how `chaos` interacts with different secret manager CLIs. Its main purpose is to abstract the logic for:
-   Reading secrets (e.g., `bw get notes <id>`, `op read op://...`).
-   Writing/exporting secrets (e.g., `bw create item`, `op item create`).
-   Checking the status of the provider's CLI tool (e.g., ensuring it's installed and authenticated).
-   That's it! The rest of the integration is handled by the base class.

## Implementing the `Provider` Class

You must create a class that inherits `chaos.lib.secret_backends.base`'s Provider class and implement its abstract methods.

### `pyproject.toml` Entry Point

First, register your class in your plugin's `pyproject.toml`:

```toml
[project.entry-points."chaos.providers"]
my-provider = "my_chaos_provider.main:MyProvider"
```

### Required Methods

Here is a skeleton of the `Provider` class you need to implement.

```python
# src/my_chaos_provider/main.py

import argparse
from typing import Tuple
from chaos.lib.secret_backends.base import Provider
from chaos.lib.utils import checkDep

class MyProvider(Provider):
    @staticmethod
    def get_cli_name() -> Tuple[str, str]:
        """
        Returns the flag name and the config name for the provider.
        - The first element is the attribute name for the direct CLI flag (e.g., '--from-my-provider' becomes 'from_my_provider').
        - The second element is the key used in the chaos config file.
        """
        return "from_my_provider", "my_provider"

    @staticmethod
    def register_flags(parser: argparse.ArgumentParser) -> None:
        """
        Register a direct, ephemeral flag for your provider.
        """
        parser.add_argument(
            '--from-my-provider', '-m',
            type=str,
            nargs=2,
            metavar=('ITEM_ID', 'KEY_TYPE'),
            help='Retrieve keys from MyProvider ephemerally.'
        )

    @staticmethod
    def register_export_subcommands(subparser: argparse._SubParsersAction) -> argparse.ArgumentParser:
        """
        Register subcommands for `chaos secrets export`.
        """
        export_parser = subparser.add_parser('my-provider', help="MyProvider export options")
        # Add arguments specific to exporting to your provider
        export_parser.add_argument('--some-export-option', help="An example export option.")
        return export_parser

    @staticmethod
    def register_import_subcommands(subparser: argparse._SubParsersAction) -> argparse.ArgumentParser:
        """
        Register subcommands for `chaos secrets import`.
        """
        import_parser = subparser.add_parser('my-provider', help="MyProvider import options")
        return import_parser

    def get_ephemeral_key_args(self) -> tuple[str, str] | None:
        """
        Return the arguments passed to the direct flag (e.g., from '--from-my-provider').
        """
        return self.args.from_my_provider

    def check_status(self) -> Tuple[bool, str]:
        """
        Check if the provider's CLI tool is installed and authenticated.
        Raise an exception or return (False, "error message") if not ready.
        """
        if not checkDep("my-provider-cli"):
            raise EnvironmentError("MyProvider CLI is not installed.")
        # Add authentication checks here
        return True, "MyProvider is ready."

    def readKeys(self, item_id: str) -> str:
        """
        Implement the logic to read a secret from the provider's CLI or API.
        This method should return the raw content of the secret (e.g., the notes field).
        """
        # Example:
        # result = subprocess.run(
        #     ["my-provider-cli", "get", "secret", item_id],
        #     capture_output=True, text=True, check=True
        # )
        # return result.stdout.strip()
        raise NotImplementedError

    def export_secrets(self) -> None:
        """
        Implement the logic to write a secret to the provider.
        Access arguments via `self.args`.
        """
        # key_type = self.args.key_type
        # key_content = "..." # Prepare the key content
        # subprocess.run(
        #     ["my-provider-cli", "create", "secret", "--notes", key_content, ...],
        #     check=True
        # )
        raise NotImplementedError
```

### Ephemeral Environment

The most complex part is `setupEphemeralEnv`, which is already partially implemented in the base class. The base implementation uses the `get_ephemeral_key_args` and `readKeys` methods you define, along with helper functions, to prepare an environment for `sops`.

Overriding setupEphemeralEnv is bad practice, since the main Provider class already sets the ephemeral environment safely and securely for you. If your provider requires special handling, consider overriding `get_ephemeral_key_args` and `readKeys` instead, or requiring additional arguments in `register_flags`, or even requiring previously authentication in `check_status`.
