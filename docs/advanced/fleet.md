# Fleet Management

The `fleet` feature extends `chaos` to orchestrate multiple machines simultaneously. By adding a `fleet` block to your Ch-obolo file, you can define a group of remote hosts and run roles across all of them from a single command.

This is essential for managing any infrastructure with more than one machine, such as a cluster of web servers, a set of development VMs, or any group of computers that need consistent configuration.

## How It Works

When you run an `apply` command with the `--fleet` flag, `chaos` will:
1. Read the `fleet` block from your Ch-obolo file.
2. For each host defined, connect to it via SSH.
3. Execute the specified roles on all hosts, either in sequence or in parallel.

## Defining Your Fleet

To define your fleet, create a `fleet` key in your Ch-obolo file.

```yaml
# ch-obolo.yml

fleet:
  # Optional: Set the max number of hosts to configure at once.
  # Defaults to 0 (unlimited parallelism).
  parallelism: 5

  hosts:
    # --- Host definition using a dictionary ---
    - my-server-01:
        ssh_user: root
        ssh_port: 22
        ssh_key: /path/to/private/key

    # --- You can define multiple hosts ---
    - my-server-02:
        ssh_user: admin
        ssh_port: 2222
        ssh_key: /path/to/another/key

    # --- Minimal definition, relying on defaults or ssh config ---
    - my-server-03: {}
```

The hosts are defined as a list of dictionaries, where each dictionary contains a single host and its connection data. All `pyinfra` connection arguments (like `ssh_user`, `ssh_port`, `ssh_key`, etc.) are supported.

## Applying Roles to the Fleet

To apply roles to the fleet, use the `-f` or `--fleet` flag with the `chaos apply` command.

```bash
# Apply the 'packages' role to all hosts in the fleet
chaos apply packages --fleet

# Apply multiple roles to the fleet with a dry run
chaos apply users services --fleet --dry
```

`chaos` will then connect to each host defined in your fleet and execute the roles, respecting the `parallelism` setting.
