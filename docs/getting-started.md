# Getting Started

This guide will walk you through the initial setup of the `chaos` CLI and its core components.

## Installation

!!! warning
    Currently, Ch-aOS is not available on package managers like `pip` or AUR (I'm working on it ok?) using the following command:

```bash
curl -LsSf https://raw.githubusercontent.com/Ch-aOS-Ch/Ch-aOS/refs/heads/main/install.sh | sudo bash
```

## Verify Installation

After installation, you can verify that the CLI is working and see the available commands.

1.  **Update the plugin cache:**
    Run the following command to make sure `chaos` discovers all installed plugins.
    ```bash
    chaos -u
    ```

2.  **View the help menu:**
    ```bash
    chaos -h
    ```

3.  **Check available components:**
    You can list all the roles, explanations, and aliases provided by your installed plugins.
    ```bash
    chaos check roles
    chaos check explanations
    ```

You are now ready to start using Ch-aOS!
