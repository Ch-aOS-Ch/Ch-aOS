class RambleExplain:
    _order = ["create", "read", "edit", "find", "encrypt", "update", "move", "delete"]

    def explain_ramble(self, complexity="basic"):
        if complexity == "advanced":
            return {
                "concept": "Programmatic Knowledge Base API",
                "what": "A documentation engine powered by `chaos.lib.ramble`, utilizing `SecretsContext` for secure access.",
                "why": "Allows for the automation of incident response playbooks or automated daily logging via the Ch-aOS SDK.",
                "how": "The SDK handles path traversal protections, transparent `sops` decryption, and YAML serialization through the `Ramble*Payload` DTOs.",
                "security": "Leverages SOPS to seamlessly protect sensitive data integrated directly into the infrastructure code.",
            }
        elif complexity == "intermediate":
            return {
                "concept": "CLI-Native Encrypted Wiki",
                "what": "A file-based knowledge base integrated seamlessly with SOPS encryption.",
                "why": "Enables team-wide, version-controlled documentation that can safely include sensitive data.",
                "how": "Files are stored as YAML. `chaos` commands orchestrate encryption and decryption transparently.",
                "security": "Metadata like titles remain plaintext for fast searching, while file contents are encrypted.",
            }
        else:
            return {
                "concept": "An Encrypted Personal Knowledge Base",
                "what": "The `ramble` subsystem is an integrated journaling or personal wiki system.",
                "why": "It provides a secure place to store technical notes and code snippets alongside your management tools.",
                "how": 'Rambles are organized into "journals" and "pages" within `~/.local/share/chaos/ramblings/`.',
                "security": "Ramblings can be encrypted with `sops`, making them a safe place to store sensitive information.",
            }

    def explain_create(self, complexity="basic"):
        if complexity == "advanced":
            return {
                "concept": "Programmatic File Generation",
                "what": "Uses `RambleCreatePayload` and `handleCreateRamble` to generate files via the SDK.",
                "how": "Resolves target paths and ensures no traversal escapes the base directory. Can bypass the editor to inject automated data directly into the returned file path.",
                "examples": [{"yaml": "chaos ramble create linux.networking -e"}],
            }
        elif complexity == "intermediate":
            return {
                "concept": "Note Initialization",
                "what": "Initializes a new YAML structure for a Ramble note and optionally encrypts it immediately.",
                "how": "Parses `journal.page` to build directories, writes boilerplate YAML, and invokes `$EDITOR`. If `-e` is passed, runs `sops` on the resulting file.",
                "examples": [
                    {
                        "yaml": "chaos ramble create linux.networking\nchaos ramble create linux.networking -e"
                    }
                ],
            }
        else:
            return {
                "concept": "Creating a New Note",
                "what": "The `create` command creates a new ramble journal and/or page.",
                "how": "It creates a `page.yml` inside the `journal` directory and opens it in your `$EDITOR`.",
                "equivalent": "mkdir -p ~/.local/share/chaos/ramblings/my-journal\n$EDITOR ~/.local/share/chaos/ramblings/my-journal/my-page.yml",
                "examples": [{"yaml": "chaos ramble create linux.networking"}],
            }

    def explain_read(self, complexity="basic"):
        if complexity == "advanced":
            return {
                "concept": "Payload-Driven Decryption & Parsing",
                "what": "Constructs a `RambleReadPayload` to safely fetch and decrypt data via `chaos.lib.ramble.handleReadRamble`.",
                "how": "Returns a `ResultPayload` containing a dictionary of requested targets mapped to their parsed YAML content, ideal for programmatically querying playbooks.",
                "examples": [{"yaml": "chaos ramble read linux.networking"}],
            }
        elif complexity == "intermediate":
            return {
                "concept": "In-Memory Rendering",
                "what": "Reads and renders Rambles, decrypting them in-memory automatically if they are SOPS-encrypted.",
                "how": "Detects if a file is encrypted by inspecting its structure. If encrypted, invokes `sops -d` to a memory buffer before parsing YAML for display.",
                "equivalent": "sops -d ramble.sops.yml | rich-cli",
                "examples": [{"yaml": "chaos ramble read linux.networking"}],
            }
        else:
            return {
                "concept": "Reading a Note",
                "what": "The `read` command displays the content of one or more ramble pages.",
                "how": "It parses the YAML file and uses the `rich` library to render it nicely.",
                "equivalent": "cat ramble.yml | rich-cli",
                "examples": [
                    {
                        "yaml": "chaos ramble read linux.networking\nchaos ramble read linux.list"
                    }
                ],
            }

    def explain_edit(self, complexity="basic"):
        if complexity == "advanced":
            return {
                "concept": "Secure Editing Lifecycle via SDK",
                "what": "Executes `handleEditRamble` using `RambleEditPayload`, leveraging `sops` to enforce secure tmpfs editing.",
                "how": "Relies on `chaos.lib.secret_backends.utils` to spin up ephemeral provider environments if a master key needs to be fetched.",
                "examples": [{"yaml": "chaos ramble edit linux.networking"}],
            }
        elif complexity == "intermediate":
            return {
                "concept": "Transparent Decryption/Re-encryption",
                "what": "Provides a secure edit lifecycle for notes, guaranteeing unencrypted data is not permanently written to disk.",
                "how": "Uses `sops` to decrypt to a temporary file, opens `$EDITOR`, and re-encrypts upon exit.",
                "equivalent": "sops ramble.sops.yml",
                "examples": [{"yaml": "chaos ramble edit linux.networking"}],
            }
        else:
            return {
                "concept": "Editing a Note",
                "what": "The `edit` command opens an existing ramble page in your default editor.",
                "how": "If the file is encrypted, it handles the decryption/re-encryption cycle automatically.",
                "equivalent": "$EDITOR ramble.yml",
                "examples": [{"yaml": "chaos ramble edit linux.networking"}],
            }

    def explain_find(self, complexity="basic"):
        if complexity == "advanced":
            return {
                "concept": "Programmatic Database Querying",
                "what": "Invokes `handleFindRamble` via `RambleFindPayload` to search the documentation database.",
                "how": "Returns a list of matching targets in `ResultPayload.data`, allowing SDK users to build custom search integrations.",
                "examples": [
                    {
                        "yaml": "chaos ramble find docker\nchaos ramble find --tag security"
                    }
                ],
            }
        elif complexity == "intermediate":
            return {
                "concept": "Full-Text and Tag-Based Engine",
                "what": "A search engine that traverses both plaintext and SOPS-encrypted rambles.",
                "how": "For encrypted files, it executes bulk in-memory decryption before scanning the YAML structures for the search term or tags.",
                "equivalent": "rg 'my-keyword' ~/.local/share/chaos/ramblings/",
                "examples": [
                    {
                        "yaml": "chaos ramble find docker\nchaos ramble find --tag security"
                    }
                ],
            }
        else:
            return {
                "concept": "Searching Your Notes",
                "what": "The `find` command searches through the content of all your rambles for a keyword or tag.",
                "how": "It performs a case-insensitive search, decrypting files if necessary to read their content.",
                "equivalent": "rg 'my-keyword' ~/.local/share/chaos/ramblings/",
                "examples": [
                    {
                        "yaml": "chaos ramble find docker\nchaos ramble find --tag security"
                    }
                ],
            }

    def explain_encrypt(self, complexity="basic"):
        if complexity == "advanced":
            return {
                "concept": "Targeted Regex Encryption",
                "what": "Constructs a `RambleEncryptPayload` to interface with the SOPS binary via `subprocess`.",
                "how": "Applies precise regex filtering to target fields for encryption, ensuring the file complies with the project's SecretsContext.",
                "examples": [
                    {
                        "yaml": "chaos ramble encrypt journal.page\nchaos ramble encrypt journal.page -k my_secret"
                    }
                ],
            }
        elif complexity == "intermediate":
            return {
                "concept": "In-Place SOPS Conversion",
                "what": "Converts a plaintext YAML file into a SOPS-encrypted file based on your `.sops.yaml` creation rules.",
                "how": "Calls `sops encrypt -i` on the file, using `--encrypted-regex` to protect specific fields while leaving `title` and `tags` plaintext.",
                "equivalent": "sops encrypt -i --encrypted-regex '...' my-ramble.yml",
                "examples": [
                    {
                        "yaml": "chaos ramble encrypt journal.page\nchaos ramble encrypt journal.page -k my_secret"
                    }
                ],
            }
        else:
            return {
                "concept": "Encrypting a Note",
                "what": "The `encrypt` command applies encryption to an existing, unencrypted ramble page.",
                "how": "It uses `sops` to encrypt the file in-place, keeping metadata like `title` unencrypted by default.",
                "equivalent": "sops encrypt ... my-ramble.yml",
                "examples": [
                    {
                        "yaml": "chaos ramble encrypt journal.page\nchaos ramble encrypt journal.page -k my_secret"
                    }
                ],
            }

    def explain_update(self, complexity="basic"):
        if complexity == "advanced":
            return {
                "concept": "Batch SOPS Re-encryption",
                "what": "Uses `RambleUpdateEncryptPayload` to trigger a batch SOPS re-encryption operation.",
                "why": "Re-evaluates every encrypted file against current `.sops.yaml` creation rules, adding or stripping master keys as necessary.",
                "examples": [{"yaml": "chaos ramble update"}],
            }
        elif complexity == "intermediate":
            return {
                "concept": "Automated Key Propagation",
                "what": "Automates the `sops updatekeys` process across the entire `ramblings/` directory.",
                "why": "Ensures that key rotations (adding a new team member, revoking an old key) are applied to every encrypted note.",
                "equivalent": "sops updatekeys -y my-ramble.sops.yml",
                "examples": [{"yaml": "chaos ramble update"}],
            }
        else:
            return {
                "concept": "Updating Encryption Keys",
                "what": "The `update` command updates the encryption keys for all your rambles.",
                "why": "Necessary after adding or removing a key from your configuration.",
                "equivalent": "sops updatekeys -y my-ramble.sops.yml",
                "examples": [{"yaml": "chaos ramble update"}],
            }

    def explain_move(self, complexity="basic"):
        if complexity == "advanced":
            return {
                "concept": "Safe File Relocation via SDK",
                "what": "Constructs a `RambleMovePayload` to execute file relocation.",
                "how": "Performs strict path validation to prevent traversal attacks outside the designated `ramblings/` directory during `os.rename`.",
                "examples": [
                    {"yaml": "chaos ramble move old_journal.page new_journal.page"}
                ],
            }
        elif complexity == "intermediate":
            return {
                "concept": "Namespace and File Renaming",
                "what": "Safely relocates a Ramble page between journals or renames it.",
                "how": "Resolves the old and new `journal.page` structures into absolute paths and moves the underlying file.",
                "equivalent": "mv ~/.local/share/chaos/ramblings/old.yml ~/.local/share/chaos/ramblings/new.yml",
                "examples": [{"yaml": "chaos ramble move journal.old journal.new"}],
            }
        else:
            return {
                "concept": "Renaming or Moving a Note",
                "what": "The `move` command renames a page or moves it to a different journal.",
                "equivalent": "mv ~/.local/share/chaos/ramblings/old.yml ~/.local/share/chaos/ramblings/new.yml",
                "examples": [
                    {
                        "yaml": "chaos ramble move journal.old_name journal.new_name\nchaos ramble move old_journal.page new_journal.page"
                    }
                ],
            }

    def explain_delete(self, complexity="basic"):
        if complexity == "advanced":
            return {
                "concept": "Programmatic Deletion",
                "what": "Constructs a `RambleDeletePayload` for destructive operations via the SDK.",
                "how": "Provides `i_know_what_im_doing` flag integration to bypass interactive prompts when deleting files in scripts.",
                "examples": [{"yaml": "chaos ramble delete journal.page_to_delete"}],
            }
        elif complexity == "intermediate":
            return {
                "concept": "Documentation Removal",
                "what": "Removes documentation files or entire directories from the filesystem.",
                "how": "Parses the target path and recursively deletes a journal or removes a specific YAML file.",
                "equivalent": "rm -r ~/.local/share/chaos/ramblings/journal",
                "examples": [{"yaml": "chaos ramble delete journal"}],
            }
        else:
            return {
                "concept": "Deleting a Note or Journal",
                "what": "The `delete` command permanently removes a page or an entire journal.",
                "how": "It uses standard file system commands after asking for confirmation.",
                "equivalent": "rm ~/.local/share/chaos/ramblings/journal/page.yml",
                "examples": [
                    {
                        "yaml": "chaos ramble delete journal.page_to_delete\nchaos ramble delete journal"
                    }
                ],
            }
