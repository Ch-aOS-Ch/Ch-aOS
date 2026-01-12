# Writting pyinfra successors for Ch-aronte

## TLDR:
`State`: Pyinfra session where all of your op's go.

`op`: Declarative operations from pyinfra.

`add_op()`: `op` pile made to be ran with `run_ops()`

Why?: Cause pyinfra is significantly faster than ansible, and it allows for the use of python's ecosystem.

USE THE PYINFRA API, _NOT_ THE BINARY.

----


## Why?
Well, I _do_ have all of the systems working, why change this?

Simple: Cause ansible is slow. Pyinfra is fast as hell, and it allows for the use of python's ecosystem picture an "Ch-obolo" schema meant to verify if the Ch-obolo is valid before running the systems, _this_ is why I'm making this switch.

Also, nix is not just a config file with a lot of semantics, it's a _programming_ language, with this system, I can show people _how_ to use something like OmegaConf to generate valid Ch-obolos, then validate it manually, then validate it automatically, just like nix, but with a middle portion meant to show people the "what" their system is going to become.

---

## First of all:
The docs. The documentation for Pyinfra is not the best when regarding API mode, therefore I'm going to do the best of my efforts to explain what everything does and how the things should be setup, ok? ok.

First of all: what is this?
```py
from pyinfra.api import State, Config, Inventory
from pyinfra.api.connect import connect_all, disconnect_all
from pyinfra.api.state import StateStage
from pyinfra.context import ctx_state
```

These are pyinfra modules, they serve as normal modules, but they are very sparse and work weirdly because of--

## Secondly:
Pyinfra is not just an api, it is also a binary akin to python, this means they have a very big system setup to serve both of these, however they use the same language, so you can technically just import the wrong modules and python won't even notice.

## Thirdly: Connection? In my localhost based code?
```py
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
hosts = ["@local"] # <~ this can be ["host1.net", "10.0.0.30100", "@local"] or even a combination of tools
                   # picture: hosts=ChObolo.hosts if ChObolo.hosts else ["@local"] for fleet management. For now, let's stick to ["@local"].
inventory = Inventory((hosts, {{}}))
config = Config()
state = State(inventory, config)
state.current_stage = StateStage.Prepare # <~ btw, this is necessary, this project will not use SS.Deploy nor SS.Cleanup*, 
                                         # these serve to not need to use run_ops(),
                                         # we'll not use them since those are implicit and,
                                         # for debugging and better maintenance, let's stick to add_op() + run_ops()
ctx_state.set(state)

print("Connecting to localhost...")
connect_all(state)
host = state.inventory.get_host("@local")
print("Connection established.")
```

Yeah, remember when I said it's not just an API, but a binary as well? Yeah, this is why this is an issue in this case.

You see, since pyinfra is an ansible alternative, they need to have a way to connect to your pc and/or to other pcs, this is how they do it.

For this project, you'll probably see it just this once, but it is important to note it, since you'll need to use the state and host in the roles.

Oh yeah, forgot to mention. I use the API, _NOT_ the binary. Using the API opens up _all_ of python's systems and modules to be used, with the binary, I'd lose a lot of good (and native) imports.

We only use `ctx_state.set(state)` once at startup. Avoid relying on global context inside roles, always pass `state` explicitly to keep roles deterministic and reusable as a library.

> [!TIP] StateStages Quick mental notes:
> - `Prepare`: collect & queue operations (what we use)
> - `Deploy`: execute operations automatically without calling `run_ops()`
> - `Cleanup`: post-deploy hooks

We stick to `Prepare` + manual `run_ops()` to keep execution explicit, maintainable, and easier to debug.

## Fourthly: How to create the modules?

Well, It's a list
1. first you need to state the state of the state like so:
    ```py
    state.current_stage = StateStage.Prepare
    ```
    but of course I've already took care of that for you

