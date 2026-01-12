# Getting Started

This guide will walk you through the initial setup of the `chaos` CLI and its core components.

## Installation

!!! warning
    Currently, Ch-aOS is not available on package managers like `pip` or AUR (I'm working on it ok?) The only way to install it is by cloning the repository.

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/Dexmachi/Ch-aOS.git
    cd Ch-aOS
    ```

2.  **Install the `chaos` CLI:**
    The project uses `makepkg` to build and install the components.
    ```bash
    cd cli/build/b-coin/
    makepkg -fcsi
    ```

3.  **Install Optional Components:**
    Ch-aOS is modular. You can install "cores" for specific distributions and other plugins.

    -   **Ch-aronte (Arch Linux Core):**
        ```bash
        cd ../../Ch-aronte/build/core/
        makepkg -fcsi
        ```

    -   **chaos-dots (Dotfile Manager Plugin):**
        ```bash
        cd ../../external_plugins/chaos-dots/
        makepkg -fcsi
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
