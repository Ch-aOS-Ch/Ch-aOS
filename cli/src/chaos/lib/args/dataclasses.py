from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional


@dataclass(frozen=True)
class TeamPrunePayload:
    companies: List[str]
    i_know_what_im_doing: bool


@dataclass(frozen=True)
class TeamListPayload:
    company: Optional[str]
    no_pretty: bool
    json: bool


@dataclass(frozen=True)
class TeamClonePayload:
    target: str
    path: Optional[str]


@dataclass(frozen=True)
class TeamInitPayload:
    target: str
    path: Optional[str]
    i_know_what_im_doing: bool


@dataclass(frozen=True)
class TeamActivatePayload:
    path: Optional[str]


@dataclass(frozen=True)
class TeamDeactivatePayload:
    company: str
    teams: List[str]


@dataclass(frozen=True)
class ExplainPayload:
    topics: List[str]
    no_pretty: bool
    json: bool
    details: str = "basic"
    complexity: str = "basic"


@dataclass(frozen=True)
class SetPayload:
    chobolo_file: Optional[str]
    sops_file: Optional[str]
    secrets_file: Optional[str]


@dataclass(frozen=True)
class ProviderConfigPayload:
    provider: Optional[str] = None
    ephemeral_provider_args: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SecretsContext:
    team: Optional[str] = None
    sops_file_override: Optional[str] = None
    secrets_file_override: Optional[str] = None
    provider_config: Optional[ProviderConfigPayload] = None
    i_know_what_im_doing: bool = False


@dataclass(frozen=True)
class ProviderExportArgs:
    pass


@dataclass(frozen=True)
class ProviderImportArgs:
    pass


@dataclass(frozen=True)
class SecretsExportPayload:
    provider_name: str
    key_type: Literal["age", "gpg", "vault"]
    no_import: bool
    save_to_config: bool
    item_name: Optional[str] = None
    keys: Optional[str] = None
    vault_addr: Optional[str] = None
    fingerprints: Optional[List[str]] = None
    provider_specific_args: ProviderExportArgs = field(
        default_factory=ProviderExportArgs
    )


@dataclass(frozen=True)
class SecretsImportPayload:
    provider_name: str
    key_type: Literal["age", "gpg", "vault"]
    item_id: Optional[str] = None
    provider_specific_args: ProviderImportArgs = field(
        default_factory=ProviderImportArgs
    )


@dataclass(frozen=True)
class SecretsRotatePayload:
    type: Literal["age", "pgp", "vault"]
    keys: List[str]
    context: SecretsContext
    index: Optional[int] = None
    pgp_server: Optional[str] = None
    create: bool = False


@dataclass(frozen=True)
class SecretsListPayload:
    type: Literal["age", "pgp", "vault"]
    context: SecretsContext
    no_pretty: bool = False
    json: bool = False
    value: bool = False


@dataclass(frozen=True)
class SecretsEditPayload:
    context: SecretsContext
    edit_sops_file: bool = False


@dataclass(frozen=True)
class SecretsPrintPayload:
    context: SecretsContext
    print_sops_file: bool = False
    as_json: bool = False


@dataclass(frozen=True)
class SecretsCatPayload:
    keys: List[str]
    context: SecretsContext
    cat_sops_file: bool = False
    as_json: bool = False
    value_only: bool = False


@dataclass(frozen=True)
class SecretsSetShamirPayload:
    index: int
    share: int
    context: SecretsContext