2. About these weird... Things
   ```py
   if toAddNative:
    add_op(
        state,
        pacman.packages,
        name="Installing packages",
        packages=toAddNative,
        present=True,
        update=True,
        _sudo=True
    )
    # you can stick a run_ops() over here, but it's not necessary, since it just adds another thing to be ran
   if toRemoveNative:
    add_op(
        state,
        pacman.packages,
        name="Uninstalling packages",
        packages=toRemoveNative,
        present=False,
        update=True,
        _sudo=True
    )
   run_ops(state) # <~ better positioning for this context, if the context requires it, use run_ops() inside the if block
   ```

   Ok, let's be thorough about this.

   Pyinfra uses "Piles" (officially called "pending operations") to manage the state, you want to use `add_op()` to declare how and what the state should be. Thankfully, these adds are very intelligent, only passing what they need when they need it. For instance, I used pacman.packages, so the add knew what I meant by `packages`, `present` and `update`. `Name`s are universal, `state`s should always be declared and be the one passed by `main.py`.

   Oh, but we're not finished yet, cause you see that `_sudo` right there? Yeah, all things that start with _ are universal as well, you can just slap one of these badboys in any `op` (which means operation) and it'll work as the doc suggests.

   And finally, `run_ops()`, this is the _most_ important part of the system, you _need_ this to say "hey, pyinfra, I'm done adding things to the pile, make the state I passed to you match the state I declared", and it'll do it.

   Important notes: you can (and, IMO, should) _not_ use `_sudo_password` with `_sudo`, the first one declares what's going to be the password used by sudo, the second one only appends an big ol' "sudo" before any commands, when used together, sudo will know what to use, however, when using only `_sudo`, the system will automatically ask for the password, it's kinda neat, since it uses the native sudo security measures.

    Note that run_ops should not ever be called inside of your roles, Ch-aOS takes care of calling it after all roles have been processed. This keeps execution predictable and easier to manage (such is the case for `-d`).

## Fifthly: OmegaConf
I use omegaconf as the thing that helps me parse the used Ch-obolo, it's very useful, you can simply do
```py
ChObolo = OmegaConf.load(ChOboloPath)
```
And every single one of your variables will be inside of `ChObolo`, so basically, you can simply do `ChObolo.users[0].shell` and get the shell of the first listed user, VERY handy whence I start remaking the scripts, since it can also just create the Ch-obolo itself, and also when I start making examples and comparing them to some `configurations.nix`'s.

## finally
So, these are my findings as of right now about this system, it IS a pain to use at first glance, but whence you understand how the thing actually works, it gets easier, also, it IS leagues faster than ansible, which is BIG.

# Creating your own Pyinfra Role
Here's a quick guide to get you started on creating a new role for Ch-aronte.

1.  **Create the File Structure:** Create your directory and Python file following the pattern: `roles/your_role/tasks/your_role.py`.

2.  **Define the Entry Point:** In your new file, create the main function that will be called by `main.py`. It must accept `state`, `host`, `skip`, and `chobolo_path` as arguments.
    ```python
    def run_your_role(state: State, host: Host, chobolo_path: str, skip: bool) -> None:
        # Your logic goes here
        print("Executing your_role!")
    ```

3.  **Implement Your Logic:** Use `add_op` and `run_ops` to execute your operations. Import any necessary `pyinfra.operations` at the top of your file.

4.  **Integrate with `main.py`:**
    *   Place an entry_point inside of pyproject.toml:
        ```toml
        [project.entry-points."chaos.roles"]
        your_role = "roles.your_role.tasks.your_role:run_your_role"
        ```

    *   You can also create aliases for your tags in the `chaos.aliases` ep, it should map directly to the dispatcher variable.:
        ```toml
        [project.entry-points."chaos.aliases"]
        yrrl = "your_role"
        ```

    *   Install your role in your environment:
      ```bash
      uv build && cp dist/your_role-0.1.0-py3-none-any.whl ~/.local/share/chaos/plugins && chaos -u # to update the cached plugins
      ```

## Minimal Example: A 'touch' Role
Here is a complete, minimal example of a role that creates a directory in `/tmp/`.

**File: `roles/touch/tasks/touch.py`**
```python
#!/usr/bin/env python3
from pyinfra.operations import server
from pyinfra.api.operation import add_op
from pyinfra.api.operations import run_ops

# Note: We don't need OmegaConf if the role doesn't read the Ch-obolo file.

def run_touch_role(state, host, chobolo_path, skip):
                                            # <~ add skip if your role has inputs, they should be skipped if skip = True
  """
  Ensures the directory /tmp/ch-aronte-test exists.
  """
  add_op(
      state,
      server.dir,
      name="Ensure /tmp/ch-aronte-test directory exists",
      path="/tmp/ch-aronte-test",
      present=True,
      _sudo=True # Use sudo if necessary, pyinfra will _APPEND_ sudo to the start of the command,
                 # so if the command _already_ uses sudo internally, you should NOT use this,
                 # command's sudo prompt will already be passed to the user for example,
                 # you should never run "sudo yay", since yay uses sudo internally,
                 # the prompt yay uses _will_ be passed no matter what using pyinfra
  )
```

