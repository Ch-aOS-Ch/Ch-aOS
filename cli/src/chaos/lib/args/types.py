from typing import Literal, Protocol, List, Optional, Tuple

class ProviderArgs(Protocol):
    provider: Optional[str]
    from_bw: Optional[Tuple[str, str]]
    from_bws: Optional[Tuple[str, str]]
    from_op: Optional[Tuple[str, str]]

class GlobalArgs(Protocol):
    target: Optional[str]
    i_know_what_im_doing: bool
    sops_file_override: Optional[str]
    secrets_file_override: Optional[str]
    sops: bool
    keys: Optional[str | List[str]]
    team: Optional[str]
    chobolo: Optional[str]
    update_plugins: bool
    tags: Optional[List[str]]
    generate_tab: bool
    edit_chobolo: bool
    command: Optional[str]
    team_commands: Optional[str]
    secrets_commands: Optional[str]
    export_commands: Optional[str]
    import_commands: Optional[str]
    ramble_commands: Optional[str]
    set_command: Optional[str]
    init_command: Optional[str]

class ApplyArgs(Protocol):
    fleet: bool
    dry: bool
    verbose: int
    v: int
    secrets: bool

class SecArgs(Protocol):
    pgp_server: Optional[str]
    key_type: Optional[Literal['age', 'gpg', 'vault']]
    type: Optional[Literal['age', 'pgp', 'vault']]
    index: Optional[int]
    item_name: Optional[str]
    item_id: Optional[str]
    project_id: Optional[str]
    fingerprints: Optional[List[str]]
    vault_addr: Optional[str]
    save_to_config: bool
    organization_id: Optional[str]
    collection_id: Optional[str]
    bw_tags: Optional[List[str]]
    op_location: Optional[str]
    op_tags: Optional[List[str]]

class RambleArgs(Protocol):
    encrypt: bool
    find_term: Optional[str]
    tag: Optional[str]
    old: Optional[str]
    new: Optional[str]
    topics: Optional[List[str]]
    details: Optional[Literal['basic', 'intermediate', 'advanced']]

class CheckArgs(Protocol):
    checks: Optional[Literal['explanations', 'roles', 'aliases']]

class SetArgs(Protocol):
    chobolo_file: Optional[str]
    secrets_file: Optional[str]
    sops_file: Optional[str]

class TeamArgs(Protocol):
    companies: Optional[List[str]]
    company: Optional[str]
    path: Optional[str]
    teams: Optional[List[str]]

class ChaosArguments(GlobalArgs, ProviderArgs, ApplyArgs, SecArgs, RambleArgs, CheckArgs, SetArgs, TeamArgs, Protocol):
    pass
