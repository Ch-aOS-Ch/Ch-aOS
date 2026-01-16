import subprocess
import argparse
import functools
import os

if "_ARGCOMPLETE" in os.environ:
    try:
        from argcomplete.completers import FilesCompleter # type: ignore
    except ImportError:
        class FilesCompleter: # type: ignore
            def __call__(self, *args, **kwargs):
                return []
else:
    class FilesCompleter:
        def __call__(self, *args, **kwargs):
            return []


from chaos.lib.utils import get_providerEps

"""
gets the argument parser for chaos
"""
class RolesCompleter:
    def __init__(self):
        self._roles = None
        self._aliases = None
        self.explain = None

    def __call__(self, prefix, **kwargs):
        if self._roles is None or self._aliases is None:
            from chaos.lib.plugDiscovery import get_plugins
            self. _roles, self._aliases, _, _, _ = get_plugins()

        all_comps = list(self._roles.keys()) + list(self._aliases.keys())
        return [comp for comp in all_comps if comp.startswith(prefix)]

class ExplainCompleter:
    def __init__(self):
        self._topics = None
    def __call__(self, prefix, **kwargs):
        if self._topics is None:
            from chaos.lib.plugDiscovery import get_plugins
            _, _, self._topics, _, _ = get_plugins()

        all_comps = list(self._topics.keys())
        return [comp for comp in all_comps if comp.startswith(prefix)]


import functools

@functools.lru_cache(maxsize=None)
def get_loaded_providers():
    providerEps = get_providerEps()
    loaded_providers = []
    if not providerEps:
        return loaded_providers
    try:
        for ep in providerEps:
            provider = ep.load()
            loaded_providers.append(provider)
    except ImportError as e:
        print(f"Error loading provider entry points: {e}")
    return loaded_providers

def add_provider_args(parser):
    """Adds the standard provider arguments to a given parser."""
    providers = get_loaded_providers()
    if not providers:
        return

    provider_group = parser.add_mutually_exclusive_group()
    provider_group.add_argument('-p', '--provider', nargs='?', const='default', default=None, help="Use a configured provider for decryption. If no name is given, uses the default provider.")
    for provider in providers:
        provider.register_flags(provider_group)

def add_provider_export_subcommands(subparsers):
    """Adds the standard provider subparsers to a given subparsers object."""
    providers = get_loaded_providers()
    if not providers:
        return
    for provider in providers:
        providerSub = provider.register_export_subcommands(subparsers)
        providerSub.add_argument('-t', '--key-type', choices=['age', 'gpg', 'vault'], help="The type of key you want to export.")
        providerSub.add_argument('-N', '--no-import', action='store_true', help="Add a check to incapacitate importing of secrets.")
        providerSub.add_argument('-n', '--item-name', help="Name of the item to export the key.")
        providerSub.add_argument('-k', '--keys', help="Path to the key file to be exported (required for age and vault keys, needs to contain all keys.).").completer = FilesCompleter() # type: ignore
        providerSub.add_argument('-a', '--vault-addr', help="Vault address where the token is used (required for vault keys).")
        providerSub.add_argument('-f', '--fingerprints', nargs="+", help="GPG Fingerprint to be exported (required for gpg keys).")
        providerSub.add_argument('-s', '--save-to-config', action='store_true', help="Save the project ID to the chaos config file.")

def add_provider_import_subcommands(subparsers):
    """Adds the standard provider subparsers to a given subparsers object."""
    providers = get_loaded_providers()
    if not providers:
        return
    for provider in providers:
        providerSub = provider.register_import_subcommands(subparsers)
        providerSub.add_argument('-t', '--key-type', choices=['age', 'gpg', 'vault'], help="The type of key you want to import.")
        providerSub.add_argument('-i', '--item-id', help="The item ID/URL to import the key from.")

"""
creates the argument parser for chaos

KEEP THIS BIG, IT SHOULD BE LIKE THIS, SINCE DELETING A FUNCTIONALITY NEEDS TO BE EASY.
"""
def argParsing():
    parser = argparse.ArgumentParser(
        description="chaos system manager.",
    )

    parser.add_argument('-c', dest="chobolo", help="Path to Ch-obolo to be used (overrides all calls).").completer = FilesCompleter() # type: ignore
    parser.add_argument('-u', '--update-plugins', action='store_true', help="Force update of the plugin cache.")
    parser.add_argument('-t', '--generate-tab', action='store_true', help="Generate shell tab-completion script.")
    parser.add_argument('-ec', '--edit-chobolo', action='store_true', help="Edit the Ch-obolo file using the default editor.")

    return parser

