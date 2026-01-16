# Chopping Board

**Some of the future work** I plan to do on the Ch-aOS Project Suite. Feel free to contribute or suggest new features!

## (The obvious ones) Ch-iron and Ch-ronos

**Fedora and Debian based official cores** Ch-aronte is just the beginning! Official cores for other popular distributions like Fedora (Ch-iron) and Debian/Ubuntu (Ch-ronos) to expand Ch-aOS' reach and usability.

## Installation From 0 to fine-tuning

**A complete installation flow** that takes the user from a bare-metal system to a fully configured environment, including partitioning, bootloader setup, and post-install configurations, using the same declarative approach and plugin based architecture. (chaos.installers)

## Better Fleet Manaegment

**You know Ansible's dinamic inventories?** Something similar, but following Ch-aOS' design principles. A way to manage multiple systems declaratively through an plugin-based declarative inventory system, think "chaos-ec2-boat" that dinamically fetches instances from AWS EC2 and applies Ch-aOS configurations to them. (chaos.boats)

## (the big one) Ch-imera: Ch-obolo to nix mini-compilers

**NixOS is, obviously, the best declarative OS out there.** Its got atomicity, rollbacks, a MASSIVE repo, and a great community. But its language is complex, and its learning curve steep. What if we could compile Ch-aOS' Ch-obolos to Nix expressions? This would allow users to leverage NixOS' strengths while enjoying Ch-aOS' simplicity and modularity! Of course, tho, this isn't all roses, Ch-obolo generated Nix expressions would (and should) be limited, since... Well, since Ch-obolos are written in a non-Turing complete language. But still, this could be a great way to bridge the gap between the two systems, bringing a more common approach to IaC (YAML) to NixOS systems! (chaos.compilers.chimera since, if this works, we could just add a compiler for guix, for instance!)

## Atomicity and Rollbacks

**Atomicity is Important. Period.** Implementing atomic operations is more of a roles problem than a core one, however, Ch-aOS' core could provide a built-in mechanism to support atomic and granular _rollbacks_, for instance, saving the state of the *Ch-obolos* inside ovf /var/lib after applying all changes, this would allow users to revert to a previous state in case of breakage. Atomicity can be achieved by using try/except blocks in python roles, this approach would require roles to be written with atomicity in mind, like normal configuration managers do.
+1 I can already hear you say "but what about using filesystem snapshots?" Well, yes, that could be an option, but it would require users to use specific filesystems (like btrfs or zfs) and would add complexity to the core. This approach would be more universal and easier to implement across different systems.
+1 I can and will implement a dedicated role abstract class to help role developers, with an apply() and undo() methods, but the _rollbacks_ mechanism would be built into the core.
