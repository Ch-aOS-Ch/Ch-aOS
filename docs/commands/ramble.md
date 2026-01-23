# Command: `chaos ramble`

The `ramble` subsystem is an integrated, file-based personal knowledge base or wiki system. It allows you to create, edit, search, and encrypt notes directly from the command line.

**Why?** It's a convenient place to store technical notes, documentation, code snippets, and ideas co-located with your system management tools. Since notes can be encrypted with `sops`, it's also a safe place for sensitive information.

Note that chaos ramble is completely intagrated with chaos team and chaos secrets, this makes the documentation something you can share with your team and all of you will be able to share the same versionated, encryptad and auditable documentation, all from inside the same CLI that helps you with your workflow.

Rambles are organized into "journals" (directories) and "pages" (YAML files) within `~/.local/share/chaos/ramblings/`.

## `ramble create`

Creates a new ramble journal and/or page, then opens it in your default editor.

**Usage:**
```bash
chaos ramble create <journal.page>
```

-   If you provide `journal.page`, it creates `page.yml` inside the `journal` directory.

-   You can use the `-e` flag to encrypt the note immediately after creation.

**Example:**
```bash
# Create a new page 'networking' in the 'linux' journal
chaos ramble create linux.networking

# Create and encrypt a new page
chaos ramble create security.passwords -e
```

## `ramble read`

Displays the content of one or more ramble pages in a formatted, human-readable way. If the file is encrypted, it decrypts it in memory before displaying.

**Usage:**
```bash
chaos ramble read <journal.page_or_list>
```

-   Use `journal.page` to read a specific page.

-   Use `journal.list` to list all pages in a journal and be prompted to select one.

**Example:**
```bash
# Read a specific page
chaos ramble read linux.networking
```

## `ramble edit`

Opens an existing ramble page in your default editor. If the file is encrypted, it uses `sops` to handle the decryption and re-encryption cycle automatically.

**Usage:**
```bash
chaos ramble edit <journal.page>
```

## `ramble find`

Searches through the content of all your rambles for a specific keyword or tag. The search is case-insensitive and works on encrypted files.

**Usage:**
```bash
# Find all rambles containing the word 'docker'
chaos ramble find docker

# Find all rambles that have the 'security' tag
chaos ramble find --tag security
```

## `ramble encrypt`

Applies `sops` encryption to an existing, unencrypted ramble page.

**Usage:**
```bash
chaos ramble encrypt <journal.page> [-k key_to_encrypt]
```

By default, it encrypts most fields, but you can use the `-k` flag to specify exactly which YAML keys to encrypt.

## `ramble update`

Updates the encryption keys for all encrypted ramble files. This is necessary after you add or remove a key from your `.sops.yaml` configuration using `chaos secrets rotate-add/rm`.

**Usage:**
```bash
chaos ramble update
```

## `ramble move`

Renames a page or moves it to a different journal.

**Usage:**
```bash
# Rename a page
chaos ramble move journal.old_name journal.new_name

# Move a page to a different journal
chaos ramble move old_journal.page new_journal.page
```

## `ramble delete`

Permanently removes a page or an entire journal after asking for confirmation.

**Usage:**
```bash
# Delete a single page
chaos ramble delete journal.page_to_delete

# Delete an entire journal and all its pages
chaos ramble delete journal
```