def addSecParsers(parser):
    secParser = parser.add_parser('secrets', help="Manage your secrets.")
    secSubParser = secParser.add_subparsers(dest="secrets_commands", help="Secret subcommands", required=True)

    secExport = secSubParser.add_parser('export', help="Export keys to a Password Manager.")
    secSubExport = secExport.add_subparsers(dest='export_commands', help="Secret export subcommands", required=True)
    add_provider_export_subcommands(secSubExport)

    secImport = secSubParser.add_parser('import', help="Import keys from a Password Manager.")
    secSubImport = secImport.add_subparsers(dest='import_commands', help="Secret import subcommands", required=True)
    add_provider_import_subcommands(secSubImport)

    secRotateAdd = secSubParser.add_parser('rotate-add', help="Add new keys to your secrets.")
    secRotateAdd.add_argument('type', choices=['age', 'pgp', 'vault'], help="The type of key you want to add")
    secRotateAdd.add_argument('keys', nargs="+", help="Keys to be added.")
    secRotateAdd.add_argument('-i', '--index', type=int, help="Rule index to be used.")
    secRotateAdd.add_argument('-cr', '--create', action='store_true', help="If you want to create a new key group or not.")
    secRotateAdd.add_argument('-ikwid', '-u', '--i-know-what-im-doing', action='store_true', help="Update all shares directly.")
    secRotateAdd.add_argument('-s', '--pgp-server', dest="pgp_server", help="Server to import GPG keys.")
    secRotateAdd.add_argument('-ss', '--sops-file', dest='sops_file_override', help="Path to the .sops.yaml config file (overrides all calls).").completer = FilesCompleter() # type: ignore
    secRotateAdd.add_argument('-t', '--team', type=str, help="Team to be used, in the format company.team.group")
    add_provider_args(secRotateAdd)

    secRotateRemove = secSubParser.add_parser('rotate-rm', help="Remove keys from your secrets.")
    secRotateRemove.add_argument('type', choices=['age', 'pgp', 'vault'], help="The type of key you want to remove.")
    secRotateRemove.add_argument('keys', nargs="+", help="Keys to be removed.")
    secRotateRemove.add_argument('-i', '--index', type=int, help="Rule index to be used.")
    secRotateRemove.add_argument('-ss', '--sops-file', dest='sops_file_override', help="Path to the .sops.yaml config file (overrides all calls).").completer = FilesCompleter() # type: ignore
    secRotateRemove.add_argument('-t', '--team', type=str, help="Team to be used, in the format company.team.group")
    secRotateRemove.add_argument('-ikwid', '-u', '--i-know-what-im-doing', action='store_true', help="Update all shares directly.")
    add_provider_args(secRotateRemove)

    secList = secSubParser.add_parser('list',  help="Show all keys inside your sops configuration.")
    secList.add_argument('type', choices=['age', 'pgp', 'vault'], help="The type of key you want to list.")
    secList.add_argument('-ss', '--sops-file', dest='sops_file_override', help="Path to the .sops.yaml config file (overrides all calls).").completer = FilesCompleter() # type: ignore
    secList.add_argument('-t', '--team', type=str, help="Team to be used, in the format company.team.group")

    secEdit = secSubParser.add_parser('edit', help="Edit your secrets file.")
    secEdit.add_argument('-t', '--team', type=str, help="Team to be used, in the format company.team.group")
    secEdit.add_argument('-s', '--sops', help="Edit the sops file instead of the secrets file.", action='store_true')
    secEdit.add_argument('-ss', '--sops-file', dest='sops_file_override', help="Path to the .sops.yaml config file (overrides all calls).").completer = FilesCompleter() # type: ignore
    secEdit.add_argument('-sf', '--secrets-file', dest='secrets_file_override', help="Path to the sops-encrypted secrets file (overrides all calls).").completer = FilesCompleter() # type: ignore
    add_provider_args(secEdit)

    secPrint = secSubParser.add_parser('print', help="Print your secrets to the screen. Be careful where you use this.")
    secPrint.add_argument('-t', '--team', type=str, help="Team to be used (company.team.group). If you have a team repository, you may check your team secrets on it.")
    secPrint.add_argument('-s', '--sops', help="Print the sops file instead of the secrets file.", action='store_true')
    secPrint.add_argument('-sf', dest='secrets_file_override', help="Path to the sops-encrypted secrets file (overrides all calls).").completer = FilesCompleter() # type: ignore
    secPrint.add_argument('-ss', dest='sops_file_override', help="Path to the .sops.yaml config file (overrides all calls).").completer = FilesCompleter() # type: ignore
    add_provider_args(secPrint)

    secCat = secSubParser.add_parser("cat", help="Get the specified keys inside of your secrets file, nested or not.")
    secCat.add_argument("keys", nargs="+", help="The keys to be cat-ed.")
    secCat.add_argument('-t', '--team', type=str, help="Team to be used (company.team.group). If you have a team repository, you may check your team secrets on it.")
    secCat.add_argument('-s', '--sops', help="Print the sops file instead of the secrets file.", action='store_true')
    secCat.add_argument('-sf', dest='secrets_file_override', help="Path to the sops-encrypted secrets file (overrides all calls).").completer = FilesCompleter() # type: ignore
    secCat.add_argument('-ss', dest='sops_file_override', help="Path to the .sops.yaml config file (overrides all calls).").completer = FilesCompleter() # type: ignore
    secCat.add_argument('-j', '--json', action="store_true", help="Make the output be JSON")
    add_provider_args(secCat)

    secShamir = secSubParser.add_parser('set-shamir', help="Manage Shamir's Secret Sharing configuration.")
    secShamir.add_argument('index', type=int, help="Rule index to be used.")
    secShamir.add_argument('share', type=int, help="Amount of Shares to be obligatory.")
    secShamir.add_argument('-ss', '--sops-file', dest='sops_file_override', help="Path to the .sops.yaml config file (overrides all calls).").completer = FilesCompleter() # type: ignore
    secShamir.add_argument('-t', '--team', type=str, help="Team to be used, in the format company.team.group")
    secShamir.add_argument('-ikwid', '-u', '--i-know-what-im-doing', action='store_true', help="Update all shares directly.")
    add_provider_args(secShamir)


