from chaos.lib.plugDiscovery import get_plugins, load_roles
import subprocess
import argparse
from argcomplete.completers import FilesCompleter

class RolesCompleter:
    def __init__(self):
        self._roles = None
        self._aliases = None
        self.explain = None

    def __call__(self, prefix, **kwargs):
        if self._roles is None or self._aliases is None or self.explain is None:
            self. _roles, self._aliases, self.explain, self.keys = get_plugins()

        all_comps = list(self._roles.keys()) + list(self._aliases.keys()) + list(self.explain.keys()) + list(self.keys.keys())
        return [comp for comp in all_comps if comp.startswith(prefix)]

def argParsing():
    parser = argparse.ArgumentParser(
        description="chaos system manager.",
    )

    parser.add_argument('-c', dest="chobolo", help="Path to Ch-obolo to be used (overrides all calls).").completer = FilesCompleter()
    parser.add_argument('-sf', dest='secrets_file_override', help="Path to the sops-encrypted secrets file (overrides all calls).").completer = FilesCompleter()
    parser.add_argument('-ss', dest='sops_file_override', help="Path to the .sops.yaml config file (overrides all calls).").completer = FilesCompleter()
    parser.add_argument('-u', '--update-plugins', action='store_true', help="Force update of the plugin cache.")
    parser.add_argument('-t', '--generate-tab', action='store_true', help="Generate shell tab-completion script.")
    parser.add_argument('-es', '--edit-sec', action='store_true', help="Edit the secrets encrypted file using sops. Do not run publicly.")
    parser.add_argument('-ec', '--edit-chobolo', action='store_true', help="Edit the Ch-obolo file using the default editor.")

    subParser = parser.add_subparsers(dest="command", help="Available subcommands")

    rambleParser = subParser.add_parser('ramble', help="Annotate your rambles!")

    secParser = subParser.add_parser('secrets', help="Manage your secrets.")

    secSubParser = secParser.add_subparsers(dest="secrets_commands", help="Secret subcommands", required=True)

    secRotateRemove = secSubParser.add_parser('rotate-rm', help="Remove PGP keys from your secrets.")
    secRotateRemove.add_argument('type', choices=['age', 'pgp', 'vault'], help="The type of key you want to remove.")
    secRotateRemove.add_argument('keys', nargs="+", help="Keys to be removed.")
    secRotateRemove.add_argument('-i', '--index', type=int, help="Rule index to be used.")
    secRotateRemove.add_argument('-ss', '--sops-file', dest='sops_file_override', help="Path to the .sops.yaml config file (overrides all calls).").completer = FilesCompleter()
    secRotateRemove.add_argument('-ikwid', '-y', '--i-know-what-im-doing', action='store_true', help="Skips all confirmations for role execution.")

    secList = secSubParser.add_parser('list',  help="Show all PGP keys inside your sops configuration.")
    secList.add_argument('type', choices=['age', 'pgp', 'vault'], help="The type of key you want to list.")
    secList.add_argument('-ss', '--sops-file', dest='sops_file_override', help="Path to the .sops.yaml config file (overrides all calls).").completer = FilesCompleter()

    secRotateAdd = secSubParser.add_parser('rotate-add', help="Add new keys to your secrets.")
    secRotateAdd.add_argument('type', choices=['age', 'pgp', 'vault'], help="The type of key you want to add")
    secRotateAdd.add_argument('keys', nargs="+", help="Keys to be added.")
    secRotateAdd.add_argument('-i', '--index', type=int, help="Rule index to be used.")
    secRotateAdd.add_argument('-cr', '--create', action='store_true', help="If you want to create a new key group or not.")
    secRotateAdd.add_argument('-ikwid', '-y', '--i-know-what-im-doing', action='store_true', help="Skips all confirmations for role execution.")
    secRotateAdd.add_argument('-s', '--pgp-server', dest="pgp_server", help="Server to import PGP keys.")
    secRotateAdd.add_argument('-ss', '--sops-file', dest='sops_file_override', help="Path to the .sops.yaml config file (overrides all calls).").completer = FilesCompleter()

    secShamir = secSubParser.add_parser('shamir', help="Manage Shamir's Secret Sharing configuration.")
    secShamir.add_argument('index', type=int, help="Rule index to be used.")
    secShamir.add_argument('share', type=int, help="Amount of Shares to be obligatory.")
    secShamir.add_argument('-ss', '--sops-file', dest='sops_file_override', help="Path to the .sops.yaml config file (overrides all calls).").completer = FilesCompleter()

    rambSubParser = rambleParser.add_subparsers(dest="ramble_commands", help="Ramble subcommands", required=True)

    rambleCreate = rambSubParser.add_parser('create', help='Create a new ramble or a rambling inside a ramble.')
    rambleCreate.add_argument('target', help='The ramble/rambling to create (e.g., ramble.rambling)')

    rambleEdit = rambSubParser.add_parser('edit', help='Edit a rambling directly, whether encrypted or not.')
    rambleEdit.add_argument('target', help='The rambling you want to edit (e.g., ramble.rambling)')
    rambleEdit.add_argument('-ss', '--sops-file', dest='sops_file_override', help="Path to the .sops.yaml config file (overrides all calls).").completer = FilesCompleter()

    rambleEncrypt = rambSubParser.add_parser('encrypt', help='Encrypt a rambling inside a ramble with sops.')
    rambleEncrypt.add_argument('target', help='The rambling you want to encrypt (e.g., ramble.rambling)')
    rambleEncrypt.add_argument('-k', '--keys', nargs='+', help='Encrypt keys in a granular way')
    rambleEncrypt.add_argument('-ss', '--sops-file', dest='sops_file_override', help="Path to the .sops.yaml config file (overrides all calls).").completer = FilesCompleter()

    rambleRead = rambSubParser.add_parser('read', help='Read your ramblings.')
    rambleRead.add_argument('targets', nargs='+', help='The ramble(s)/rambling(s) to read. Use ramble.list to list ramblings inside a ramble and ramble.rambling to read a rambling.')
    rambleRead.add_argument('-ss', '--sops-file', dest='sops_file_override', help="Path to the .sops.yaml config file (overrides all calls).").completer = FilesCompleter()

    rambleFind = rambSubParser.add_parser('find', help='Find rambles by keyword or tag.')
    rambleFind.add_argument('find_term', nargs='?', default=None, help='A keyword to search for in your rambles.')
    rambleFind.add_argument('-t', '--tag', help='Filter rambles by a specific tag.')
    rambleFind.add_argument('-ss', '--sops-file', dest='sops_file_override', help="Path to the .sops.yaml config file (overrides all calls).").completer = FilesCompleter()

    rambleMove = rambSubParser.add_parser('move', help='Move a rambling through rambles')
    rambleMove.add_argument('old', help='Your old rambling')
    rambleMove.add_argument('new', help='Your new rambling')

    rambleUpdate = rambSubParser.add_parser('update', help='Update your rambling encryption keys, great for rotation!')
    rambleUpdate.add_argument('-ss', '--sops-file', dest='sops_file_override', help="Path to the .sops.yaml config file (overrides all calls).").completer = FilesCompleter()

    rambleDel = rambSubParser.add_parser('delete', help='Delete a rambling or an entire ramble.')
    rambleDel.add_argument('ramble', help='Your ramble')

    expParser = subParser.add_parser('explain', help="Explain a role topic or subtopic.")
    expParser.add_argument('topics', nargs="+", help="Topic(s) to be explained. Use topic.list to list topics and topic.subtopic to read a subtopic")
    expParser.add_argument('-d', '--details', choices=['basic', 'intermediate', 'advanced'], default='basic', help="Level of detail for the explanation.")

    checkParser = subParser.add_parser('check', help='Check and list roles, secrets, aliases and explanations')
    checkParser.add_argument('checks', choices=['explanations', 'roles', 'secrets', 'aliases'], help='The operations you want to check.')
    checkParser.add_argument('-t', '--team', type=str, help="If you have a team repository, you may check your team secrets on it.")
    checkParser.add_argument('-c', dest="chobolo", help="Path to Ch-obolo to be used (overrides all calls).").completer = FilesCompleter()
    checkParser.add_argument('-sf', dest='secrets_file_override', help="Path to the sops-encrypted secrets file (overrides all calls).").completer = FilesCompleter()
    checkParser.add_argument('-ss', dest='sops_file_override', help="Path to the .sops.yaml config file (overrides all calls).").completer = FilesCompleter()

    setParser = subParser.add_parser('set', help='Set configuration files')
    setSubParser = setParser.add_subparsers(dest="set_command")

    chParser = setSubParser.add_parser('chobolo', aliases=['c', 'ch'], help="Set default chobolo file")
    chParser.add_argument('chobolo_file', help="Chobolo file path")

    secParser = setSubParser.add_parser('secrets', aliases=['sec', 'se'], help="Set default secrets file")
    secParser.add_argument('secrets_file', help="Secrets file path")

    sopsParser = setSubParser.add_parser('sops', aliases=['sop'], help="Set default sops file")
    sopsParser.add_argument('sops_file', help="Sops file path")

    applyParser = subParser.add_parser('apply', help="Apply an available role")
    tags = applyParser.add_argument('tags', nargs='+', help="The tag(s) for the role(s) to be executed.")

    applyParser.add_argument('-d', '--dry', action='store_true', help="Execute roles in dry mode.")
    applyParser.add_argument('-v', action='count', default=0, help="Increase verbosity level.")
    applyParser.add_argument('--verbose', type=int, choices=[1, 2, 3], help="Set log level directly.")
    applyParser.add_argument('-c', dest="chobolo", help="Path to Ch-obolo to be used (overrides all calls).").completer = FilesCompleter()
    applyParser.add_argument('-sf', '--secrets-file', dest='secrets_file_override', help="Path to the sops-encrypted secrets file (overrides all calls).").completer = FilesCompleter()
    applyParser.add_argument('-ss', '--sops-file', dest='sops_file_override', help="Path to the .sops.yaml config file (overrides all calls).").completer = FilesCompleter()
    applyParser.add_argument('-ikwid', '-y', '--i-know-what-im-doing', action='store_true', help="Skips all confirmations for role execution.")

    initParser = subParser.add_parser('init', help="Let Ch-aOS handle the boiler plates!")

    initSubParser = initParser.add_subparsers(dest='init_command', required=True, help='What to initialize')
    initSubParser.add_parser('chobolo', help="Initialize a boiler plate chobolo based on the plugins/core you have installed!")
    initSubParser.add_parser('secrets', help="Initialize both a secrets file and a sops file!")

    tags.completer = RolesCompleter()

    return parser

def handleGenerateTab():
    subprocess.run(['register-python-argcomplete', 'chaos'])
