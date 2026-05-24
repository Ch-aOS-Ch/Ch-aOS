# Ch-aOS lore

Ch-aOS is a very... how should I put it... "namey" typa tool. You'll often find a lot of new words in the docs and in the tool, this glossary should help you connect the dots and understand what they mean.

Ch-aOS is heavily inspired by Greek mythology, real world greek nomenclature and to nautical themes, you'll find a lot of references to all of those in the names of the concepts and components of Ch-aOS.

| Term | Definition | Comparison with normal names |
| --- | --- | --- |
| **Ch-aOS** | It's the tool itself. Pronounced "Kaos", means "Change an OS". | It's just the name of the tool... Like Ansible or smth. |
| **Ch-obolo** | Pure data files written in pure YAML. They are the "source of truth" for Ch-aOS, and are declarative. | Think of it as "config files", but for the entire OS, like on Ansible's Playbooks. |
| **Soul(s)** | Ch-aOS' plugins. They are written in Python and can be used to extend pretty much anything in Ch-aOS. | Literally "plugins". There ain't much here chief. |
| **Styx** | Where do Souls go when they die? To the Styx, of course! It's a registry of Souls, where you can find and invoke them. | Ansible's "Galaxy", but for Ch-aOS' Souls. It's a place to find and share Souls with the community. Also, it's decentralized, so anyone can host their own Styx and share their Souls there. |
| **Roles** | Soul Python/Pyinfra scripts that consume the Ch-obolo data and generate actual changes on the system. They are imperative. | Think of them as "tasks" or "modules" in Ansible, but they are more powerful and can do more complex things. |
| **Fleet** | A collection of hosts that share the same Ch-obolo. They are defined in the Ch-obolo itself, and can be restricted with the "restrictions" field. | Think of it as "inventory groups" in Ansible. |
| **Boats** | Soul Python scripts used to generate dynamic fleets at runtime. They are also defined in the Ch-obolo (you'll be reading this allot). | Think of them as "dynamic inventory scripts" in Ansible, but they are more powerful and can do more complex things. |
| **Logbook** | No, this is NOT just a buncha logs. The Logbook is Ch-aOS' observability and monitoring system. It collects data from the Roles and the system, and saves it in a Limani. | Basically a "giga verbose" mode that saves all data to a local or remote database. |
| **Limani** | A Soul database used by the Logbook to store all the data. It can be local (SQLite) or remote (PostgreSQL). | Just a fancy name for "database", but it's specifically designed for Ch-aOS' needs. |
| **Providers** | Souls that provide private keys for Ch-aOS' secret management system. They are used to go to a vault/secret manager/password manager and retrieve the private keys needed to decrypt the secrets in the Ch-obolo. | There... there ain't much to compare here, I mean, it's quite a different concept from normal names. |
| **Restrictions** | A field in the Ch-obolo that allows you to restrict the execution of Roles to certain hosts or groups. | Think of it as "when" or "tags" in Ansible. |
| **Explanations** | Inline documentations for Souls. Provided by, well, you guessed it, a type of Soul. | Man or Ansible-doc are the first to come to mind. |
| **Ch-aronte** | Ch-aronte is the Arch Linux core Soul for Ch-aOS. It provides all the basic functionalities needed to manage an Arch Linux installation through Ch-aOS. | IDK, Ansible's builtins? But this does not come pre-installed with Ch-aOS, so idk what really to compare it to. Also, Fun fact, this was the Tool's original name and implementation, back when it was just a few shell scripts with Ansible to manage and install Arch from scratch! |
| **Ch-ronos** | Ch-ronos is a Core Soul for Debian in Ch-aOS. | Ch-aronte, but for Debian. (WIP) |
| **Ch-iron** | Ch-iron is a Core Soul for Fedora in Ch-aOS. | Ch-aronte, but for Fedora. (WIP) |
| **Ch-imera** | Ch-imeira is a Soul for cross-compilation between Ch-aOS' Ch-obolos and NixOS | Idk chief, there ain't really a lotta comparisons to be made here, it's quite a unique concept. (WIP) |
| **Ch-aotic way** | The "Ch-aotic way" is Ch-aOS' philisophy and approach to system management. We focus on flexibility, extensibility, and community-driven development, HOWEVER, we also focus on clear pipelines, fast and efficient execution, and good UX. There are a lot of best practices and patterns that we encourage, and most of them are clearly documented through docstrings (for your LSP) and through this docs. | Clean Code? IDK, it really isn't that biiiig of a deal yk? |
