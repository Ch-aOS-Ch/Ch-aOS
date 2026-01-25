# Pyinfra Connectors

Huh??? Weren't we just talking about Ch-aOS? Why Pyinfra all of the sudden??? Well, Ch-aOS uses [Pyinfra](https://github.com/pyinfra-dev/pyinfra) under the hood to manage and configure systems, we just build a lot around it to make it a complete solution, not only a configuration management tool.

So... what is a Pyinfra Connector? Well, glad you asked! A Pyinfra Connector is a way for Pyinfra to connect to and manage remote (or not remote) systems. Connectors define exactly how Pyinfra communicates with the target system, whether it's over SSH (the base way, without any `@`'s), via Docker, or (the base Ch-aOS way) locally.

## Why?

So, why should you care? If you're using Ch-aOS in a more advanced way, you absolutely should care, and like, a lot! Connectors allow you to manage different systems in different ways, all while using the same framework and tooling! Since Ch-aOS simply translates your Ch-obolo inputs to Pyinfra's format, you can use any Pyinfra Connector you want with Ch-aOS, opening up a whole new world of possibilities.

Also, it is the singular entry_point that Pyinfra even provides to extend its functionality, its like a match made in heaven for Ch-aOS!

## How to Use

Simple! In your `fleet.hosts` key inside your Ch-obolo file, you can simply add the connector with its specific tag (e.g. `@dockerssh/` for the Docker SSH connector) to the host you want to use it with. For example:
```yaml
fleet:
  hosts:
    # all base Ch-aOS available connectors (I've checked the source code)
    - '@dockerssh/my_docker_container': {}
    - '@docker/my_docker_container': {}
    - '@podman/my_podman_container': {}
    - '@terraform/my_terraform_instance': {}
    - '@chroot/mnt/my/chroot': {}
    - '@vagrant/my_vagrant_box': {}
    - '@local': {}
    - 'my_remote_server': {} # This one uses the default SSH connector
```

Since Ch-aOS uses Pyinfra under the hood, you can use any Pyinfra Connector available on [PyPI](https://pypi.org/search/?q=pyinfra+connector&type=packages) or even create your own! Since Ch-aOS' plugins are simple .whl files that install Python packages, you can easily create/install any custom connectors through `chaos styx invoke`, since it is quite literally just an entry point to Pyinfra's connector system.

This means that, since there are multiple Pyinfra plugins are being developped inside of [Pyinfra-dev](https://github.com/pyinfra-dev), Ch-aOS could, theoretically, support even [windows](https://github.com/pyinfra-dev/pyinfra-windows) in the future!

## Developing Custom Connectors

Well, Pyinfra's documentation on creating custom connectors is a bit sparse, but the general idea is that you need to create a Python package that defines a new connector class inheriting from `pyinfra.api.connectors.BaseConnector`. You then need to register this connector in your package's `setup.py` or `pyproject.toml` file under the `entry_points` section.

A bit more can be found in [Our own documentation](../plugins/connectors.md) and also in [Pyinfra's documentation](https://docs.pyinfra.com/en/3.x/api/connectors.html).

I'll try my best to explain exactly how to create a working Connector.

If you want to contribute directly to Ch-aOS, you can not only contribute to [our repo](https://github.com/Ch-aOS-Ch/Ch-aOS), but also to [Pyinfra's repo](https://github.com/pyinfra-dev/pyinfra)
