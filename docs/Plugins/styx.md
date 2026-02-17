# The Styx Plugin Registry

Styx is the official and decentralized plugin registry for Ch-aOS. It offers a simple and secure way for users to discover, install, and manage plugins that extend the functionality of `chaos`.

Instead of a complex central server, Styx uses a Git repository containing a single YAML file (`registry.yaml`) as its source of truth. This pragmatic approach makes the system transparent, low-cost, and easy to maintain by the community.

## Using `chaos styx`

The `chaos styx` command is your interface for interacting with the registry.

### `chaos styx list`

Lists all plugins available in the Styx registry or information about specific plugins.

**Usage:**
```bash
# List all available plugins
chaos styx list

# Get information about a specific plugin
chaos styx list chaos-dots
```

This will show the plugin's name, its version, a brief description, and a link to the repository.

### `chaos styx invoke`

Downloads and installs one or more plugins from the registry.

**Usage:**
```bash
# Install the dotfiles management plugin
chaos styx invoke chaos-dots
```

`chaos` will query the registry, find the plugin's release URL, download the `.whl` file, and install it in the `~/.local/share/chaos/plugins/` directory.

### `chaos styx destroy`

Removes a plugin that has been installed locally.

**Usage:**
```bash
# Remove the chaos-dots plugin
chaos styx destroy chaos-dots
```

This will remove the plugin's file from your local directory, effectively uninstalling it.

## Submitting a Plugin to Styx

If you have developed a plugin and wish to share it with the community, you can submit it to Styx.

Styx is intentionally simple and does not resolve dependencies. Therefore, plugins should be as self-contained as possible.

To submit, open a Pull Request in the [Styx repository](https://github.com/Ch-aOS-Ch/styx) by adding your plugin's entry to the `registry.yaml` file. The structure is as follows:

```yaml
styx:
  # Your plugin's name (as it will be called in chaos styx)
  my-plugin:
    # The built package name (used for the .whl file)
    name: my_plugin
    # The Git repository where the plugin is hosted
    repo: https://github.com/your-username/my-plugin
    # A brief description about your plugin
    about: "A plugin that does something amazing."
    # The specific release version (cannot be "latest")
    version: "v0.1.0"
    # The sha256 checksum of the .whl file for integrity verification
    hash: "abc123def456..."
```

## The Styx Security Model

Security is a priority in Styx. The following measures are in place to protect users:

1.  Human Review: All new plugins and updates undergo a Pull Request review process by Ch-aOS team members before being accepted into the registry.

2.  Open Source and Transparency: All plugins listed in Styx must be open source, allowing anyone to audit the source code.

3.  Signed Commits: Contributions to the Styx registry must be made with signed commits, ensuring the authenticity of the author.

4.  Controlled Origin: Plugins are downloaded from specific, well-defined "release" URLs in the plugins' official repositories, reducing the risk of downloads from untrusted sources.

5.  Secure Installation: Installation occurs in a specific user directory, without the need for superuser permissions, and `chaos` performs basic checks to prevent *path traversal* attacks.

6. As you've probably noticed, Styx calculates and verifies the SHA256 checksum of the downloaded plugin file against the value specified in the registry. This removes a lot of tampering issues, the attacker would need to make me put their normal code inside of my repo, then make a malicious release with the same version as mine, and then change the hash in the registry (with a review PR), which would be very sketchy, to make an attack.

7. Styx does NOT resolve either dependencies, conflicts or versioning. This means each plugin MUST be self-contained and as atomic as possible.

8. The Styx registry is read-only for users, and only maintainers can merge changes to it. This means that even if an attacker compromises a user's account, they cannot directly modify the registry to add malicious plugins.

Although these layers create a secure environment, the good practice of only installing software from trusted sources is still encouraged.
