# Command: `chaos apply`

Well duh, how is a "system management tool" supposed to manage your system if it can't apply changes?

The `chaos apply` command is the engine of Ch-aOS. It executes roles to bring your system to the state declared in your [Ch-obolo file](../core-concepts.md/#ch-obolos-the-data).

This implements a **declarative state orchestration** model. `pyinfra`, the underlying engine, first inspects the current state of the system ("facts"), compares it to the desired state, calculates the necessary changes (the "delta"), and then executes the operations to reconcile the state.

## Usage

```bash
chaos apply [tags...] [options]
```

-   `[tags...]`: One or more tags corresponding to the [roles](../core-concepts.md/#roles-the-logic) you want to execute.

-   `[options]`: Flags to modify the command's behavior.

## Key Concepts & Options

### Tags (`[tags...]`)

Tags are the primary mechanism for selecting which roles to execute. You can specify one or more tags to run multiple roles in sequence. Plugins can also provide shorter aliases for tags.

**Why?** They allow you to manage your system modularly. You can apply just the `users` configuration, or just `packages`, or both, without running your entire configuration every time.

**Example:**
```bash
# Apply the configuration for users and packages
chaos apply users packages

# You can also use aliases defined by plugins
chaos apply usr pkgs
```

### Ch-obolo (`-c`, `--chobolo`)

Specifies the path to the Ch-obolo file to be used for this operation. This overrides any default path configured with `chaos set chobolo`.

**Why?** This provides flexibility, allowing you to use different configuration files for different environments or tasks without changing the global settings.

### Secrets (`-s`, `--secrets`)

The `--secrets` flag signals to `chaos apply` that the role you are running needs access to decrypted data from your secrets file.

**Why?** To securely provide sensitive data, like user passwords or private keys, to your orchestration logic without hardcoding them in your Ch-obolo. The decrypted secrets are held only in memory for the duration of the command.

**Example:**
```bash
# The 'users' role requires passwords from the secrets file
chaos apply users --secrets

# Decrypt using an ephemeral key from a configured provider
chaos apply users --secrets -p bw.age
```

### Dry Run (`-d`, `--dry`)

The `--dry` flag is an essential safety feature. It tells `chaos apply` to calculate and show all the changes it *would* make, but **without actually executing them**.

**Why?** It allows you to preview and verify the impact of your configuration changes before applying them to your live system. It's a great way to learn what a role does and to ensure your changes are correct.

**Example:**
```bash
# See what changes would be made for the 'packages' role
chaos apply --dry packages

# Combine with verbosity for more detail
chaos apply -d -vvv packages
```

!!! note about secret having plugins
    You NEED to have a "secret_plugins" section inside of your global config file (~/.config/chaos/config.yml) in order to use secrets inside of a specific role.

### Fleet Mode (`-f`, `--fleet`)

Applies the roles to a fleet of remote hosts defined in the Ch-obolo file instead of the local machine.

See the [Fleet Management](../Advanced/fleet.md) documentation for more details.

### Verbosity (`-v`, `-vv`, `-vvv` or `--verbose`)

Increases the verbosity of the output. This is useful for debugging and understanding what `pyinfra` is doing behind the scenes.

-   `-v`: Warning level
-   `-vv`: Info level
-   `-vvv`: Debug level

### Skip Confirmation (`-y`, `--i-know-what-im-doing`)

This flag skips all confirmation prompts during role execution. Use with caution.
