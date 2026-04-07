# Chopping Board

**Some of the future work** I plan to do on the Ch-aOS Project Suite. Feel free to contribute or suggest new features!

## (The obvious ones) Ch-iron and Ch-ronos

**Fedora and Debian based official cores** Ch-aronte is just the beginning! Official cores for other popular distributions like Fedora (Ch-iron) and Debian/Ubuntu (Ch-ronos) to expand Ch-aOS' reach and usability.

## Installation From 0 to fine-tuning

**A complete installation flow** that takes the user from a bare-metal system to a fully configured environment, including partitioning, bootloader setup, and post-install configurations, using the same declarative approach and plugin based architecture. (chaos.installer)

## Better Fleet Manaegment

!!! success "this has been implemented!"
    Check out the [docs](./Advanced/boats.md) for more information.
    Can be improved through an `--limit` flag on the CLI, for better targeting, but the main idea (expandable inventories) is already here.

**You know Ansible's dinamic inventories?** Something similar, but following Ch-aOS' design principles. A way to manage multiple systems declaratively through an plugin-based declarative inventory system, think "chaos-ec2-boat" that dinamically fetches instances from AWS EC2 and applies Ch-aOS configurations to them. (chaos.boats)

## (the big one) Ch-imera: Ch-obolo to nix mini-compilers

**NixOS is, obviously, the best declarative OS out there.** Its got atomicity, rollbacks, a MASSIVE repo, and a great community. But its language is complex, and its learning curve steep. What if we could compile Ch-aOS' Ch-obolos to Nix expressions? This would allow users to leverage NixOS' strengths while enjoying Ch-aOS' simplicity and modularity! Of course, tho, this isn't all roses, Ch-obolo generated Nix expressions would (and should) be limited, since... Well, since Ch-obolos are written in a non-Turing complete language. But still, this could be a great way to bridge the gap between the two systems, bringing a more common approach to IaC (YAML) to NixOS systems! (chaos.compilers.chimera since, if this works, we could just add a compiler for guix, for instance!)

## (New one!) Ch-aOS archipelago.

Now, now, with all of these nautical references, I couldn't just not add this one! Think about it, you have a very good way to _configure_ your system, but what about _provisioning_ it? Ch-aOS Archipelago (or just pelago) would be a tool that utilizes the same plugin-based architecture to provision new systems on the cloud, using Pulumi as the underlying provisioning engine. Instead of just provisioning it, tho, it would be able to apply Ch-aOS configurations to it as well, making it a one-command solution for going from 0 to a fully configured VM! (chaos.isles)

## (Another big task) Ch-aOS Capitain... or should I say, Ch-apetanios

**So, you know Ansible Tower and you know Puppet Master, get ready for...** Ch-aOS Ch-apetanios! A centralized server that should provide a single point of management for multiple Ch-aOS managed systems. There are a... "few" steps to achieve this, such as:

  - Job scheduling and queuing system.

  - Git-centric workflow (kinda like argocd, but for configuration management).

  - Helm charts for easy deployment on k8s + Docker images for easy deployment anywhere else.

  - Integration with the prometheus stack for metrics collection and display.

  - TUI interface for easy management and monitoring.

    - visualization of the state of managed systems.

    - logs and reports.

    - job history.

So, as you can see, this is not a small task... like, at all, but it could turn Ch-aOS into a more enterprise-ready solution for managing large fleets of systems.
Also, yeah, its going to be written in Go, since... well, its a server, and Go is great for that, plus, I want to learn Go, plus plus, its a TUI, not a web app, so... yeah.

!!! experiment "Metrics are on the table!"
    I've implemented a complete metrics collection for Ch-aOS that can be seen [here](./Advanced/logbook.md), this is a first step towards Ch-apetanios, since it provides a way to collect data from multiple systems. (Also, I had to create a pyinfra FACT for this to get system hardware info, kinda cooool huuuuh?)

## (Something I'd enjoy using) Ch-aOS Styx

!!! success "this has been implemented!"
    Check out the [docs](./Commands/styx.md) for more information.

**Ansible has Galaxy, Puppet has Forge, Chef has Supermarket, SaltStack has the SaltStack Community Repository...** Ch-aOS Styx would be an git repo with a bunch of plugin metadata and pointers, this saves me from buying a server to keep all of this info since... well, I have no money... this could integrate with chaos and make installing plugins quick n easy, plus, since it's just a bunch of metadata, I can futurally create a fully operational website to discover new plugins