def addRambleParsers(parser):
    rambleParser = parser.add_parser('ramble', help="Annotate your rambles!")

    rambSubParser = rambleParser.add_subparsers(dest="ramble_commands", help="Ramble subcommands", required=True)
    rambleCreate = rambSubParser.add_parser('create', help='Create a new ramble or a rambling inside a ramble.')
    rambleCreate.add_argument('target', help='The ramble/rambling to create (e.g., ramble.rambling)')
    rambleCreate.add_argument('-t', '--team', type=str, help="Team to be used, in the format company.team.person")
    rambleCreate.add_argument('-e', '--encrypt', action='store_true', help='Encrypt the rambling upon creation.')
    rambleCreate.add_argument('-k', '--keys', nargs='+', help='Encrypt keys in a granular way')
    rambleCreate.add_argument('-ss', '--sops-file', dest='sops_file_override', help="Path to the .sops.yaml config file (overrides all calls).").completer = FilesCompleter() # type: ignore

    rambleEdit = rambSubParser.add_parser('edit', help='Edit a rambling directly, whether encrypted or not.')
    rambleEdit.add_argument('target', help='The rambling you want to edit (e.g., ramble.rambling)')
    rambleEdit.add_argument('-s', '--sops', help="Edit the sops file instead of the ramble file.", action='store_true')
    rambleEdit.add_argument('-ss', '--sops-file', dest='sops_file_override', help="Path to the .sops.yaml config file (overrides all calls).").completer = FilesCompleter() # type: ignore
    rambleEdit.add_argument('-t', '--team', type=str, help="Team to be used, in the format company.team.person")
    add_provider_args(rambleEdit)

    rambleEncrypt = rambSubParser.add_parser('encrypt', help='Encrypt a rambling inside a ramble with sops.')
    rambleEncrypt.add_argument('target', help='The rambling you want to encrypt (e.g., ramble.rambling)')
    rambleEncrypt.add_argument('-k', '--keys', nargs='+', help='Encrypt keys in a granular way')
    rambleEncrypt.add_argument('-ss', '--sops-file', dest='sops_file_override', help="Path to the .sops.yaml config file (overrides all calls).").completer = FilesCompleter() # type: ignore
    rambleEncrypt.add_argument('-t', '--team', type=str, help="Team to be used, in the format company.team.person")
    add_provider_args(rambleEncrypt)

    rambleRead = rambSubParser.add_parser('read', help='Read your ramblings.')
    rambleRead.add_argument('targets', nargs='+', help='The ramble(s)/rambling(s) to read. Use ramble.list to list ramblings inside a ramble and ramble.rambling to read a rambling.')
    rambleRead.add_argument('-ss', '--sops-file', dest='sops_file_override', help="Path to the .sops.yaml config file (overrides all calls).").completer = FilesCompleter() # type: ignore
    rambleRead.add_argument('-t', '--team', type=str, help="Team to be used, in the format company.team.person")
    add_provider_args(rambleRead)

    rambleFind = rambSubParser.add_parser('find', help='Find rambles by keyword or tag.')
    rambleFind.add_argument('find_term', nargs='?', default=None, help='A keyword to search for in your rambles.')
    rambleFind.add_argument('--tag', help='Filter rambles by a specific tag.')
    rambleFind.add_argument('-t', '--team', type=str, help="Team to be used, in the format company.team.person")
    rambleFind.add_argument('-ss', '--sops-file', dest='sops_file_override', help="Path to the .sops.yaml config file (overrides all calls).").completer = FilesCompleter() # type: ignore

    rambleMove = rambSubParser.add_parser('move', help='Move a rambling through rambles')
    rambleMove.add_argument('old', help='Your old rambling')
    rambleMove.add_argument('new', help='Your new rambling')
    rambleMove.add_argument('-t', '--team', type=str, help="Team to be used, in the format company.team.person")

    rambleUpdate = rambSubParser.add_parser('update', help='Update your rambling encryption keys, great for rotation!')
    rambleUpdate.add_argument('-ss', '--sops-file', dest='sops_file_override', help="Path to the .sops.yaml config file (overrides all calls).").completer = FilesCompleter() # type: ignore
    rambleUpdate.add_argument('-t', '--team', type=str, help="Team to be used, in the format company.team.person")
    add_provider_args(rambleUpdate)

    rambleDel = rambSubParser.add_parser('delete', help='Delete a rambling or an entire ramble.')
    rambleDel.add_argument('ramble', help='Your ramble')
    rambleDel.add_argument('-t', '--team', type=str, help="Team to be used, in the format company.team.person")

