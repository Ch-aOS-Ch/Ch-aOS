# Command: `chaos secrets`

The `chaos secrets` command suite acts as an orchestrator for Mozilla's `sops` (Secrets OPerationS). It simplifies the entire workflow of managing encrypted secrets, allowing you to safely store sensitive data (like passwords, tokens, and API keys) in YAML files that can be committed to a Git repository.

## `secrets edit`

Securely edits a secrets file. This command decrypts the file into a temporary buffer, opens it in your default text editor (`$EDITOR`), and automatically re-encrypts it when you save and close the editor.

**Why?** It provides a seamless and secure workflow for editing secrets without ever permanently saving an unencrypted version to disk.

**Usage:**
```bash
# Edit the default secrets file
chaos secrets edit

# Edit a specific secrets file for a team
chaos secrets edit -t my-company.my-team
```

## `secrets print`

Decrypts a secrets file and prints its entire contents to standard output.

**Usage:**
```bash
chaos secrets print
```

!!! warning "Security Risk"
    Be careful where you use this command. The decrypted secrets will be visible on your screen and potentially in your shell history. Avoid using it in shared or untrusted environments.

## `secrets cat`

Decrypts a secrets file and prints only the specific value(s) of the key(s) you ask for. This is more secure and convenient for scripting than `print`.

**Usage:**
```bash
# Get the value of 'password' inside the 'dex' user object
chaos secrets cat user_secrets.dex.password
```

## Key Management

### `secrets rotate-add`

Adds a new encryption key (e.g., a GPG fingerprint or an `age` public key) to your `.sops.yaml` configuration. This is how you grant a new person or machine access to the secrets.

**Usage:**
```bash
# Add a new GPG key to the sops configuration
chaos secrets rotate-add pgp 'FINGERPRINT_OF_NEW_USER'

# Add a new age key
chaos secrets rotate-add age 'age1...'
```

After adding a key, you must run `sops updatekeys` (or use the `-u` flag with `rotate-add`) on your secret files to re-encrypt them.

### `secrets rotate-rm`

Removes a key from your `.sops.yaml` configuration, revoking access for that key. This is a critical step when someone leaves a team or a machine is decommissioned.

**Usage:**
```bash
chaos secrets rotate-rm pgp 'FINGERPRINT_TO_REMOVE'
```

Like `rotate-add`, you must update the files afterward to apply the key removal.

## `secrets shamir`

Configures Shamir's Secret Sharing, creating an "M-of-N" policy where `M` out of `N` total keys are required to decrypt a secret.

**Why?** It builds redundancy (preventing a single point of failure if a key is lost) and can be used to require a quorum for highly sensitive data.

**Usage:**
```bash
# Set the first (index 0) rule in .sops.yaml to require 2 keys to decrypt
chaos secrets shamir 0 2
```

## `secrets import`/`export`

These commands allow you to securely transfer master keys to and from external password managers. See [Secret Providers](../advanced/providers.md) for more details.
