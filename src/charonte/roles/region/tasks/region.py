from io import StringIO
from pyinfra.operations import server, files
import sys
import re
from pyinfra.facts.server import Command
from omegaconf import OmegaConf
from pyinfra.api.operation import add_op

def setTimezone(state, timezone, ntp):
    if timezone:
        add_op(
            state,
            server.shell,
            name=f"Set timezone to {timezone}",
            commands=f"timedatectl set-timezone {timezone}",
            _sudo=True
        )
    if ntp:
        add_op(
            state,
            server.shell,
            name="Enable NTP",
            commands=["timedatectl set-ntp true"],
        )

def setLocales(state, locales, host):
    if not locales:
        return

    originalContent = host.get_fact(Command, "cat /etc/locale.gen", _sudo=True)
    if originalContent is None:
        print("WARNING: Could not read /etc/locale.gen. Skipping...")
        return

    modifiedContent = originalContent
    changesMade = False

    for locale in locales:
        desiredLine = f"{locale} UTF-8"
        regex = re.compile(rf"^\s*#?\s*{re.escape(locale)}\s+UTF-8.*$", re.MULTILINE)

        if re.search(rf"^\s*{re.escape(desiredLine)}.*$", modifiedContent, re.MULTILINE):
            continue

        newContent, num_subs = regex.subn(desiredLine, modifiedContent)

        if num_subs > 0:
            modifiedContent = newContent
        else:
            modifiedContent += f"\n{desiredLine}"

    if modifiedContent != originalContent:
        add_op(
            state,
            files.put,
            name="Update /etc/locale.gen with desired locales",
            src=StringIO(modifiedContent),
            dest="/etc/locale.gen",
            _sudo=True,
        )
        add_op(
            state,
            server.shell,
            name="Regenerate locales",
            commands="locale-gen",
            _sudo=True
        )

def setDefaults(state, locales, keymap):
    if locales:
        add_op(
            state,
            files.put,
            name=f"Set default locale as {locales[0]}",
            src=StringIO(f"LANG={locales[0]}\n"),
            dest="/etc/locale.conf",
            _sudo=True,
            mode="0644"
        )
    if keymap:
        add_op(
            state,
            files.put,
            name=f"Set default keymap as {keymap}",
            src=StringIO(f"KEYMAP={keymap}\n"),
            dest="/etc/vconsole.conf",
            _sudo=True,
            mode="0644"
        )

def run_region_logic(state, host, chobolo_path, skip):
    try:
        ChObolo = OmegaConf.load(chobolo_path)
        region = ChObolo.get('region')
        locales = region.get('locale')
        keymap = region.get('keymap')
        timezone = region.get('timezone')
        ntp = region.get('ntp')
    except AttributeError as e:
        print(f"{e} You've probably not set an region block in your chobolo")
        sys.exit(0)

    print("\n--- Declared state ---")
    if locales:
        print(f"locales: {locales}")
    if keymap:
        print(f"keymap: {keymap}")
    if timezone:
        print(f"timezone: {timezone}")
    if locales or timezone or keymap or ntp:
        confirm = "y" if skip else input("\nIs This correct (Y/n)? ")
        if confirm.lower() in ["y", "yes", "", "s", "sim"]:
            if timezone or ntp:
                setTimezone(state, timezone, ntp)
            if locales:
                setLocales(state, locales, host)
            if keymap or locales:
                setDefaults(state, locales, keymap)
    else:
        print("Nothing to be done.")
