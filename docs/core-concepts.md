# Core Concepts

Ch-aOS is built on a few core concepts that work together to provide a powerful and flexible system management experience.

## Ch-obolos: The Data

A "Ch-obolo" is a YAML file where you declare the desired state of your system. It serves as the single source of truth, containing the **data** that roles will use to configure the system.

**Key Idea:** Ch-obolos strictly separate data (what you want) from roles (the logic, how to achieve it).

This makes your configurations:

-   **Readable:** All your variables are in one place, not scattered around a massive file.

-   **Reusable:** Use the same roles with different Ch-obolo files for different systems.

-   **Version-Controllable:** Track changes to your system's desired state using Git.

You can specify a Ch-obolo file with the `-c` flag or set a default path using `chaos set chobolo`.

### Example Ch-obolo

```yaml
# ch-obolo.yml
hostname: "my-arch-box"

users:
  - name: "dex"
    shell: "zsh"
    sudo: True
    groups:
      - wheel
      - docker

packages:
  - git
  - neovim
aurPkgs:
  - google-chrome
```

## Roles: The Logic (The SDK Way)

A "Role" is a Python class (inheriting from the SDK's `Role` base class) that contains the **logic** for achieving a desired state. Roles define a contract of `get_context`, `delta`, and `plan` methods. They read data from your Ch-obolo (and your secrets) and use the `pyinfra` library to stack operations.

When you run `chaos apply <role_tag>`, the Ch-aOS SDK instantiates the corresponding role from its installed plugins and orchestrates its lifecycle:
1. **Context**: Gathers data about the system's current state.

2. **Delta**: Compares current state to the desired state from the Ch-obolo.

3. **Plan**: Schedules the necessary `pyinfra` operations.

This object-oriented, modular approach allows you to apply specific parts of your configuration independently, and even compose roles within your own Python applications.

## Plugins: The Functionality

Ch-aOS is designed to be minimal and modular. Most of its functionality is provided through external plugins. The SDK is the engine; the plugins provide the REAL power.

There are several types of plugins:

-   **Cores**: A "core" provides the basic set of roles for managing a specific Linux distribution. For example, `Ch-aronte` is the core for Arch Linux.

-   **Functionality Plugins**: Add specialized tools (e.g., `chaos-dots` for dotfiles).

-   **Secret Providers**: Integrate with external password managers like Bitwarden or 1Password.

-   **Explanations**: Add documentation accessible via the `chaos explain` command.

-   **Keys**: Add boilerplate for `chaos init chobolo`.

-   **Aliases**: Add shortcuts to chaos roles.

??? quote "Hey, hey you there, I've got a secret to tell you"
    Ch-aOS will have more types of plugins in the future, check the [Chopping Board](chopping-board.md) for planned features!

This architecture means you only install the functionality you need. Since it's built on the standard `pyproject.toml` entry points, one plugin package can seamlessly implement multiple plugin types!

## Learning: The process

The system was designed to be very deep in functionality, however, I personally do not recommend you try to learn everything at once.

I specifically designed this project to have a "progressive disclosure" learning curve. Start with the basics (what is a Ch-obolo, what is a role) and gradually discover more advanced features (secrets management, SDK integration, etc.) as you need them.

The best way to learn is to take a quick look at `chaos check explanations`, go through the ones you find interesting, explore `chaos styx list`, invoke a plugin (like `chaos-dots`), read its explanations, and then initialize a Ch-obolo to apply it. Understanding the configuration before applying is a much better way to learn than blindly running commands!