## Real usage example:
**file**: roles/pkgs/tasks/pkgs.py
```py
#!/usr/bin/env python3
from omegaconf import OmegaConf

from pyinfra.api.operation import add_op
from pyinfra.api.operations import run_ops
from pyinfra.operations import server, pacman
from pyinfra.facts.server import Command

def pkgLogic(host, chobolo_path):
    """Get the packages delta"""
    ChObolo = OmegaConf.load(chobolo_path)
    aur_helper = ChObolo.aur_helpers[0] if ChObolo.aur_helpers else None

    basePkgs = list(ChObolo.pacotes + ChObolo.pacotes_base_override + [user.shell for user in ChObolo.users if 'shell' in user])
    if aur_helper:
        basePkgs.append(aur_helper)

    root_partition = next((p for p in ChObolo.particoes.partitions if p.get('important') == 'root'), None)
    if root_partition and root_partition.type=="btrfs":
        basePkgs.append("btrfs-progs")

    boot_partition = next((p for p in ChObolo.particoes.partitions if p.get('important') == 'boot'), None)
    if boot_partition:
        basePkgs.append("dosfstools")

    if ChObolo.firmware=="UEFI" and ChObolo.bootloader=="grub":
        basePkgs.append("efibootmgr")

    if ChObolo.bootloader:
        basePkgs.append(ChObolo.bootloader)
    else:
        basePkgs.append("grub")

    wntNotNatPkgs = ChObolo.aur_pkgs

    native = host.get_fact(Command, "pacman -Qqen").strip().splitlines()
    dependencies = host.get_fact(Command, "pacman -Qqdn").strip().splitlines()
    aur = host.get_fact(Command, "pacman -Qqem").strip().splitlines()
    aurDependencies= host.get_fact(Command, "pacman -Qqdm").strip().splitlines()

    toRemoveNative = sorted(set(native) - set(basePkgs))
    toRemoveAur = sorted(set(aur) - set(wntNotNatPkgs))

    toAddNative = sorted(set(basePkgs) - set(native) - set(dependencies))
    toAddAur = sorted(set(wntNotNatPkgs) - set(aur) - set(aurDependencies))

    return toAddNative, toRemoveNative, toAddAur, toRemoveAur, aur_helper

def nativeLogic(state, toAddNative, toRemoveNative, skip, dry):
    """Applies changes to Native packages"""
    if toAddNative or toRemoveNative:
        print("--- Native packages to be removed: ---")
        for pkg in toRemoveNative:
            print(pkg)

        print("\n--- Native packages to Add: ---")
        for pkg in toAddNative:
            print(pkg)

        confirm = "y" if skip else input("Is This correct (Y/n)? ")
        if confirm.lower() in ["y", "yes", "", "s", "sim"]:
            print("\nInitiating Native package management...")
            if toAddNative:
                add_op(
                    state,
                    pacman.packages,
                    name="Installing packages",
                    packages=toAddNative,
                    present=True,
                    update=True,
                    _sudo=True
                )
            if toRemoveNative:
                add_op(
                    state,
                    pacman.packages,
                    name="Uninstalling packages",
                    packages=toRemoveNative,
                    present=False,
                    update=True,
                    _sudo=True
                )
    else:
        print("No native packages to be managed.")

def aurLogic(state, toAddAur, toRemoveAur, aur_helper, skip, dry):
    """Applies AUR changes"""
    aur_work_to_do = toAddAur or toRemoveAur

    print("\nInitiating AUR package management...")
    if aur_work_to_do and aur_helper:
        print("\n--- AUR packages to Remove: ---")
        for pkg in toRemoveAur:
            print(pkg)

        print("\n--- AUR packages to Add: ---")
        for pkg in toAddAur:
            print(pkg)

        confirmAur = "y" if skip else input("Is This correct (Y/n)? ")
        if confirmAur.lower() in ["y", "yes", "", "s", "sim"]:
            if toAddAur:
                packagesStr = " ".join(toAddAur)
                fullCommand = f"{aur_helper} -S --noconfirm --answerdiff None --answerclean All --removemake {packagesStr}"
                add_op(
                    state,
                    server.shell,
                    commands=[fullCommand],
                    name="Instaling AUR packages.",
                )
            if toRemoveAur:
                packagesRmvStr = " ".join(toRemoveAur)
                fullRemoveCommand = f"{aur_helper} -Rns --noconfirm {packagesRmvStr}"
                add_op(
                    state,
                    server.shell,
                    commands=[fullRemoveCommand],
                    name="Uninstalling AUR packages.",
                )
    elif aur_work_to_do and not aur_helper:
        print("\nThere ARE aur packages to be managed, but you still don't have an AUR helper.\n run python3 main.py aur -e path/to/ch-obolo to manage your aur helpers.")
    else:
        print("\nNo AUR packages to be managed.")

def run_all_pkg_logic(state, host, chobolo_path, skip, dry):
    """Point of entry for this role"""
    toAddNative, toRemoveNative, toAddAur, toRemoveAur, aur_helper = pkgLogic(host, chobolo_path)
    nativeLogic(state, toAddNative, toRemoveNative, skip, dry)
    aurLogic(state, toAddAur, toRemoveAur, aur_helper, skip, dry)
```
