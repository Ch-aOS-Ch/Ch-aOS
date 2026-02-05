class SecretsExplain:
    _order = [
        "sops",
        "bw",
        "bws",
        "op",
        "age",
        "gpg",
        "vault",
        "edit",
        "print",
        "cat",
        "rotate-add",
        "rotate-rm",
        "shamir",
        "import",
        "export",
        "providers",
    ]

    def explain_age(self, detail_level="basic"):
        return {
            "concept": "Age Encryption",
            "what": "Age is a simple, modern, and secure file encryption tool, library and concrete format. It uses X25519, ChaCha20-Poly1305, and HMAC-SHA256.",
            "why": "It is often preferred for its simplicity and strong cryptographic primitives, making it a modern alternative to GPG for many use cases, especially with `sops`.",
            "how": "`chaos` can generate `age` keys, manage them in `sops-config.yml`, and use them for encrypting/decrypting secrets. You can also derive `age` keys from your SSH keys for convenience and even backups.",
            "equivalent": "age-keygen -o key.txt\n# Get public key:\nage-keygen -y key.txt",
            "learn_more": [
                "age GitHub Repository",
                "Arch Wiki: age",
                "ssh-to-age Tool",
            ],
        }

    def explain_gpg(self, detail_level="basic"):
        return {
            "concept": "GPG (GNU Privacy Guard) Encryption",
            "what": "GPG is a complete and free implementation of the OpenPGP standard. It provides cryptographic privacy and authentication for data communication, commonly used for encrypting files and emails.",
            "why": "It is a widely adopted and battle-tested standard for asymmetric encryption. `chaos` uses GPG keys as a robust method for encrypting and decrypting `sops` secrets.",
            "how": "`chaos` can help generate GPG keys (using modern algorithms like EdDSA/Curve25519), import/export them, and manage their fingerprints in `sops-config.yml` for use with your secrets.",
            "equivalent": "gpg --full-generate-key\n# List fingerprints:\ngpg --list-secret-keys --keyid-format LONG",
            "learn_more": ["GnuPG Website", "Arch Wiki: GnuPG"],
        }

    def explain_vault(self, detail_level="basic"):
        return {
            "concept": "HashiCorp Vault Integration",
            "what": "HashiCorp Vault is a tool for securely accessing secrets. A secret is anything you want to tightly control access to, such as API keys, passwords, certificates, and encryption keys.",
            "why": "Integrating `vault` with `sops` (and thus `chaos`) allows for dynamic secret generation, centralized policy enforcement, and robust auditing of secret access, especially valuable in complex infrastructure setups.",
            "how": "`chaos` manages Vault URIs in your `sops-config.yml` file, allowing `sops` to interact with Vault for encryption/decryption. Ensure your `VAULT_ADDR` and `VAULT_TOKEN` environment variables are set and valid.",
            "security": "Always use the least privileged Vault token possible. Ensure your Vault authentication is configured correctly to prevent unauthorized access.",
            "equivalent": "vault login\n# ... or check authentication:\nvault token lookup",
            "learn_more": ["HashiCorp Vault Documentation"],
        }

    def explain_sops(self, detail_level="basic"):
        return {
            "concept": "Secrets OPerationS (SOPS)",
            "what": "SOPS is an open-source tool by Mozilla that encrypts files (YAML, JSON, ENV, INI, etc.) using KMS, GPG, AWS KMS, GCP KMS, Azure Key Vault, or HashiCorp Vault. It focuses on encrypting only the values in a structured file, leaving keys unencrypted for readability.",
            "why": "It allows you to safely commit encrypted secret files to Git repositories. Only authorized individuals or machines with the correct decryption keys can access the plain text secrets.",
            "how": "Ch-aOS uses SOPS as its core encryption engine. When you use `chaos secrets` commands, `chaos` translates your actions into `sops` commands, handling key management and integration with external providers.",
            "files": ["sops-config.yml", "secrets.yml", ".sops.yaml"],
            "equivalent": "sops --version",
            "learn_more": ["man sops", "Mozilla SOPS GitHub Repository"],
        }

    def explain_bw(self, detail_level="basic"):
        return {
            "concept": "Bitwarden CLI Integration",
            "what": "Bitwarden is an open-source password manager. The `bw` CLI tool allows `chaos` to programmatically interact with your Bitwarden vault to store and retrieve master encryption keys.",
            "why": "It provides a secure, centralized, and cross-platform way to store and share the `sops` master keys (GPG, Age, Vault tokens). This means you don't have to manage these keys locally on every machine.\nTIP: There is a open-source self-hosted option for Bitwarden called Vaultwarden, setting it up with chaos + hashicorp vault makes for a powerful self-hosted secrets management solution, potentially even enterprise-level.",
            "how": "`chaos` uses the `bw` CLI to create new secure notes containing your master keys or to fetch keys from existing items. These fetched keys can then be used ephemerally to decrypt `sops` files.",
            "security": "Ensure your Bitwarden vault is unlocked (`bw unlock`) before running `chaos` commands that interact with `bw`. Your session token (BW_SESSION) is crucial.\nTIP: Use export BW_SESSION=$(bw unlock --raw) to set it in your environment automatically and safelly.",
            "learn_more": ["Bitwarden CLI Documentation"],
        }

    def explain_bws(self, detail_level="basic"):
        return {
            "concept": "Bitwarden Secrets CLI Integration",
            "what": "Bitwarden Secrets is a dedicated secrets management platform by Bitwarden, often used for application secrets. The `bws` CLI tool allows `chaos` to store and retrieve `sops` master encryption keys from Bitwarden Secrets projects.",
            "why": "It provides an alternative, potentially more enterprise-focused, way to manage `sops` master keys for applications and services, separate from individual user vaults.",
            "how": "Similar to `bw`, `chaos` uses the `bws` CLI to create new secrets or retrieve existing ones based on project IDs and item names. These retrieved keys are used ephemerally for `sops` operations.",
            "security": "Ensure your BWS_ACCESS_TOKEN environment variable is set for authentication before running `chaos` commands that interact with `bws`.",
            "learn_more": ["Bitwarden Secrets CLI Documentation"],
        }

    def explain_op(self, detail_level="basic"):
        return {
            "concept": "1Password CLI Integration",
            "what": "1Password is a popular password manager. The `op` CLI tool allows `chaos` to programmatically interact with your 1Password vaults to store and retrieve master encryption keys.",
            "why": "It offers another secure, centralized, and cross-platform option for managing `sops` master keys (GPG, Age, Vault tokens), especially if your team already uses 1Password.",
            "how": "`chaos` uses the `op` CLI to create new items (e.g., Secure Notes) in specified vaults, or to read keys from existing items. These fetched keys can then be used ephemerally to decrypt `sops` files.",
            "security": "Ensure you are signed in to 1Password (`op signin`) and your session token is set (OP_SESSION_<ACC_HASH>) before running `chaos` commands that interact with `op`.",
            "learn_more": ["1Password CLI Documentation"],
        }

    def explain_secrets(self, detail_level="basic"):
        return {
            "concept": "Encrypted Secret Management",
            "what": 'In Ch-aOS, a "secret" refers to any sensitive piece of information (e.g., passwords, API keys, private certificates, tokens, or other credentials) that needs to be stored securely and managed in an encrypted format. These are typically stored in YAML or JSON files, with their sensitive values encrypted by `sops`.',
            "why": "It allows you to safely store sensitive data, like passwords or API keys, inside your git projects by encrypting them with 'age', 'gpg', or 'vault' keys.",
            "how": "The commands orchestrate `sops` by using a `sops-config.yml` configuration file to determine which keys to use for encryption and decryption. The subsystem also integrates with password managers to fetch keys on-demand.",
            "learn_more": [
                "man sops",
                "Mozilla SOPS GitHub Repository",
                "bitwarden CLI Documentation",
                "1Password CLI Documentation",
            ],
            "security": "The security of your secrets depends entirely on the security of the master keys (e.g., your GPG or `age` private key). Protect them carefully.",
        }

    def explain_edit(self, detail_level="basic"):
        return {
            "concept": "Securely Editing Secrets",
            "what": "The `chaos secrets edit` command decrypts a secrets file into a temporary, unencrypted file, opens it in your default text editor (`$EDITOR`), and automatically re-encrypts it upon closing.",
            "why": "It provides a seamless and secure workflow for editing secrets without ever permanently saving an unencrypted version to disk.",
            "equivalent": "sops --config /path/to/your/sops-config.yml /path/to/your/secrets.yml",
            "examples": [
                {
                    "yaml": """# Edit the default secrets file
chaos secrets edit

# Edit a specific secrets file for a team
chaos secrets edit -t my-company.my-team"""
                }
            ],
        }

    def explain_print(self, detail_level="basic"):
        return {
            "concept": "Securely Viewing Secrets",
            "what": "The `chaos secrets print` command decrypts a secrets file and prints its entire contents to standard output.",
            "why": "Useful for a quick review of all secrets or for piping the decrypted content into another script or process in an automated workflow.",
            "security": "Be careful where you use this command. The decrypted secrets will be visible on your screen and potentially in your shell history. Avoid using it in shared or untrusted environments.",
            "equivalent": "sops --config /path/to/your/sops-config.yml -d /path/to/your/secrets.yml",
            "examples": [{"yaml": "chaos secrets print"}],
        }

    def explain_cat(self, detail_level="basic"):
        return {
            "concept": "Viewing Specific Secret Values",
            "what": "The `chaos secrets cat` command decrypts a secrets file and prints only the specific value(s) of the key(s) you ask for.",
            "why": "To extract a single secret value without displaying the entire file, which is more secure and convenient for scripting.",
            "how": "It decrypts the file in memory, selects the value using a dot-separated path, and prints the result.",
            "equivalent": '# Conceptually similar to:\nsops --config sops-config.yml -d secrets.yml | yq ".path.to.key"',
            "examples": [
                {
                    "yaml": """# Get the value of 'password' inside the 'dex' user object
chaos secrets cat user_secrets.dex.password"""
                }
            ],
        }

    def explain_rotate_add(self, detail_level="basic"):
        return {
            "concept": "Adding a New Encryption Key",
            "what": "The `rotate-add` command adds a new key (like a GPG fingerprint, an 'age' public key or a vault URI) to your `sops-config.yml` configuration.",
            "why": "To grant a new person or machine access to the secrets. After adding the key, you can re-encrypt the files so they can decrypt them.",
            "how": "It programmatically modifies the `sops-config.yml` file to add the specified key to a key group. If you use the `-u` (`--i-know-what-im-doing`) flag, it will also run `sops --config sops-config.yml updatekeys [f for f in all_files_in_secret_dir]` on all relevant files.",
            "equivalent": "# No direct equivalent. This command modifies the sops-config.yml file directly.\n# The update step is equivalent to `sops --config sops-config.yml updatekeys -y <file for each file>`",
            "examples": [
                {
                    "yaml": """# Add a new GPG key to the sops configuration
chaos secrets rotate-add pgp 'FINGERPRINT_OF_NEW_USER'

# Add a new age key and immediately update all secrets
chaos secrets rotate-add age 'age1...' -u"""
                }
            ],
        }

    def explain_rotate_rm(self, detail_level="basic"):
        return {
            "concept": "Revoking an Encryption Key",
            "what": "The `rotate-rm` command removes a key from your `sops-config.yml` configuration.",
            "why": "To revoke access for a person or machine that should no longer be able to decrypt the secrets. This is a critical step when someone leaves a team.",
            "how": "It removes the specified key from all key groups in the `sops-config.yml` file. You must then run `sops updatekeys` (or use the `-u` flag) on your secrets files to re-encrypt them without the revoked key.",
            "equivalent": "# No direct equivalent. This command modifies the sops-config.yml file directly.\n# The update step is equivalent to `sops updatekeys -y <file>`",
            "examples": [
                {"yaml": "chaos secrets rotate-rm pgp 'FINGERPRINT_TO_REMOVE'"}
            ],
        }

    def explain_shamir(self, detail_level="basic"):
        return {
            "concept": "Shamir`s Secret Sharing",
            "what": 'The `shamir` command configures a "M-of-N" policy, where M out of N total keys are required to decrypt a secret. For example, a 2-of-3 policy means any 2 of the 3 specified keys can decrypt the file.',
            "why": "It builds redundancy and prevents a single point of failure. If one person loses their key, others can still access the secrets. It can also be used to require a quorum for highly sensitive data.",
            "how": "It adds or modifies the `shamir_threshold` value in a specific creation rule within your `sops-config.yml` file.",
            "equivalent": "# No direct equivalent. This command modifies the sops-config.yml file directly.",
            "examples": [
                {
                    "yaml": """# Set the first (index 0) rule in .sops.yaml to require 2 keys to decrypt
chaos secrets shamir 0 2"""
                }
            ],
        }

    def explain_import(self, detail_level="basic"):
        return {
            "concept": "Importing Master Keys",
            "what": "The `secrets import` command retrieves a master `age`, `gpg` or `hashicorp vault` key/address from an external password manager (like Bitwarden or 1Password) and saves it to your local environment.",
            "why": "To bootstrap a new machine or team member, allowing them to get the central encryption key from a trusted source without sending it over an insecure channel.",
            "how": "It uses the password manager`s CLI to read the key from a specific item and then saves it to a local file (`keys.txt` for `age`, `vault_keys.txt` for `vault`) or imports it into your local GPG keyring.",
            "equivalent": "# For Bitwarden:\nbw get notes <AGE_ITEM_ID> > keys.txt",
            "examples": [{"yaml": "chaos secrets import bw age --item-id '...' "}],
        }

    def explain_export(self, detail_level="basic"):
        return {
            "concept": "Exporting Master Keys",
            "what": "The `secrets export` command saves a local `age` or `gpg` master key into an external password manager.",
            "why": "To securely back up your master key and make it available for other team members to import.",
            "how": "It reads the key from your local files/keyring and uses the password manager`s CLI to create a new, secure item containing the key material.",
            "equivalent": '# For Bitwarden:\nbw create item --notes "$(cat keys.txt)" --organizationid ... --collectionid ... --name "My Team Age Key"',
            "examples": [
                {
                    "yaml": "chaos secrets export bw age --item-name 'My Team Age Key' --keys ~/.config/chaos/keys.txt"
                }
            ],
        }

    def explain_providers(self, detail_level="basic"):
        return {
            "concept": "Ephemeral Key Providers",
            "what": "The `-p`/`--provider` flag (used with `apply`, `secrets edit`, etc.) tells `chaos` to fetch a decryption key from a password manager for a single operation, without permanently storing it locally.",
            "why": "This is an extremely secure workflow. The master key lives only in the trusted password manager and is only present in your computer`s memory for the few seconds it takes to run the command.",
            "how": "You configure providers in `~/.config/chaos/config.yml`. For example, you can map the name `bw.age` to a specific age key stored in a Bitwarden item. When you run `chaos apply --secrets -p bw.age`, `chaos` automatically fetches that key and uses it for the operation.",
            "equivalent": "# This complex workflow is what `chaos` automates:\nbw get notes <ITEM_ID> > /tmp/tempkey.txt\nSOPS_AGE_KEY_FILE=/tmp/tempkey.txt sops -d secrets.yml\nrm /tmp/tempkey.txt",
        }
