# Developing Pyinfra Connectors

So, Pyinfra's connectors have some things going on for them, mainly, their base.

## First things first:

Let's start in parts, firstly, the `ConnectorData`

This is a Python object with one singular objective: store all data that can be defined inside your Connector.

Ssh connector example:
```py
class ConnectorData(TypedDict):
    ssh_hostname: str
    ssh_port: int
    ssh_user: str
    ssh_password: str
    ssh_key: str
    ssh_key_password: str

    ssh_allow_agent: bool
    ssh_look_for_keys: bool
    ssh_forward_agent: bool

    ssh_config_file: str
    ssh_known_hosts_file: str
    ssh_strict_host_key_checking: str

    ssh_paramiko_connect_kwargs: dict

    ssh_connect_retries: int
    ssh_connect_retry_min_delay: float
    ssh_connect_retry_max_delay: float
    ssh_file_transfer_protocol: str
```

This gets loaded by the BaseConnector through the line:
```py
data_cls: Type = ConnectorData
```

This translating to Ch-aOS's fleets:
```yaml
fleet:
  hosts:
   - "@ssh/my_server.net": # You can omit the "@ssh/"
      ssh_hostname: str
      ssh_port: str
      ...: ...
```

As you can see, Its a perfect match!

## Meta shtuff

The `DataMeta` class is a simple auto documenting class/default values handler... quite Ch-aOtic of them to add a feature like this huh?

```py
class DataMeta:
    description: str
    default: Any

    def __init__(self, description, default=None) -> None:
        self.description = description
        self.default = default
```

Pyinfra's ssh object example of usage:
```py
connector_data_meta: dict[str, DataMeta] = {
    "ssh_hostname": DataMeta("SSH hostname"),
    "ssh_port": DataMeta("SSH port"),
    "ssh_user": DataMeta("SSH user"),
    "ssh_password": DataMeta("SSH password"),
    "ssh_key": DataMeta("SSH key filename"),
    "ssh_key_password": DataMeta("SSH key password"),
    "ssh_allow_agent": DataMeta(
        "Whether to use any active SSH agent",
        True,
    ),
# Other ConnectorData descriptions and default values
```

## The juicy part

Now... the BaseConnector part... this is the most complex part of them, but it is quite important.

This is the complete object:

```py
class BaseConnector(abc.ABC):
    state: "State"
    host: "Host"

    handles_execution = False

    data_cls: Type = ConnectorData
    data_meta: dict[str, DataMeta] = {}

    def __init__(self, state: "State", host: "Host"):
        self.state = state
        self.host = host
        self.data = host_to_connector_data(self.data_cls, self.data_meta, host.data)

    @staticmethod
    @abc.abstractmethod
    def make_names_data(name: str) -> Iterator[tuple[str, dict, list[str]]]:
        """
        Generate inventory targets. This is a staticmethod because each yield will become a new host
        object with a new (ie not this) instance of the connector.
        """

    def connect(self) -> None:
        """
        Connect this connector instance. Should raise ConnectError exceptions to indicate failure.
        """

    def disconnect(self) -> None:
        """
        Disconnect this connector instance.
        """

    @abc.abstractmethod
    def run_shell_command(
        self,
        command: "StringCommand",
        print_output: bool,
        print_input: bool,
        **arguments: Unpack["ConnectorArguments"],
    ) -> tuple[bool, "CommandOutput"]:
        """
        Execute a command.

        Args:
            command (StringCommand): actual command to execute
            print_output (bool): whether to print command output
            print_input (bool): whether to print command input
            arguments: (ConnectorArguments): connector global arguments

        Returns:
            tuple: (bool, CommandOutput)
            Bool indicating success and CommandOutput with stdout/stderr lines.
        """

    @abc.abstractmethod
    def put_file(
        self,
        filename_or_io: Union[str, IOBase],
        remote_filename: str,
        remote_temp_filename: Optional[str] = None,
        print_output: bool = False,
        print_input: bool = False,
        **arguments: Unpack["ConnectorArguments"],
    ) -> bool:
        """
        Upload a local file or IO object by copying it to a temporary directory
        and then writing it to the upload location.

        Returns:
            bool: indicating success or failure.
        """

    @abc.abstractmethod
    def get_file(
        self,
        remote_filename: str,
        filename_or_io: Union[str, IOBase],
        remote_temp_filename: Optional[str] = None,
        print_output: bool = False,
        print_input: bool = False,
        **arguments: Unpack["ConnectorArguments"],
    ) -> bool:
        """
        Download a local file by copying it to a temporary location and then writing
        it to our filename or IO object.

        Returns:
            bool: indicating success or failure.
        """

    def check_can_rsync(self) -> None:
        raise NotImplementedError("This connector does not support rsync")

    def rsync(
        self,
        src: str,
        dest: str,
        flags: Iterable[str],
        print_output: bool = False,
        print_input: bool = False,
        **arguments: Unpack["ConnectorArguments"],
    ) -> bool:
        raise NotImplementedError("This connector does not support rsync")

```

