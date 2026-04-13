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

    def explain_age(self, complexity="basic"):
        if complexity == "advanced":
            return {
                "concept": "Cryptographic Standard for SOPS",
                "what": "A cryptographic standard natively supported by Mozilla SOPS for data key wrapping.",
                "why": "Provides robust asymmetric encryption. Its simplicity makes it easy to store in external providers and inject via environment variables (`SOPS_AGE_KEY`).",
                "how": "The SDK passes the age identity to SOPS. When rotating, `chaos.lib.secrets` manipulates the `age` array in the SOPS creation rules.",
            }
        elif complexity == "intermediate":
            return {
                "concept": "Modern Encryption Format",
                "what": "A fast, modern encryption format utilizing X25519, ChaCha20-Poly1305, and HMAC-SHA256.",
                "why": "It lacks the complex web-of-trust of GPG, making it ideal for automated secrets management.",
                "how": "Public keys are added to `.sops.yaml`. Ch-aOS uses the private keys to decrypt data.",
                "equivalent": "age-keygen -y key.txt",
            }
        else:
            return {
                "concept": "Age Encryption",
                "what": "Age is a simple, modern, and secure file encryption tool.",
                "why": "It is often preferred for its simplicity over GPG.",
                "how": "`chaos` manages `age` keys in `sops-config.yml` to encrypt/decrypt secrets.",
                "equivalent": "age-keygen -o key.txt",
                "learn_more": ["age GitHub Repository", "ssh-to-age Tool"],
            }

    def explain_gpg(self, complexity="basic"):
        if complexity == "advanced":
            return {
                "concept": "PGP Backend for SOPS",
                "what": "An established cryptographic backend for SOPS, utilizing PGP packets.",
                "why": "Supports complex key management. Ch-aOS interacts with GPG via `subprocess`, handling key imports into temporary GNUPGHOME directories during ephemeral provider usage.",
                "how": "The `chaos.lib.secret_backends` modules handle exporting ascii-armored blocks and injecting them into the GPG agent dynamically.",
            }
        elif complexity == "intermediate":
            return {
                "concept": "GNU Privacy Guard (OpenPGP)",
                "what": "GNU Privacy Guard, implementing the OpenPGP standard for asymmetric encryption.",
                "why": "Useful if a team already relies heavily on GPG infrastructure or smartcards (like YubiKey).",
                "how": "Ch-aOS orchestrates GPG via SOPS, using your local keyring to decrypt. Fingerprints are stored in `.sops.yaml`.",
                "equivalent": "gpg --list-secret-keys --keyid-format LONG",
            }
        else:
            return {
                "concept": "GPG Encryption",
                "what": "GPG is a widely used standard for encrypting files.",
                "why": "It is a battle-tested method for encrypting and decrypting secrets.",
                "how": "`chaos` manages GPG key fingerprints in `sops-config.yml`.",
                "equivalent": "gpg --full-generate-key",
            }

    def explain_vault(self, complexity="basic"):
        if complexity == "advanced":
            return {
                "concept": "Vault Transit API Integration",
                "what": "Integration with Vault's Transit API for SOPS data key unwrapping.",
                "why": "Shifts cryptographic operations to the Vault server. `chaos` simply configures the Vault URI in `.sops.yaml`.",
                "how": "The SDK ensures environment variables are propagated to the SOPS subprocess, which makes HTTP API calls to Vault for KMS operations.",
            }
        elif complexity == "intermediate":
            return {
                "concept": "KMS Backend for SOPS",
                "what": "A KMS (Key Management Service) backend for SOPS, using Vault's Transit secrets engine.",
                "why": "Allows dynamic secret generation and strict auditing without distributing master private keys.",
                "how": "Ensure `VAULT_ADDR` and `VAULT_TOKEN` are set. SOPS communicates directly with Vault to encrypt/decrypt.",
            }
        else:
            return {
                "concept": "HashiCorp Vault Integration",
                "what": "HashiCorp Vault securely manages secrets and encryption keys.",
                "why": "It is valuable in complex infrastructure setups for centralized policy enforcement.",
                "how": "`chaos` manages Vault URIs in your `sops-config.yml`.",
            }

    def explain_sops(self, complexity="basic"):
        if complexity == "advanced":
            return {
                "concept": "Foundational Cryptographic Layer",
                "what": "The foundational cryptographic layer for `chaos.lib.secrets`. A Go binary that wraps data keys using multiple providers.",
                "why": "Supports Shamir's Secret Sharing and multiple key groups, enabling complex RBAC.",
                "how": "The SDK executes the SOPS binary via strict subprocess calls, parsing output into OmegaConf dicts, managing environment variables dynamically.",
                "files": ["sops-config.yml", "secrets.yml", ".sops.yaml"],
            }
        elif complexity == "intermediate":
            return {
                "concept": "Secrets OPerationS (SOPS)",
                "what": "A CLI tool that uses KMS, GPG, or Age to encrypt the leaf nodes of a document.",
                "why": "Provides readable git diffs since keys remain plaintext, making code review possible.",
                "how": "Ch-aOS generates a `.sops.yaml` creation rule file used by SOPS to determine encryption keys.",
                "files": ["sops-config.yml", "secrets.yml", ".sops.yaml"],
            }
        else:
            return {
                "concept": "Secrets OPerationS (SOPS)",
                "what": "SOPS encrypts structured files (YAML, JSON), encrypting only values, not keys.",
                "why": "It allows you to safely commit encrypted files to Git.",
                "how": "Ch-aOS uses SOPS as its core encryption engine.",
                "files": ["sops-config.yml", "secrets.yml", ".sops.yaml"],
            }

    def explain_bw(self, complexity="basic"):
        if complexity == "advanced":
            return {
                "concept": "Provider Backend (`bw`)",
                "what": "A subclass of `Provider` in `chaos.lib.secret_backends` interacting with the Bitwarden CLI.",
                "why": "Facilitates the ephemeral key workflow, isolating private keys from the filesystem.",
                "how": "The `setupEphemeralEnv` method executes `bw`, writes to a tmpfs or named pipe before invoking SOPS, and cleans up immediately.",
            }
        elif complexity == "intermediate":
            return {
                "concept": "Bitwarden Provider Plugin",
                "what": "A Secret Provider plugin for the Bitwarden Password Manager.",
                "why": "Transforms static Age/GPG keys into IAM-like access by storing them in Bitwarden secure notes.",
                "how": "Requires an unlocked vault (`BW_SESSION`). `chaos` extracts the note via `bw get notes <id>` into memory.",
            }
        else:
            return {
                "concept": "Bitwarden CLI Integration",
                "what": "The `bw` CLI allows `chaos` to interact with Bitwarden to store master keys.",
                "why": "It securely stores master keys so they aren't kept locally.",
                "how": "`chaos` uses `bw` to fetch keys ephemerally to decrypt `sops` files.",
            }

    def explain_bws(self, complexity="basic"):
        if complexity == "advanced":
            return {
                "concept": "Provider Backend (`bws`)",
                "what": "A `Provider` implementation utilizing the `bws` binary.",
                "why": "Provides robust, token-based authentication for the Ch-aOS SDK to dynamically load keys in headless environments.",
                "how": "Extracts the `value` field from the JSON response of `bws`, injecting it into the SOPS context.",
            }
        elif complexity == "intermediate":
            return {
                "concept": "Bitwarden Secrets Integration",
                "what": "Integrates with Bitwarden Secrets Manager for machine-to-machine secret access.",
                "why": "Ideal for CI/CD pipelines where a standard password manager vault is inappropriate.",
                "how": "Fetches secrets via `bws secret get <id>` using service account tokens.",
            }
        else:
            return {
                "concept": "Bitwarden Secrets CLI Integration",
                "what": "The `bws` CLI tool allows `chaos` to store master encryption keys in Bitwarden Secrets.",
                "why": "It provides an enterprise-focused way to manage master keys for applications.",
                "how": "Requires the BWS_ACCESS_TOKEN to retrieve keys ephemerally.",
            }

    def explain_op(self, complexity="basic"):
        if complexity == "advanced":
            return {
                "concept": "Provider Backend (`op`)",
                "what": "A `Provider` backend relying on the 1Password CLI.",
                "why": "Integrates with 1Password's advanced RBAC and audit logging for master key access.",
                "how": "The SDK parses `op://vault/item/field` URIs from the global config, fetches the payload, and establishes the SOPS environment.",
            }
        elif complexity == "intermediate":
            return {
                "concept": "1Password Provider Plugin",
                "what": "A Secret Provider plugin for 1Password, utilizing `op://` URIs.",
                "why": "Leverages 1Password's strong security model and biometric unlock capabilities.",
                "how": "Uses `op read` to fetch the contents of a secure note. Requires an active `OP_SESSION`.",
            }
        else:
            return {
                "concept": "1Password CLI Integration",
                "what": "The `op` CLI allows `chaos` to interact with 1Password to manage master keys.",
                "why": "A secure, cross-platform option for teams already using 1Password.",
                "how": "`chaos` fetches keys ephemerally from 1Password items.",
            }

    def explain_secrets(self, complexity="basic"):
        if complexity == "advanced":
            return {
                "concept": "Programmatic API (`chaos.lib.secrets`)",
                "what": "A programmatic API for managing encrypted payloads via `SecretsContext`.",
                "why": "Ensures infrastructure automation can securely handle credentials without leaking them.",
                "how": "Utilizes `decrypt_secrets()` which handles file resolution, provider instantiation, subprocess execution, and deserialization.",
            }
        elif complexity == "intermediate":
            return {
                "concept": "SOPS Lifecycle Subsystem",
                "what": "The subsystem that handles the SOPS lifecycle, abstracting away complex command-line arguments.",
                "why": "Provides a unified CLI interface for editing, reading, and rotating keys.",
                "how": "Reads `.sops.yaml` to identify key groups and integrates with providers for key retrieval.",
            }
        else:
            return {
                "concept": "Encrypted Secret Management",
                "what": "A 'secret' is sensitive information (passwords, API keys) stored securely.",
                "why": "Allows safe storage of sensitive data in git projects using encryption.",
                "how": "Commands orchestrate `sops` using a `sops-config.yml` to determine keys.",
            }

    def explain_edit(self, complexity="basic"):
        if complexity == "advanced":
            return {
                "concept": "Interactive SOPS Subprocess",
                "what": "Constructs a `SecretsEditPayload` to execute SOPS in interactive mode.",
                "how": "The SDK resolves the SOPS configuration based on `SecretsContext`, sets up ephemeral provider keys, and hands over TTY control to the SOPS subprocess.",
                "examples": [{"yaml": "chaos secrets edit -t my-company.my-team"}],
            }
        elif complexity == "intermediate":
            return {
                "concept": "Native Editing via SOPS",
                "what": "Invokes the native editing capabilities of SOPS.",
                "why": "Prevents accidental commits of plaintext secrets to version control.",
                "how": "SOPS decrypts the file to a secure temporary location, launches `$EDITOR`, waits, and re-encrypts.",
                "equivalent": "sops ... secrets.yml",
                "examples": [{"yaml": "chaos secrets edit"}],
            }
        else:
            return {
                "concept": "Securely Editing Secrets",
                "what": "Decrypts a secrets file, opens it in your editor, and re-encrypts it.",
                "why": "A seamless workflow for editing secrets without permanently saving them unencrypted.",
                "equivalent": "sops ... secrets.yml",
                "examples": [
                    {
                        "yaml": "chaos secrets edit\nchaos secrets edit -t my-company.my-team"
                    }
                ],
            }

    def explain_print(self, complexity="basic"):
        if complexity == "advanced":
            return {
                "concept": "Raw SDK Decryption",
                "what": "Executes `handlePrintSecrets` with a `SecretsPrintPayload`.",
                "how": "The SDK fetches the raw string via `decrypt_secrets()`. If `no_pretty` is true, it dumps raw text; otherwise, it formats it via `rich`.",
                "examples": [{"yaml": "chaos secrets print"}],
            }
        elif complexity == "intermediate":
            return {
                "concept": "Full SOPS Decryption",
                "what": "Performs a full decryption of the SOPS file to `stdout`.",
                "why": "To inspect the plaintext YAML structure. Use `--no-pretty` for raw YAML/JSON output for `jq` processing.",
                "how": "Calls `sops -d` and captures the output.",
                "equivalent": "sops -d secrets.yml",
                "examples": [{"yaml": "chaos secrets print"}],
            }
        else:
            return {
                "concept": "Securely Viewing Secrets",
                "what": "Decrypts a secrets file and prints its contents to standard output.",
                "why": "Useful for quick reviews or piping decrypted content into scripts.",
                "equivalent": "sops -d secrets.yml",
                "examples": [{"yaml": "chaos secrets print"}],
            }

    def explain_cat(self, complexity="basic"):
        if complexity == "advanced":
            return {
                "concept": "OmegaConf Dictionary Traversal",
                "what": "Utilizes `SecretsCatPayload` and `OmegaConf` for dictionary traversal.",
                "how": "After in-memory decryption, the string is loaded into a `DictConfig`. The dot-path is evaluated, and the specific node is serialized to stdout.",
                "examples": [{"yaml": "chaos secrets cat user_secrets.dex.password"}],
            }
        elif complexity == "intermediate":
            return {
                "concept": "Nested Key Extraction",
                "what": "Extracts deeply nested keys from the decrypted YAML/JSON structure.",
                "why": "Ideal for shell scripts needing a single password without exposing the entire secret document.",
                "how": "Decrypts the file in-memory, traverses the dictionary using dot notation, and prints the result.",
                "examples": [{"yaml": "chaos secrets cat user_secrets.dex.password"}],
            }
        else:
            return {
                "concept": "Viewing Specific Secret Values",
                "what": "Decrypts a secrets file and prints only the specific value(s) requested.",
                "why": "More secure and convenient for scripting than printing the whole file.",
                "how": "Uses a dot-separated path to extract the value.",
                "examples": [{"yaml": "chaos secrets cat user_secrets.dex.password"}],
            }

    def explain_rotate_add(self, complexity="basic"):
        if complexity == "advanced":
            return {
                "concept": "Programmatic SOPS Rules Modification",
                "what": "Constructs a `SecretsRotatePayload` to programmatically update SOPS creation rules.",
                "how": "Uses a YAML parser that preserves comments to edit `.sops.yaml`. If `update_confirmed` is true, sequentially runs `sops updatekeys` on all discovered files.",
                "examples": [{"yaml": "chaos secrets rotate-add age 'age1...' -u"}],
            }
        elif complexity == "intermediate":
            return {
                "concept": "Key Rotation Lifecycle",
                "what": "Mutates `.sops.yaml` creation rules to include a new public key or KMS URI.",
                "why": "Adding the key allows SOPS to encrypt the data key for the new recipient.",
                "how": "Reads `.sops.yaml`, appends the key string to the appropriate backend array, and writes it back.",
                "examples": [
                    {"yaml": "chaos secrets rotate-add pgp 'FINGERPRINT_OF_NEW_USER'"}
                ],
            }
        else:
            return {
                "concept": "Adding a New Encryption Key",
                "what": "Adds a new key to `sops-config.yml`.",
                "why": "To grant a new person or machine access to the secrets.",
                "how": "Modifies the config file. Use `-u` to immediately update all files.",
                "examples": [
                    {
                        "yaml": "chaos secrets rotate-add pgp 'FINGERPRINT_OF_NEW_USER'\nchaos secrets rotate-add age 'age1...' -u"
                    }
                ],
            }

    def explain_rotate_rm(self, complexity="basic"):
        if complexity == "advanced":
            return {
                "concept": "Cryptographic Revocation via Payload",
                "what": "Uses `SecretsRotatePayload` to revoke cryptographic access.",
                "how": "Modifies the AST of `.sops.yaml`. It's critical to trigger a re-encryption (`updatekeys`) immediately to strip the old wrapped data key.",
                "examples": [
                    {"yaml": "chaos secrets rotate-rm pgp 'FINGERPRINT_TO_REMOVE'"}
                ],
            }
        elif complexity == "intermediate":
            return {
                "concept": "Rule Mutating Revocation",
                "what": "Removes a specified public key from the `.sops.yaml` creation rules.",
                "why": "Ensures that the next time a file is updated, the removed key's wrapped data key is stripped from the file.",
                "how": "Searches YAML arrays for the exact string match and removes it.",
                "examples": [
                    {"yaml": "chaos secrets rotate-rm pgp 'FINGERPRINT_TO_REMOVE'"}
                ],
            }
        else:
            return {
                "concept": "Revoking an Encryption Key",
                "what": "Removes a key from your `sops-config.yml` configuration.",
                "why": "To revoke access for a person or machine.",
                "how": "Removes the key from the config file. You must then run `sops updatekeys` to re-encrypt.",
                "examples": [
                    {"yaml": "chaos secrets rotate-rm pgp 'FINGERPRINT_TO_REMOVE'"}
                ],
            }

    def explain_shamir(self, complexity="basic"):
        if complexity == "advanced":
            return {
                "concept": "Cryptographic Quorum Enforcement",
                "what": "Utilizes `SecretsSetShamirPayload` to enforce cryptographic quorum.",
                "how": "SOPS generates the data key, uses Shamir's Secret Sharing to split it into N parts, wrapping each part. M parts are needed to reconstruct the data key.",
                "examples": [{"yaml": "chaos secrets shamir 0 2"}],
            }
        elif complexity == "intermediate":
            return {
                "concept": "Key Splitting in SOPS",
                "what": "Implements key splitting logic in SOPS via the `.sops.yaml` configuration.",
                "why": "Useful for quorum-based decryption (e.g., requiring 2 admins to decrypt).",
                "how": "Sets the `shamir_threshold` integer on a specific creation rule index.",
                "examples": [{"yaml": "chaos secrets shamir 0 2"}],
            }
        else:
            return {
                "concept": "Shamir's Secret Sharing",
                "what": "Configures an M-of-N policy, where M out of N keys are required to decrypt.",
                "why": "Builds redundancy and prevents a single point of failure.",
                "how": "Modifies the `shamir_threshold` in your `sops-config.yml`.",
                "examples": [{"yaml": "chaos secrets shamir 0 2"}],
            }

    def explain_import(self, complexity="basic"):
        if complexity == "advanced":
            return {
                "concept": "Provider API Retrieval",
                "what": "Executes `Provider.readKeys` and routes the output to persistent local storage.",
                "how": "If the `# NO-IMPORT` marker is detected in the payload, the SDK raises a security exception, enforcing distribution-only key management.",
                "examples": [{"yaml": "chaos secrets import bw age --item-id '...' "}],
            }
        elif complexity == "intermediate":
            return {
                "concept": "Master Key Download",
                "what": "Downloads a master private key from an external vault to local disk or keyring.",
                "why": "For users who prefer persistent local keys rather than the ephemeral `-p` workflow.",
                "how": "Authenticates via the provider plugin, fetches the secret payload, and writes it locally.",
                "examples": [{"yaml": "chaos secrets import bw age --item-id '...' "}],
            }
        else:
            return {
                "concept": "Importing Master Keys",
                "what": "Retrieves a master key from a password manager and saves it locally.",
                "why": "To bootstrap a new machine, getting the encryption key securely.",
                "how": "Uses the password manager's CLI to read the key and saves it to a local file.",
                "examples": [{"yaml": "chaos secrets import bw age --item-id '...' "}],
            }

    def explain_export(self, complexity="basic"):
        if complexity == "advanced":
            return {
                "concept": "Provider API Injection",
                "what": "Executes `Provider.export_secrets` via the `SecretsExportPayload`.",
                "how": "Can optionally append a `# NO-IMPORT` marker to the payload before transmission, establishing a one-way security boundary for the master key.",
                "examples": [
                    {
                        "yaml": "chaos secrets export bw age --item-name 'Key' --keys ~/.config/chaos/keys.txt"
                    }
                ],
            }
        elif complexity == "intermediate":
            return {
                "concept": "Centralized Key Upload",
                "what": "Uploads an existing private key to a centralized secret provider.",
                "why": "Enables the ephemeral workflow for the team and acts as a secure backup.",
                "how": "Reads `keys.txt` or exports from the GPG keyring, then calls the provider's creation API.",
                "examples": [
                    {
                        "yaml": "chaos secrets export bw age --item-name 'Key' --keys ~/.config/chaos/keys.txt"
                    }
                ],
            }
        else:
            return {
                "concept": "Exporting Master Keys",
                "what": "Saves a local master key into an external password manager.",
                "why": "To securely back up your key and share it with the team.",
                "how": "Reads the local key and uses the password manager's CLI to create a new item.",
                "examples": [
                    {
                        "yaml": "chaos secrets export bw age --item-name 'Key' --keys ~/.config/chaos/keys.txt"
                    }
                ],
            }

    def explain_providers(self, complexity="basic"):
        if complexity == "advanced":
            return {
                "concept": "Provider Abstract Base Class",
                "what": "Implementation of the `Provider` abstract base class in `chaos.lib.secret_backends`.",
                "how": "The `SecretsContext` carries the `ProviderConfigPayload`. `decrypt_secrets()` uses a context manager (`setupEphemeralEnv`) to execute retrieval logic and securely zero the memory/files on exit.",
                "equivalent": "SOPS_AGE_KEY_FILE=/tmp/tempkey.txt sops -d secrets.yml",
            }
        elif complexity == "intermediate":
            return {
                "concept": "Plugin Architecture for CLIs",
                "what": "A plugin architecture that bridges Ch-aOS with external password manager CLIs.",
                "why": "Eliminates the need for long-lived private keys on disks, mitigating filesystem exfiltration.",
                "how": "When `-p` is used, the provider class is instantiated, authenticates, fetches the key to a tmpfs or env var, runs SOPS, and cleans up.",
            }
        else:
            return {
                "concept": "Ephemeral Key Providers",
                "what": "The `-p` flag tells `chaos` to fetch a decryption key for a single operation.",
                "why": "Extremely secure workflow. The key lives only in memory for a few seconds.",
                "how": "You configure providers in `~/.config/chaos/config.yml` (e.g., `bw.age`).",
                "equivalent": "SOPS_AGE_KEY_FILE=/tmp/tempkey.txt sops -d secrets.yml",
            }
