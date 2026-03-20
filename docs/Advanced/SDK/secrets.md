# Managing Secrets via SDK

Handling secrets programmatically can be tricky. You want to keep them secure, avoid leaking them into logs, and preferably never write them to disk unencrypted.

With the Ch-aOS SDK, you can integrate our powerful `sops` wrapper directly into your own Python applications. This allows you to decrypt YAML/JSON files on the fly, fetch keys from external providers (like Bitwarden or 1Password), and rotate keys programmatically.

## The Secrets Context

Whenever you interact with secrets in the SDK, you need to provide a `SecretsContext`. This payload defines the environment: which team you are targeting, any specific file overrides, and which ephemeral provider to use (if any).

```python
from chaos.lib.args.dataclasses import SecretsContext, ProviderConfigPayload

# A simple context for the local user
context = SecretsContext(
    team=None,
    sops_file_override=None,
    secrets_file_override=None,
    i_know_what_im_doing=True # Skips confirmation prompts
)

# A context using an ephemeral provider (e.g., Bitwarden)
provider_cfg = ProviderConfigPayload(
    provider="bw.age", # Uses the 'bw' backend with 'age' keys from your config
    ephemeral_provider_args="from_bw": ('item_id_here', "key_type_here(age)") # not necessary, provider was already passed.
)

# Let it be known that ephemeral provider args come from plugins, therefore the plugin must document how to use them and what they do. The SDK will not validate or understand these arguments, it just passes them through to the provider plugin.

advanced_context = SecretsContext(
    team="my_company.my_team.backend",
    provider_config=provider_cfg,
    i_know_what_im_doing=True
)
```

## Decrypting Secrets on the Fly

The most common use case is decrypting a secrets file directly into memory so your script can use the credentials.

We provide a handy utility `decrypt_secrets` that handles the heavy lifting, including spinning up the ephemeral provider environment if necessary!

```python
from chaos.lib.secret_backends.utils import decrypt_secrets, get_sops_files
from chaos.lib.args.dataclasses import SecretsContext
import omegaconf

context = SecretsContext(team="my_company.my_team.backend")

# Resolve the actual file paths and the global chaos config
secrets_file, sops_file, global_config = get_sops_files(
    sops_file_override=context.sops_file_override,
    secrets_file_override=context.secrets_file_override,
    team=context.team
)

try:
    # Decrypt the file! This returns the raw YAML/JSON string.
    raw_decrypted_text = decrypt_secrets(
        secrets_file=secrets_file,
        sops_file=sops_file,
        config=global_config,
        context=context
    )

    # Parse it into a dictionary using OmegaConf, or use your own YAML/JSON parser
    secrets_dict = omegaconf.OmegaConf.create(raw_decrypted_text)

    print(f"Database password is: {secrets_dict.db.password}")

except Exception as e:
    print(f"Decryption failed: {e}")
```

## Rotating Keys Programmatically

Need to build a Slack bot that automatically adds a new developer's public key to the team's secrets? You can do that!

```python
from chaos.lib.args.dataclasses import SecretsRotatePayload, SecretsContext
from chaos.lib.secrets import handleRotateAdd

context = SecretsContext(
    team="my_company.my_team.backend",
    i_know_what_im_doing=True # Automatically confirm updates
)

payload = SecretsRotatePayload(
    type="age",
    keys=["age1yourpublickeyhere..."],
    context=context,
    update_confirmed=True # Trigger a full sops updatekeys after adding
)

result = handleRotateAdd(payload)

if result.success:
    print("Key added and secrets updated successfully!")
    for msg in result.message:
        print(msg)
else:
    print(f"Failed to add key: {result.error}")
```

The SDK seamlessly handles adding the key to your `.sops.yaml` configuration and immediately running the update process across your encrypted files.

## Providers and Ephemeral Environments

If you are building an automated pipeline, you probably don't want master `age` or `gpg` keys sitting on the CI/CD runner. By passing a `ProviderConfigPayload` inside your `SecretsContext` (as shown earlier), the SDK will automatically authenticate with the external CLI (like `bw` or `op`), pull the key into memory or `/dev/shm`, decrypt the secrets, and immediately wipe the key.

You don't have to write any teardown code for the keys; the `Provider` context managers handle it securely under the hood!
