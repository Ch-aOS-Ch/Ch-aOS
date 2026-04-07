# Rambling with the SDK

The `ramble` subsystem is essentially an encrypted, CLI-native knowledge base. But because Ch-aOS is an SDK, you can completely automate how you read, create, and parse your team's documentation.

Want to pull your team's incident response playbooks directly into a custom dashboard? Or automatically generate a daily journal entry? The SDK makes it trivial.

## Reading Rambles

To read rambles, you just need a `RambleReadPayload`. The SDK handles the file resolution, path traversal protections, and (if it's encrypted) seamlessly decrypts the content via `sops`.

```python
from chaos.lib.args.dataclasses import RambleReadPayload, SecretsContext
from chaos.lib.ramble import handleReadRamble
import json

# Setup context (points to a specific team's ramble directory)
context = SecretsContext(team="my_company.my_team.ops")

# We want to read the 'incident_response' page inside the 'playbooks' journal
payload = RambleReadPayload(
    targets=["playbooks.incident_response"],
    context=context,
    no_pretty=True # We want raw data, not rich CLI formatting (not needed, only useful if you use this in your own CLI)
)

result = handleReadRamble(payload)

if result.success:
    # result.data is a dictionary where the keys are the targets requested
    # and the values are the parsed YAML content of the ramble.
    data = result.data.get("playbooks.incident_response", {})

    print(f"Title: {data.get('title')}")
    print(f"What to do: {data.get('what')}")
else:
    print(f"Failed to read ramble: {result.error}")
```

## Creating Rambles Programmatically

You can dynamically generate new entries. Note that by default, creating a ramble via the CLI opens an editor. When using the SDK, you might want to create the file and then write to it programmatically instead of waiting for a user's text editor.

```python
from chaos.lib.args.dataclasses import RambleCreatePayload, SecretsContext
from chaos.lib.ramble import handleCreateRamble
import yaml

context = SecretsContext(team="my_company.my_team.ops", i_know_what_im_doing=True)

# Create a new page called '2026-03-19' inside the 'dailies' journal
payload = RambleCreatePayload(
    target="dailies.2026-03-19",
    context=context,
    encrypt=False, # Set to True to encrypt it after creation
    confirmed=True # Skip "file already exists" prompts (overrites without asking)
)

result = handleCreateRamble(payload)

if result.success:
    # The SDK returns the path to the newly created file
    file_path = result.data.get("file_to_edit")

    # Now you can programmatically append your automated data
    automated_data = {
        "title": "Daily automated check",
        "concept": "System status",
        "what": "All systems operational.",
        "tags": ["daily", "automated"]
    }

    with open(file_path, "w") as f:
        yaml.dump(automated_data, f)

    print(f"Successfully created and populated {file_path}")
else:
    print(f"Creation failed: {result.error}")
```

## Searching your Knowledge Base

You can also leverage the SDK to search through all encrypted and unencrypted notes. This is great for building custom search integrations (e.g., a Slack command that queries your encrypted team notes).

```python
from chaos.lib.args.dataclasses import RambleFindPayload, SecretsContext
from chaos.lib.ramble import handleFindRamble

context = SecretsContext(team="my_company.my_team.ops")

payload = RambleFindPayload(
    context=context,
    find_term="database outage",
    tag="critical" # Optional: only search rambles with this tag
)

result = handleFindRamble(payload)

if result.success:
    print("Found relevant rambles:")
    for match in result.data:
        print(f"- {match}") # e.g., 'playbooks.incident_response'
else:
    print("No matches found or an error occurred.")
```
