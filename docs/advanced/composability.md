# Ch-aOS Composability Features

So, Ch-aOS is not just about managing machines, it also has lots of features for managing secrets, getting documentation and all sorts of other things. These features are cool and all, but what about when you want to not use the main Ch-aOS tool with them? What if you want to use them in your own scripts or tools?

Well, that's where composability comes in. Ch-aOS is designed to be composable, meaning you can use its features in your own code without having to rely on the main Ch-aOS command-line tool.

## How It Works

Well, when you first use Ch-aOS you might see that... well, the stdouts aren't exactly what you'd want for a library. That's because Ch-aOS is primarily a CLI tool.

However, most (if not all, hmu if you find one that isn't) of the features in Ch-aOS have a built-in "--json" and (if applicable) a "--no-pretty" flag. These flags turn the output from something quite cute into something more... machinery-y. Of course, this makes it quite easy for other programs to use Ch-aOS features.

## Why Use Composability?

There are a few reasons why you might want to use Ch-aOS's composability features:

  - automation: You might want to automate certain tasks using Ch-aOS features in your own scripts or tools.

  - integration: You might want to integrate Ch-aOS features into your own applications or systems.

  - customization: You might want to customize the behavior of Ch-aOS features to better suit your needs.

And other use-cases I'm sure you can think of, these are just the first ones that came to mind!

## How to use

Uh... Just `chaos <feature> --json` or `chaos <feature> --no-pretty`? Like, it's really that simple. For example:

```bash
chaos explain --no-pretty -j chaos
# Yes, I know, quite cool that you can get explanations in JSON huh?
# just think of the possibilities! (mainly UI or documentation)
```

Returns:
```json
{
  "concept": "The Ch-aOS Command-Line Interface",
  "what": "`chaos` is the main entry point for the Ch-aOS tool. It acts as a CLI to orchestrate system configuration, manage secrets, and handle team Ch-aOS configurations and documentation.",
  "why": "It provides a single interface to some backend tools (like `pyinfra` and `sops`), simplifying complex workflows and making system management declarative and repeatable (I'M WORKING ON ATOMICITY OK?).",
  "how": "When you run a command like `chaos apply users -s`, the CLI parses your arguments, loads the necessary configuration from your \"Ch-obolo\" file, discovers the appropriate role from its plugins, and executes the underlying logic.",
  "learn_more": [
    "run `chaos --help` to see all available commands."
  ]
}
```

Or:
```bash
chaos explain --no-pretty chaos
```

Returns:
```yaml
concept: The Ch-aOS Command-Line Interface
what: '`chaos` is the main entry point for the Ch-aOS tool. It acts as a CLI to orchestrate
  system configuration, manage secrets, and handle team Ch-aOS configurations and
  documentation.'
why: It provides a single interface to some backend tools (like `pyinfra` and `sops`),
  simplifying complex workflows and making system management declarative and repeatable
  (I'M WORKING ON ATOMICITY OK?).
how: When you run a command like `chaos apply users -s`, the CLI parses your arguments,
  loads the necessary configuration from your "Ch-obolo" file, discovers the appropriate
  role from its plugins, and executes the underlying logic.
learn_more:
- run `chaos --help` to see all available commands.
```

By the way, most of the features that have a `--json` tag need to be used with `--no-pretty` to get valid JSON output. Just a heads up!

By using these flags, you can easily integrate Ch-aOS features into your own scripts and tools, making it a powerful and flexible tool for system management and automation.

OH YEAH, forgot to mention!
In some rare cases, you can see a teeny tiny `--value` `-v` flag. This is for when you just want the raw value of something, like a secret or a config value, without any extra formatting or metadata.
Yes, this means that something like this is possible:

```bash
chaos secrets cat ssh_pass -v | chaos apply users -slye -ps
```


??? quote "Hey, hey you there, I've got a secret to tell you"
    Wanna use Ch-aOS like a big' ol `pass`? `chaos ramble read <encrypted.note> --no-pretty -v <all> <these> <keys>` will output the decrypted keys directly to stdout for easy piping, You can basically use it like a password manager CLI! (Not really the intention, but hey, it works!)