def addExplainParsers(parser):
    expParser = parser.add_parser('explain', help="Explain a role topic or subtopic.")

    topics = expParser.add_argument('topics', nargs="+", help="Topic(s) to be explained. Use topic.list to list topics and topic.subtopic to read a subtopic")
    expParser.add_argument('-d', '--details', choices=['basic', 'intermediate', 'advanced'], default='basic', help="Level of detail for the explanation.")
    expParser.add_argument('-c', '--complexity', type=str, choices=['basic', 'intermediate', 'advanced'], default='basic', help="Level of complexity for the explanation.")
    topics.completer = ExplainCompleter() # type: ignore

def addCheckParsers(parser):
    checkParser = parser.add_parser('check', help='Check and list roles, aliases and explanations')

    checkParser.add_argument('checks', choices=['explanations', 'roles', 'aliases'], help='The operations you want to check.')
    checkParser.add_argument('-c', dest="chobolo", help="Path to Ch-obolo to be used (overrides all calls).").completer = FilesCompleter() # type: ignore

def addSetParsers(parser):
    setParser = parser.add_parser('set', help='Set configuration files')
    setSubParser = setParser.add_subparsers(dest="set_command")

    chParser = setSubParser.add_parser('chobolo', aliases=['c', 'ch'], help="Set default chobolo file")
    chParser.add_argument('chobolo_file', help="Chobolo file path")

    secParser = setSubParser.add_parser('secrets', aliases=['sec', 'se'], help="Set default secrets file")
    secParser.add_argument('secrets_file', help="Secrets file path")

    sopsParser = setSubParser.add_parser('sops', aliases=['sop'], help="Set default sops file")
    sopsParser.add_argument('sops_file', help="Sops file path")

