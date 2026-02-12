from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass(frozen=True, slots=True)
class TeamPrunePayload:
    companies: list[str]
    i_know_what_im_doing: bool


@dataclass(frozen=True, slots=True)
class TeamListPayload:
    company: str | None
    no_pretty: bool
    json: bool


@dataclass(frozen=True, slots=True)
class TeamClonePayload:
    target: str
    path: str | None


@dataclass(frozen=True, slots=True)
class TeamInitPayload:
    target: str
    path: str | None
    i_know_what_im_doing: bool


@dataclass(frozen=True, slots=True)
class TeamActivatePayload:
    path: str | None


@dataclass(frozen=True, slots=True)
class TeamDeactivatePayload:
    company: str
    teams: list[str]


@dataclass(frozen=True, slots=True)
class ExplainPayload:
    topics: list[str]
    no_pretty: bool
    json: bool
    details: str = "basic"
    complexity: str = "basic"


@dataclass(frozen=True, slots=True)
class SetPayload:
    chobolo_file: str | None
    sops_file: str | None
    secrets_file: str | None


@dataclass(frozen=True, slots=True)
class ProviderConfigPayload:
    provider: str | None = None
    ephemeral_provider_args: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class SecretsContext:
    team: str | None = None
    sops_file_override: str | None = None
    secrets_file_override: str | None = None
    provider_config: ProviderConfigPayload | None = None
    i_know_what_im_doing: bool = False


@dataclass(frozen=True, slots=True)
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
    item_name: str | None = None
    keys: str | None = None
    vault_addr: str | None = None
    fingerprints: list[str] | None = None
    provider_specific_args: ProviderExportArgs = field(
        default_factory=ProviderExportArgs
    )


@dataclass(frozen=True)
class SecretsImportPayload:
    provider_name: str
    key_type: Literal["age", "gpg", "vault"]
    item_id: str | None = None
    provider_specific_args: ProviderImportArgs = field(
        default_factory=ProviderImportArgs
    )


@dataclass(frozen=True)
class SecretsRotatePayload:
    type: Literal["age", "pgp", "vault"]
    keys: list[str]
    context: SecretsContext
    index: int | None = None
    pgp_server: str | None = None
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
    keys: list[str]
    context: SecretsContext
    cat_sops_file: bool = False
    as_json: bool = False
    value_only: bool = False


@dataclass(frozen=True)
class SecretsSetShamirPayload:
    index: int
    share: int
    context: SecretsContext


@dataclass(frozen=True)
class RambleCreatePayload:
    target: str
    context: SecretsContext
    encrypt: bool
    keys: list[str] | None = None


@dataclass(frozen=True)
class RambleEditPayload:
    target: str
    context: SecretsContext
    edit_sops_file: bool = False


@dataclass(frozen=True)
class RambleEncryptPayload:
    target: str
    context: SecretsContext
    keys: list[str] | None = None


@dataclass(frozen=True)
class RambleReadPayload:
    targets: list[str]
    context: SecretsContext
    no_pretty: bool = False
    json: bool = False
    values: list[str] | None = None


@dataclass(frozen=True)
class RambleFindPayload:
    context: SecretsContext
    find_term: str | None = None
    tag: str | None = None
    no_pretty: bool = False
    json: bool = False


@dataclass(frozen=True)
class RambleMovePayload:
    old: str
    new: str
    context: SecretsContext


@dataclass(frozen=True)
class RambleDeletePayload:
    ramble: str
    context: SecretsContext


@dataclass(frozen=True)
class RambleUpdateEncryptPayload:
    context: SecretsContext
