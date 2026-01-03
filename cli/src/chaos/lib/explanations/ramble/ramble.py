class RambleExplain():
    _order = ['create', 'read', 'edit', 'find', 'encrypt', 'update', 'move', 'delete']

    def explain_ramble(self, detail_level='basic'):
        return {
            'concept': 'An Encrypted Personal Knowledge Base',
            'what': 'The `ramble` subsystem is an integrated, file-based journaling or personal wiki system. It allows you to create, manage, and encrypt notes directly from the command line.',
            'why': 'It provides a convenient and secure place to store technical notes, procedural documentation, code snippets, and other bits of knowledge, keeping them co-located with the rest of your system management tools.',
            'how': 'Rambles are organized into "journals" (directories) and "pages" (YAML files) within `~/.local/share/chaos/ramblings/`. Each command manipulates these files, integrating with `sops` for encryption and your `$EDITOR` for content.',
            'security': 'Ramblings can be encrypted with `sops`, making them a safe place to store sensitive information. The `find` command can search through encrypted content.'
        }

    def explain_create(self, detail_level='basic'):
        return {
            'concept': 'Creating a New Note',
            'what': 'The `create` command creates a new ramble journal and/or page.',
            'how': 'If you provide `journal.page`, it creates a `page.yml` inside the `journal` directory. If you just provide `journal`, it creates both the directory and a default `journal.yml` page inside it. It then opens the new file in your `$EDITOR`.',
            'equivalent': 'mkdir -p ~/.local/share/chaos/ramblings/my-journal\n$EDITOR ~/.local/share/chaos/ramblings/my-journal/my-page.yml',
            'examples': [{
                'yaml': "# Create a new page 'networking' in the 'linux' journal\nchaos ramble create linux.networking\n\n# Use the -e flag to encrypt it immediately after creation\nchaos ramble create linux.networking -e"
            }]
        }

    def explain_read(self, detail_level='basic'):
        return {
            'concept': 'Reading a Note',
            'what': 'The `read` command displays the content of one or more ramble pages in a formatted, human-readable way.',
            'how': 'It parses the YAML file and uses the `rich` library to render it with Markdown and syntax highlighting. If the file is `sops`-encrypted, it decrypts it in memory before displaying.',
            'equivalent': '# For unencrypted files:\ncat ramble.yml | rich-cli\n\n# For encrypted files:\nsops -d ramble.sops.yml | rich-cli',
            'examples': [{
                'yaml': "# Read a specific page\nchaos ramble read linux.networking\n\n# List all pages in a journal and prompt to select one to read\nchaos ramble read linux.list"
            }]
        }

    def explain_edit(self, detail_level='basic'):
        return {
            'concept': 'Editing a Note',
            'what': 'The `edit` command opens an existing ramble page in your default editor.',
            'how': 'If the file is encrypted, it uses `sops` to handle the decryption/re-encryption cycle automatically. If not, it opens it directly.',
            'equivalent': '# For unencrypted files:\n$EDITOR ramble.yml\n\n# For encrypted files:\nsops ramble.sops.yml',
            'examples': [{
                'yaml': "chaos ramble edit linux.networking"
            }]
        }

    def explain_find(self, detail_level='basic'):
        return {
            'concept': 'Searching Your Notes',
            'what': 'The `find` command searches through the content of all your rambles for a specific keyword or tag.',
            'how': 'It iterates through all `.yml` files in your ramblings directory, decrypts them if necessary, and performs a case-insensitive search on their content. The `tags` field in your YAML is used for tag-based filtering.',
            'equivalent': "rg 'my-keyword' ~/.local/share/chaos/ramblings/",
            'examples': [{
                'yaml': "# Find all rambles containing the word 'docker'\nchaos ramble find docker\n\n# Find all rambles that have the 'security' tag\nchaos ramble find --tag security"
            }]
        }

    def explain_encrypt(self, detail_level='basic'):
        return {
            'concept': 'Encrypting a Note',
            'what': 'The `encrypt` command applies `sops` encryption to an existing, unencrypted ramble page.',
            'how': 'It uses the `sops` CLI to encrypt the file in-place. By default, it encrypts all fields except for some basic metadata (`title`, `tags`). You can use the `--keys` flag to specify exactly which fields to encrypt.',
            'equivalent': "sops -e -i --encrypted-regex '^(field1|field2)$' my-ramble.yml",
            'examples': [{
                'yaml': "# Encrypt a ramble page\nchaos ramble encrypt journal.page\n\n# Encrypt only the 'my_secret' field in the page\nchaos ramble encrypt journal.page -k my_secret"
            }]
        }

    def explain_update(self, detail_level='basic'):
        return {
            'concept': 'Updating Encryption Keys',
            'what': 'The `update` command (shorthand for `update-encrypt`) runs `sops updatekeys` on all encrypted ramble files.',
            'why': 'After you add or remove a key from your `.sops.yaml` config (using `chaos secrets rotate-add/rm`), you must update your files to apply the change. This command automates that process for your rambles.',
            'equivalent': 'sops updatekeys -y my-ramble.sops.yml',
            'examples': [{
                'yaml': "chaos ramble update"
            }]
        }

    def explain_move(self, detail_level='basic'):
        return {
            'concept': 'Renaming or Moving a Note',
            'what': 'The `move` command renames a page or moves it to a different journal.',
            'equivalent': 'mv ~/.local/share/chaos/ramblings/old.yml ~/.local/share/chaos/ramblings/new.yml',
            'examples': [{
                'yaml': "# Rename a page within the same journal\nchaos ramble move journal.old_name journal.new_name\n\n# Move a page to a different journal\nchaos ramble move old_journal.page new_journal.page"
            }]
        }

    def explain_delete(self, detail_level='basic'):
        return {
            'concept': 'Deleting a Note or Journal',
            'what': 'The `delete` command permanently removes a page or an entire journal.',
            'how': 'It uses standard file system commands to delete the file or directory after asking for confirmation.',
            'equivalent': 'rm ~/.local/share/chaos/ramblings/journal/page.yml\nrm -r ~/.local/share/chaos/ramblings/journal',
            'examples': [{
                'yaml': "# Delete a single page\nchaos ramble delete journal.page_to_delete\n\n# Delete an entire journal and all its pages\nchaos ramble delete journal"
            }]
        }
