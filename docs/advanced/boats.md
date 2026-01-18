# Boat Creation and Management

Boats are a "dynamic fleet" configuration system for Ch-aOS. As always, boats are both optional and pluginable, allowing you and your team to create custom dynamic fleet solutions that fit your infrastructure needs, or even use community-created boats!

## What is a Boat?

Boats, in their simplest form, are Python objects that merge the hosts inside of your fleet with dynamic data sources. This allows you to create fleets that adjust themselves to your needs at runtime. This is the base object for all boats:

```python
from abc import ABC, abstractmethod
from omegaconf import DictConfig, OmegaConf
class Boat(ABC):
    """
    Abstract base class representing a generic boat.

    A boat represents a dynamic provider for the fleet management system.
    This means that each boat has to implement methods to manage its lifecycle
    which include:
    connecting to an external inventory provider (e.g., ec2)
    getting the current state of the fleet
    creating new instances
    returning instances to the pool to list of fleets.

    A boat is configured in a Ch-obolo file like so:
    fleet:
      parallelism: x<=5
      boats:
        - provider: {name of this boat}
          config:
            {config parameters specific to this boat}

      hosts:
        - host1:
            ssh_user: user1
            ssh_key: /path/to/key1.pem

    The 'provider' name is used to find the corresponding Boat class, and the
    'config' block is passed to its constructor.
    """
    name: str = "override_me"  # Subclasses MUST override this class attribute
    config: DictConfig

    def __init__(self, config: DictConfig):
        """
        Initializes the Boat with its specific configuration block from the Ch-obolo file.
        param config: A DictConfig object containing the configuration for this boat.
        """
        self.config = config
        if self.name == "override_me":
            raise NotImplementedError

    @abstractmethod
    def check_connection(self) -> bool:
        """Check if the connection to the external provider is active."""
        raise NotImplementedError

    @abstractmethod
    def get_fleet_config(self) -> dict:
        """
        Handles the retrieval of the fleet configuration from the external provider.
        This method should return a dictionary representing the fleet configuration.
        """
        raise NotImplementedError

    @abstractmethod
    def handle_boat_logic(self, fleet_config: dict) -> dict | list:
        """
        Handle any boat-specific logic for managing the fleet.
        This method should take the current fleet configuration as input,
        perform any necessary operations, and return the hosts to be added.
        """
        raise NotImplementedError

    def get_fleet(self, old_state: DictConfig) -> DictConfig:
        """
        Orchestrates the process of fetching and merging dynamic fleet configuration.

        param old_state:
              The existing OmegaConf configuration state.
        return:
              A new state with the dynamic hosts merged in.
        raises ConnectionError:
              If the boat fails to connect to its provider.
        """
        if not self.check_connection():
            raise ConnectionError(
                f"Boat provider '{self.__class__.name}' failed to establish a connection."
            )

        this_fleet_config = self.get_fleet_config()
        hosts_to_add = self.handle_boat_logic(this_fleet_config)

        if isinstance(hosts_to_add, dict):
            hosts_to_add = [hosts_to_add]

        if not isinstance(hosts_to_add, list):
            raise ValueError(f"Boat provider '{self.__class__.name}' returned invalid hosts format.")

        current_hosts = old_state.get("fleet", {}).get("hosts", [])
        merged_hosts = current_hosts + hosts_to_add

        new_state = DictConfig(OmegaConf.create(OmegaConf.to_container(old_state, resolve=True)))
        new_state.fleet.hosts = merged_hosts

        return new_state
```

As you can see, boats are abstract base classes that require plugins to implement specific methods for connecting to external providers and retrieve the fleet data and get the specific hosts to be added to the fleet.


## Using Boats in Your Fleet

As seen in [fleet](./fleet.md), you have a "hosts" dict inside your fleet configuration. Boats only add to this list of hosts dynamically at runtime.

It is configured as such inside your Ch-obolo file:
```yaml
# ch-obolo.yml

fleet:
  # Optional: Set the max number of hosts to configure at once.
  # Defaults to 0 (unlimited parallelism).
  parallelism: 5

  # Optional: Define boats to dynamically manage your fleet
  # Each boat must specify a provider and its configuration
  boats:
    - provider: my-boat-provider
      config:
        param1: value1
        param2: value2

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

We provide a mock boat to exemplify how boats work, you can find it [here](../../cli/src/chaos/lib/boats/paperBoat.py), note that it isn't registered inside of the default Ch-aOS installation, since it is only for demonstration purposes.

## Why?

First of all: most of you probably don't even need them! They are an advanced feature for *very* specific use cases (e.g., auto-scaling groups, ephemeral fleets, cloud fleets, etc).

Secondly: boats provide a clean implementation for dynamic fleet management that lives alongside the static fleet configuration, which by design lives alongside the *data* you want to manage with Ch-aOS. This means that you can keep your fleet definition and your configuration data together, without needing to juggle multiple files or systems, which also helps a lot with discovering how exactly your infrastructure is being managed and which machines are being targeted.

Finally: boats are pluginable! You can create your own boat classes to integrate with any external system you want, or even share them with the community, so you can have a boat for AWS, GCP or even that one weird internal system your company uses!

## How to use them:

Just use the `--fleet` flag when applying roles, as usual! Ch-aOS will automatically detect and use any boats defined in your fleet configuration to dynamically adjust the hosts being targeted.
```bash
chaos apply [role_tags] --fleet
```

## Creating Your Own Boat

So, you see those @abstractmethod decorators in the Boat class? Those are the methods you need to implement to create your own boat!

So you need to create a new Python class that inherits from the Boat base class and implement the required methods, that means that all of the logic for connecting and retrieving the data is up to you (since I can't really read minds you know?)

After allat, you just need to register your boat class in the Ch-aOS plugin system, so it can be discovered and used when specified in the fleet configuration.
```toml
[project.entry_points."chaos.boats"]
my-boat = "my_module:MyBoatClass"
```