def addApplyParsers(parser):
    applyParser = parser.add_parser('apply', help="Apply an available role")

    tags = applyParser.add_argument('tags', nargs='+', help="The tag(s) for the role(s) to be executed.")
    applyParser.add_argument('-f', '--fleet', action='store_true', help="Apply to a fleet of hosts defined in the Ch-obolo file.")
    applyParser.add_argument('-d', '--dry', action='store_true', help="Execute roles in dry mode.")
    applyParser.add_argument('-v', action='count', default=0, help="Increase verbosity level.")
    applyParser.add_argument('--verbose', type=int, choices=[1, 2, 3], help="Set log level directly.")
    applyParser.add_argument('-c', dest="chobolo", help="Path to Ch-obolo to be used (overrides all calls).").completer = FilesCompleter() # type: ignore
    applyParser.add_argument('-s', '--secrets', action='store_true', help="Signal that a secret-having role is being used and decryption is needed.")
    applyParser.add_argument('-sf', '--secrets-file', dest='secrets_file_override', help="Path to the sops-encrypted secrets file (overrides all calls).").completer = FilesCompleter() # type: ignore
    applyParser.add_argument('-ss', '--sops-file', dest='sops_file_override', help="Path to the .sops.yaml config file (overrides all calls).").completer = FilesCompleter() # type: ignore
    applyParser.add_argument('-t', '--team', type=str, help="Team to be used, in the format company.team.group")
    applyParser.add_argument('-ikwid', '-y', '--i-know-what-im-doing', action='store_true', help="Skips all confirmations for role execution.")
    tags.completer = RolesCompleter() # type: ignore
    add_provider_args(applyParser)

def addTeamParsers(parser):
    teamParser = parser.add_parser('team', help="Manage your teams.")
    teamSubParser = teamParser.add_subparsers(dest="team_commands", help="Team management commands", required=True)

    teamPrune = teamSubParser.add_parser('prune', help="Prune unused teams from your configuration.")
    teamPrune.add_argument('-ikwid', '-y', '--i-know-what-im-doing', action='store_true', help="Skips all confirmations.")
    teamPrune.add_argument('companies', help="Companies to prune teams from, if not passed, will prune all companies.", nargs='*')

    listTeams = teamSubParser.add_parser('list', help="List all available teams.")
    listTeams.add_argument('company', nargs='?', help="Company to filter teams, if not passed, will list all companies.")

    # TODO: teamPersonParser = teamSubParser.add_parser('person-add', help="Add a person to a team.")
    # TODO: teamPersonParser.add_argument('target', help="Target person in the format company.team.person")
    # TODO: teamPersonParser.add_argument('type', choices=['age', 'gpg'], help="The type of key you want to add.")
    # TODO: teamPersonParser.add_argument('keys', nargs='+', help="Keys to be added.")

    teamClone = teamSubParser.add_parser('clone', help="Clone a team repository locally.")
    teamClone.add_argument('target', help="Target team repository in the git format.")

    teamInit = teamSubParser.add_parser('init', help="Initialize a team repository in the current folder.")
    teamInit.add_argument('target', help="Target team in the format company.team.person")
    teamInit.add_argument('path', help="Path where to initialize the team repository, if no path is given, current folder is used.", nargs='?')
    teamInit.add_argument('-ikwid', '-y', '--i-know-what-im-doing', action='store_true', help="Skips all confirmations.")

    teamActivate = teamSubParser.add_parser('activate', help="Activate a cloned team.")
    teamActivate.add_argument('path', help="Path where the team repository is located.", nargs="?")

    teamDeactivate = teamSubParser.add_parser('deactivate', help="deactivate a team.")
    teamDeactivate.add_argument('company', help="Company of the team to be deactivated.")
    teamDeactivate.add_argument('teams', help="Teams to be deactivated, if not passed, will try to remove all teams.", nargs="*")

def addInitParsers(parser):
    initParser = parser.add_parser('init', help="Let Ch-aOS handle the boiler plates!")
    initSubParser = initParser.add_subparsers(dest='init_command', help='What to initialize', required=True)

    initSubParser.add_parser('chobolo', help="Initialize a boiler plate chobolo based on the plugins/core you have installed!")
    initSubParser.add_parser('secrets', help="Initialize both a secrets file and a sops file!")

"""Handles the -t/--generate-tab argument, generating the tab-completion script"""
def handleGenerateTab():
    subprocess.run(['register-python-argcomplete', 'chaos'])
