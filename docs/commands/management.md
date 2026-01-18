# Commands: Management

These commands help you manage the `chaos` CLI environment itself, from initializing configuration files to discovering available functionality.

## `chaos init`

The `chaos init` command is a setup wizard that creates boilerplate configuration files, lowering the barrier to entry by generating templates for you.

### Subcommands

#### `init chobolo`

This command scans your installed plugins for their required configuration keys and generates a template `ch-obolo.yml` file. This is a great way to discover the data your roles need.

**Usage:**
```bash
chaos init chobolo
```
This will create a `ch-obolo_template.yml` in `~/.config/chaos/`.

#### `init secrets`

This command runs an interactive wizard to set up your secret management with `sops`. It helps you:

-   Choose between `age` and `gpg` as your encryption backend.

-   Generate new keys or use existing ones.

-   Create a `.sops.yaml` configuration file.

-   Create an initial `secrets.yml` file.

**Usage:**
```bash
chaos init secrets
```

---

## `chaos set`

The `chaos set` command configures default paths for your most-used files, saving you from having to specify them with flags on every command. These paths are saved to `~/.config/chaos/config.yml`.

### Subcommands

#### `set chobolo <path>`

Sets the default Ch-obolo file to use for `apply` operations.

**Usage:**
```bash
chaos set chobolo ~/my-chaos-configs/main-chobolo.yml
```

#### `set secrets <path>`

Sets the default secrets file.

**Usage:**
```bash
chaos set secrets ~/my-chaos-configs/secrets.sops.yml
```

#### `set sops <path>`

Sets the default `.sops.yaml` configuration file.

**Usage:**
```bash
chaos set sops ~/my-chaos-configs/.sops.yaml
```

---

## `chaos check`

The `chaos check` command helps you discover what functionality is available from your installed plugins.

### Subcommands

#### `check roles`

Lists all available role tags that you can use with `chaos apply`.

**Usage:**
```bash
chaos check roles
```

#### `check aliases`

Lists all available command aliases for role tags.

**Usage:**
```bash
chaos check aliases
```

#### `check explanations`

Lists all documentation topics that you can read about with `chaos explain`.

**Usage:**
```bash
chaos check explanations
```
