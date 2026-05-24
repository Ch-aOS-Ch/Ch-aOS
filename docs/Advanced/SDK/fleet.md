# Fleet Management and Boats via SDK

Managing a single host via the SDK is straightforward, but what if you want to orchestrate a dynamic fleet of servers fetched from AWS, GCP, or a custom internal API? 

In the Ch-aOS SDK, this is handled by **Boats**. Boats are Python classes that dynamically mutate your global configuration to inject hosts into the Pyinfra inventory before execution begins.

## Understanding the Fleet Lifecycle

When using the SDK, the resolution of fleets and boats happens *before* Pyinfra is initialized. The goal is to take a base configuration (from your `Ch-obolo`) and let the Boats append their dynamically discovered hosts.

### 1. The Configuration Structure

Your SDK script will usually start with a base configuration dictionary (often loaded via `OmegaConf`):

```python
from omegaconf import OmegaConf

base_config = OmegaConf.create({
    "fleet": {
        "parallelism": 5,
        "boats": [
            {
                "provider": "my_custom_aws_boat",
                "config": {"region": "us-east-1", "tag": "web-server"}
            }
        ],
        "hosts": [
            {"@local": {}} # Static hosts can coexist with dynamic ones
        ]
    }
})
```

### 2. Resolving the Fleet

The SDK provides a helper function `gather_fleet` in the `chaos.lib.apply` module. This function automatically loads the required Boat Souls, executes their logic, and merges the resulting hosts into a unified list.

```python
from chaos.lib.apply import gather_fleet
from chaos.lib.args.dataclasses import ApplyPayload, SecretsContext

payload = ApplyPayload(
    update_Souls=False,
    i_know_what_im_doing=True, # Skips fallback prompts
    dry=False,
    verbose=0,
    v=0,
    tags=["services"],
    fleet=True, # Crucial: Tells the SDK we want to run in fleet mode
    secrets_context=SecretsContext()
)

# Call the fleet gatherer
# It will execute 'my_custom_aws_boat' and merge the results
fleet_request, fleet_result = gather_fleet(payload, base_config, "virtual_chobolo_path")

if not fleet_result.success:
    print(f"Failed to resolve fleet: {fleet_result.error}")
    exit(1)

# fleet_result.data contains the resolved list of hosts and the parallelism level
resolved_hosts = fleet_result.data.get("hosts", ["@local"])
parallelism_level = fleet_result.data.get("parallels", 0)

# We update the payload with the target hosts
payload.target_hosts = resolved_hosts
payload.is_fleet_active = fleet_result.data.get("is_fleet", False)
payload.parallelism = parallelism_level

print(f"Targeting hosts: {payload.target_hosts}")
```

### 3. Executing against the Fleet

Once the `payload.target_hosts` is populated, the rest of the orchestration lifecycle remains exactly the same as a single-node run! The `setup_pyinfra` function will read `payload.target_hosts` and correctly construct the `pyinfra.api.inventory.Inventory`.

```python
from chaos.lib.apply import setup_pyinfra

setup_result = setup_pyinfra(payload)
if setup_result.success:
    payload.pyinfra_state = setup_result.data

    # payload.pyinfra_state.inventory now contains both your @local 
    # and all the dynamic AWS instances fetched by your boat!
```

## Why do this programmatically?

By handling Boats programmatically, you can inject configuration dynamically instead of relying on a static `Ch-obolo` file. 

For instance, if your Python API receives a webhook from an autoscaling group indicating that 3 new instances were launched, you can construct a `base_config` dictionary in memory with those specific IPs, run the orchestration via the SDK, and provision the new servers instantly—all without ever touching the filesystem!