As you can see... quite the big amount of code. Good for you (not me), I've spent my time reading the source code for Pyinfra extensively!

You don't need to touch `state` or `host`.

`handles_execution` Is a simple bool that answers the question "Can your connector handle command execution?". Quite important for different systems.

`data_cls` again, just the data for your connector.

`data_meta` a dict of `DataMeta`s to document and set default values

First method: `make_names_data` is like [Provider's](./provider-plugins.md) `get_cli_name`, it simply yields the tag for your connector.

Pyinfra's ssh example:
```py
    @override
    @staticmethod
    def make_names_data(name):
        yield "@ssh/{0}".format(name), {"ssh_hostname": name}, [] # transforms the name part into an @ssh/{name} and turns "ssh_hostname" into {name}
```

Some other methods that are well documented (`connect`, `disconnect`)

`run_shell_command` has one exact quirk to it: `**arguments`. This receives a `ConnectorArguments` object, which is the basic global arguments (`_sudo`, `_doas`, etc), which can be handled by you however you please, pyinfra's ssh object uses lines like `_stdin = arguments.pop("_stdin", None)`. It should return a `CommandOutput` object, which is, again, a simple object that can return each output, stdout and stderr from your connector, both as a list and as a singular, unified string.

These behaviours should be the same accross all other methods until `check_can_rsync` and `rsync` which... well, they do exactly what the name suggests.

I quite recommend you to check the Connectors inside of pyinfra's source code, they can teach you quite a lot. Also, I do recommend looking at their [documentation](https://docs.pyinfra.com/en/3.x/api/connectors.html) for more details and examples!

## Quirks, Tips and Shticks worth pointing out

Firstly: On a connection failed, make sure to raise a `ConnectError` exception, Pyinfra will catch it and handle it properly.

Secondly: `make_names_data` is a staticmethod, meaning you can't access `self` or any instance variables inside of it. This is because each yield will create a new instance of your connector.

To "get" data inside of `make_names_data`, you need to do outside functions, like documented in their official docs:
```py
def load_settings():
  settings = {}
  # logic here
  return settings

class InventoryConnector(BaseConnector):
  api_instance = external.ApiClient()
  ...

  @staticmethod
  def make_names_data(_=None)
    api_client = getattr(InventoryConnector, 'api_instance')
    api_settings = load_settings()
    ...
```

3: About `run_shell_command`, You should use their official function `make_unix_command_for_host()` and `extract_control_commands()` from `pyinfra.connectors.util` to properly handle control commands like `_sudo`, `_doas`, etc. Official example:
```py
    control_commands = extract_control_commands(arguments) # returns a dict of control commands
    wrapped_command = make_unix_command_for_host(
        self.state,
        self.host,
        command,
        **arguments, # Be sure to pass ARGUMENTS, not control_commands
    )

    timeout = control_commands.get("_timeout")
    success_exit_codes = control_commands.get("_success_exit_codes", [0])
    exit_code, output = self._execute(wrapped_command, timeout=timeout)

    success = exit_code in success_exit_codes
    return success, output
```

This is because Pyinfra has a lot of built-in logic to handle these control commands, and you should leverage that instead of re-inventing the wheel.

Also it parses commands correctly which ensures that these run correctly on the target system.

## How are them different from Ch-aOS' Boats?

Well, quite a lot actually. Boats provide you with _dynamic inventories_, Pyinfra Connectors provide you with _connection methods_, which are quite different things. Both can be used together in harmony, Boats can provide dynamic inventories that use different Connectors for different hosts, providing you with a lot of flexibility and power!
