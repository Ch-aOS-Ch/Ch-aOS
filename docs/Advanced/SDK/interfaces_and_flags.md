# Building Interfaces: Flags and Prompts

If you've been looking through the SDK's source code, you might have noticed some peculiar patterns. You might be wondering: "Why does `ramble.create` have a `gatherCreateRamble` and a `handleCreateRamble`? And what is up with all these `confirmed` or `i_know_what_im_doing` flags in the payloads?"

Well, Ch-aOS wasn't just built to be a CLI tool. It was built to be a universal engine that can power any type of interface, whether that is a CLI, a graphical application (GUI), a terminal UI (TUI), or even a web dashboard!

To make this possible without tightly coupling the core logic to the terminal, the SDK separates **Data Gathering** from **Execution**, and relies heavily on specific payload flags.

## The `gather_*` Functions and Data Requests

In a normal Python CLI script, if a user forgets an argument, the script just calls `input("Please enter X: ")`. But what if your interface is a Web UI? `input()` would crash the server!

To solve this, Ch-aOS uses a pattern where you first call a `gather_*` function (like `gatherInitTeam` or `gatherRotateAdd`).

These functions inspect your `Payload` and return a `DataGatherRequest` (which contains `DataGatherPayload` fields) if something is missing or requires explicit user confirmation. 

```python
# A typical DataGatherRequest structure
DataGatherRequest(
    name="team_init", 
    fields=[
        DataGatherPayload(
            name="engine",
            prompt="Choose encryption engine",
            input_type="choice",
            choices=["age", "gpg"],
            required=True
        )
    ]
)
```

If you are building a custom interface, you can take this `DataGatherRequest`, dynamically render a dropdown menu or a checkbox for your user, update your `Payload` with their answer, and *then* pass it to the `handle_*` execution function.

This is why the Payloads are mutable, you _build_ the Payload step by step, gathering data as you go, until it's ready for execution

### The Power of Confirmation Flags

If you are building an automated script (like a cron job) or just don't want to deal with intermediate prompts, you can bypass the `gather_*` step entirely by utilizing the confirmation flags inside your Payload.

When you instantiate a Payload, you can explicitly set flags like:
- `confirmed=True`
- `update_confirmed=True`
- `i_know_what_im_doing=True` (This one acts as a master override for all safety prompts!)

If you set these flags, the `gather_*` functions will simply return `None`, telling you: "All good, you have explicitly authorized everything. Proceed to execution."

Note that you must use the gather_* functions to... well, to bypass them! This is mostly useful not for programmatic interfaces, but for UIs, be them GUI, TUI or CLIs. If you are writing a Python script that just wants to do something without user interaction, you can skip the gather_* functions and directly call the handle_* functions with the appropriate flags set in your Payload.

```python
from chaos.lib.args.dataclasses import TeamInitPayload
from chaos.lib.team import gatherInitTeam, handleInitTeam

# Automated payload: We explicitly say we know what we are doing!
payload = TeamInitPayload(
    target="my_company.my_team",
    path="/tmp/team_repo",
    i_know_what_im_doing=True # Bypasses the gatherer!
)

# This will return None because we passed the override flag
request = gatherInitTeam(payload)

if request is None:
    # Safe to execute immediately
    handleInitTeam(payload)
```

## Pretty Printing and Machine Readability

The second piece of the puzzle for building custom interfaces is output formatting.

By default, the Ch-aOS CLI tries to be cute. It uses the `rich` library to render beautiful Markdown tables, syntax-highlighted code, and colorful trees. But "cute" is terrible if you are trying to parse the output with a Python script or `jq`.

To accommodate automation and custom UIs, our Payloads often include output modifier flags:

- `no_pretty`: Disables the rich terminal formatting, returning raw YAML or standard strings.

- `json`: When combined with `no_pretty`, forces the output to be strictly formatted as JSON.

- `value` (or `values`): Strips away all keys and metadata, returning *only* the raw value (extremely useful for piping data directly into other shell commands).

If you are building a Web UI on top of the Ch-aOS SDK, you will almost never need to use something like `json=True` or `no_pretty=True` because the SDK already returns clean, parseable data structures (like dictionaries or lists) from the `handle_*` functions. The `json` flag is mostly useful if you are building a custom UI that still wants to support machine-readable output.

```python
from chaos.lib.args.dataclasses import RambleReadPayload, SecretsContext
from chaos.lib.ramble import handleReadRamble

# We want raw JSON data to send to a frontend React app
payload = RambleReadPayload(
    targets=["dailies.2026-03-19"],
    context=SecretsContext(team="my_company.my_team"),
    no_pretty=True,
)

result = handleReadRamble(payload)
# result.data will be a clean, parseable dictionary!
```

By combining payload DTOs, the `gather_*` interface abstractions, and strict JSON output formatting, the Ch-aOS SDK provides everything you need to build entirely new experiences on top of its core engine.
