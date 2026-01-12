# Command: `chaos explain`

The `chaos explain` command provides a built-in documentation system. It offers a didactic way to learn about Ch-aOS concepts, commands, and features directly from the command line.

The content is provided by plugins, meaning the documentation lives alongside the functionality it describes.

## Usage

```bash
chaos explain [topic] [options]
```

-   `[topic]`: The topic you want an explanation for.
-   `[options]`: Flags to modify the command's behavior.

## Discovering Topics

You can discover all available topics provided by your installed plugins using `chaos check`.

```bash
chaos check explanations
```

## Reading Explanations

To read about a topic, simply pass its name to the command.

```bash
# Get a basic explanation of the 'apply' command
chaos explain apply
```

### Sub-topics

Many topics are broken down into more specific sub-topics. You can access them using a dot (`.`) notation.

-   To list all available sub-topics for a given topic, use `.list`.
-   To read a specific sub-topic, use `topic.subtopic`.

**Examples:**
```bash
# List all sub-topics for the 'secrets' command
chaos explain secrets.list

# Get an explanation for the 'edit' subcommand of 'secrets'
chaos explain secrets.edit
```

### Detail Level (`-d`, `--details`)

You can request more detailed information using the `--details` flag. This allows you to progressively drill down from a high-level concept to technical specifics.

The available levels are:
-   `basic` (default)
-   `intermediate`
-   `advanced`

**Example:**
```bash
# Get an advanced explanation of sops integration, including technical details
chaos explain secrets.sops --details advanced
```
