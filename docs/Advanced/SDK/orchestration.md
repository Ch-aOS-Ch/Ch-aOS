# Orchestrating Infrastructure via SDK

Applying roles through the CLI is great, but doing it programmatically gives you ultimate control. You can embed Ch-aOS into webhooks, custom API servers, or complex CI/CD pipelines.

Since Ch-aOS relies on `pyinfra` under the hood, running an orchestration involves a specific lifecycle. You don't just "run" a role; you gather context, calculate the delta, build a plan, and then execute it.

## The Apply Lifecycle

Here is how you can use the `chaos.lib.apply` module to orchestrate changes programmatically.

### 1. Setting up the Payload
Everything starts with the `ApplyPayload`. This object holds your targets, tags (which roles to run), verbosity, and secret contexts.

```python
from chaos.lib.args.dataclasses import ApplyPayload, SecretsContext

secrets_context = SecretsContext(i_know_what_im_doing=True)

payload = ApplyPayload(
    update_plugins=False,
    i_know_what_im_doing=True, # Skips interactive prompts
    dry=False,                 # Set to True if you only want to see what WOULD happen
    verbose=0,
    v=0,
    tags=["packages", "users"], # The roles you want to run
    chobolo="/path/to/my/chobolo.yml",
    limani=None,
    logbook=False,
    fleet=False,
    sudo_password_file=None,
    password="my_sudo_password",
    secrets=False,
    serial=False,
    no_wait=False,
    export_logs=False,
    secrets_context=secrets_context,
)
```

### 2. Gathering configs and aliases
Before running roles, you need to load the global configuration and resolve any role aliases.

```python
from chaos.lib.apply import get_configs, resolve_aliases
from omegaconf import OmegaConf

# Load global config
global_config, config_result = get_configs(payload)
if not config_result.success:
    print(config_result.error)

# Convert Omegaconf to a standard dict for the payload
payload.global_config = OmegaConf.to_container(global_config, resolve=False)

# Resolve aliases (e.g., turning "usr" into "users")
alias_result = resolve_aliases(payload)
if alias_result.success and alias_result.data:
    payload.tags = alias_result.data
```

### 3. Orchestrating the Roles
Once the payload is prepped, you load the roles, set up the pyinfra state, and run the `Context -> Delta -> Plan` cycle for each role and host.

```python
from chaos.lib.apply import (
    gather_apply,
    gather_fleet,
    resolve_allowlist_blacklist,
    setup_pyinfra,
    run_context,
    run_delta,
    run_plan,
    execute_plans,
    teardown_pyinfra
)

# This loads the actual role classes from the Souls
apply_request, apply_result = gather_apply(payload)

if not apply_result.success:
    print(f"Error loading roles: {apply_result.error}")
    exit(1)

# If fleet orchestration is enabled, gather the fleet data as well
# This will handle all boats and their associated hosts, which will be used in the context and plan stages
fleet_request, fleet_result = gather_fleet(payload)
if not fleet_result.success:
    print(f"Error gathering fleet data: {fleet_result.error}")
    exit(1)

loaded_roles = apply_result.data["loaded_roles"]
payload.global_config = apply_result.data["global_config"]

# Initialize Pyinfra
setup_result = setup_pyinfra(payload)
payload.pyinfra_state = setup_result.data

# Typically loaded from your chobolo YAML using OmegaConf
chobolo_data = {"packages": ["git", "curl"]}
restrictions = chobolo_data.get("restrictions", {}) # This is just an example, your actual restrictions would depend on your chobolo structure

run_status = "success"

try:
    # Iterate over active hosts in the Pyinfra inventory
    hosts = list(payload.pyinfra_state.inventory.iter_activated_hosts())
    roles = list(loaded_roles.values())

    for host in hosts:
        for role in roles:
            allowlist_blacklist_result = resolve_allowlist_blacklist(
                restrictions, role.name, host
            )

            if allowlist_blacklist_result:
                print(f"Skipping {role.name} on {host} due to allowlist/blacklist rules.")
                if not allowlist_blacklist_result.success:
                    print(f"Error resolving allowlist/blacklist: {allowlist_blacklist_result.error}")
                    return
                continue

            # Step A: Get Context
            context: dict[str, Any] = run_context(payload, role, host, chobolo_data)

            # Step B: Calculate Delta
            delta: Delta = run_delta(context, role, role.name)

            # Step C: Build the Plan
            # This stages the pyinfra operations without running them yet
            plan_result = run_plan(payload, delta, role, role.name, host)
            if not plan_result.success:
                run_status = "failure"

    # Step D: Execute the plans!
    # This connects to the hosts and fires all staged pyinfra operations
    execute_result = execute_plans(payload)
    if not execute_result.success:
         print("Failed to execute plans!")

finally:
    # Always teardown to close connections and export logbooks properly!
    teardown_pyinfra(payload, run_status)
```

And boom! You just orchestrated infrastructure from your own Python script, leveraging all the modularity, telemetry, and power of Ch-aOS.
