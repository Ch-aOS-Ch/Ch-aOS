# Secret Providers

So, you don't use passwords for file encryption, you use keys, fantastic! But then, where in the nine hells of Dante do you *store* those keys? They aren't physical objects you can just put in a keyring, nor are they something you want to leave lying around in your home directory. Most certainly it is not something you want to lose!

While `sops` provides the encryption, a "Secret Provider" in Ch-aOS answers the question: "Where do you securely store the master key itself?"

Providers are integrations with external password managers (like Bitwarden and 1Password) that allow `chaos` to access master encryption keys (like `age` or `gpg` keys) without needing to keep them as plaintext files on the local filesystem.

## The Ephemeral Key Workflow

The primary benefit of using a provider is enabling an **ephemeral key workflow**.

1.  The master key (e.g., your team's `age` private key) is stored securely in the password manager.

2.  When you run a command like `chaos apply --secrets -p bw.age`, `chaos` fetches that key from the provider.

3.  The key exists **only in memory** for the duration of that single command.

4.  `sops` uses the in-memory key to decrypt your secrets file.

5.  Once the command finishes, the key is gone from your local machine.

This significantly enhances security by reducing the attack surface. An attacker would need to compromise your machine *while* a `chaos` command is running and also compromise your (likely locked) password manager.

This workflow effectively transforms basic asimetric local-first keys into IAM keys. Just think about it, you abstract your private key's content into an versionable provider ID (e.g., bitwarden's IDs), this means you can 1 version control your private keys and 2 _put an RBAC on top of them_, and 3 audit the key's access through the same provider's auditability system which does the transformation's heavy ligting.

## Usage

### Configuration

You can configure named providers in your global chaos configuration file at `~/.config/chaos/config.yml`.

```yaml
# ~/.config/chaos/config.yml

secret_providers:
  # Sets the default provider to use when -p is given without a name
  default: bw.age

  bw:
    age_id: "BITWARDEN_ITEM_ID_FOR_AGE_KEY"
    gpg_id: "BITWARDEN_ITEM_ID_FOR_GPG_KEY"
    # You can also specify organization/collection IDs for 'bw'
    organization_id: "..."
    collection_id: "..."

  bws:
    project_id: "BITWARDEN_SECRETS_PROJECT_ID"
    age_id: "SECRET_ID_FOR_AGE_KEY"
    gpg_id: "SECRET_ID_FOR_GPG_KEY"

  op:
    age_url: "op://vault/item_name/notesPlain"
    gpg_url: "op://vault/item_name/notesPlain"
```

### Ephemeral Usage

Many commands that interact with secrets (like `apply`, `secrets edit`, `ramble read`) accept a `-p`/`--provider` flag to use a configured provider.

```bash
# Use the provider named 'bw.age' from your config
chaos apply users --secrets -p bw.age

# Use the default provider
chaos apply users --secrets -p
```

Most providers also register a direct flag (e.g., `-b` for Bitwarden, `-o` for 1Password) for one-off use without a pre-existing configuration.

```bash
# Use a Bitwarden item directly
chaos secrets edit -b "ITEM_ID" "age"
```

## Supported Providers

Ch-aOS has built-in support for:

-   **Bitwarden (`bw`, `rbw`)**: Integrates with the standard Bitwarden CLI (`bw` and `rbw`).

-   **Bitwarden Secrets (`bws`)**: Integrates with the Bitwarden Secrets Manager CLI (`bws`).

-   **1Password (`op`)**: Integrates with the 1Password CLI (`op`).

The provider system is extensible, allowing new plugins to add support for other backends.

## `import` / `export`

The `chaos secrets` command provides `import` and `export` subcommands to create a secure workflow for bootstrapping new machines or backing up master keys.

### `export`
Saves a local `age` or `gpg` master key into your chosen password manager.

**Example:**
```bash
chaos secrets export bw age --item-name 'My Team Age Key' --keys ~/.config/chaos/keys.txt
```

### `import`
Retrieves a master key from the password manager and saves it to your local environment (e.g., importing it into your GPG keyring or saving it to `keys.txt`).

**Example:**
```bash
chaos secrets import bw age --item-id '...'
```

### Enhanced Export Security (`--no-import`)

When exporting a key, you can use the `-N` or `--no-import` flag. This embeds a special `# NO-IMPORT` marker in the secret stored in the password manager. The `chaos secrets import` command will refuse to import any key with this marker. This creates a one-way-trip for a key, allowing it to be distributed for use but preventing it from being extracted back to a local file.
