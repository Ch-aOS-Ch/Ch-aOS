from __future__ import annotations

from typing import Any, Literal

"""
Yes, Yes, I know that dataclasses exist in Python, but they were making a 0.08s startup time into a
0.15s startup time, which is a significant increase, and that's just not acceptable for a CLI tool. So instead,
We use __slots__ and a custom __init__ to achieve the same thing, but with a much lower startup time. Plus,
this way we have more control over the initialization and can do things like validation or default values more easily.

cool, right?
"""


class BasePayload:
    __slots__ = ()

    def __repr__(self) -> str:
        attrs = ", ".join(f"{slot}={getattr(self, slot)!r}" for slot in self.__slots__)
        return f"{self.__class__.__name__}({attrs})"

    def __eq__(self, other: Any) -> bool:
        if self.__class__ is not other.__class__:
            return NotImplemented

        return all(
            getattr(self, slot) == getattr(other, slot) for slot in self.__slots__
        )

    def to_dict(self):
        return {s: getattr(self, s) for s in self.__slots__}


class TeamPrunePayload(BasePayload):
    __slots__ = ("companies", "i_know_what_im_doing")

    def __init__(self, companies: list[str], i_know_what_im_doing: bool):
        self.companies = companies
        self.i_know_what_im_doing = i_know_what_im_doing


class TeamListPayload(BasePayload):
    __slots__ = ("company", "no_pretty", "json")

    def __init__(self, company: str | None, no_pretty: bool, json: bool):
        self.company = company
        self.no_pretty = no_pretty
        self.json = json


class TeamClonePayload(BasePayload):
    __slots__ = ("target", "path")

    def __init__(self, target: str, path: str | None):
        self.target = target
        self.path = path


class TeamInitPayload(BasePayload):
    __slots__ = ("target", "path", "i_know_what_im_doing")

    def __init__(self, target: str, path: str | None, i_know_what_im_doing: bool):
        self.target = target
        self.path = path
        self.i_know_what_im_doing = i_know_what_im_doing


class TeamActivatePayload(BasePayload):
    __slots__ = ("path",)

    def __init__(self, path: str | None):
        self.path = path


class TeamDeactivatePayload(BasePayload):
    __slots__ = ("company", "teams")

    def __init__(self, company: str, teams: list[str]):
        self.company = company
        self.teams = teams


class ExplainPayload(BasePayload):
    __slots__ = ("topics", "no_pretty", "json", "details", "complexity")

    def __init__(
        self,
        topics: list[str],
        no_pretty: bool,
        json: bool,
        details: str = "basic",
        complexity: str = "basic",
    ):
        self.topics = topics
        self.no_pretty = no_pretty
        self.json = json
        self.details = details
        self.complexity = complexity


class SetPayload(BasePayload):
    __slots__ = ("chobolo_file", "sops_file", "secrets_file")

    def __init__(
        self,
        chobolo_file: str | None,
        sops_file: str | None,
        secrets_file: str | None,
    ):
        self.chobolo_file = chobolo_file
        self.sops_file = sops_file
        self.secrets_file = secrets_file


class ProviderConfigPayload(BasePayload):
    __slots__ = ("provider", "ephemeral_provider_args")

    def __init__(
        self,
        provider: str | None = None,
        ephemeral_provider_args: dict[str, Any] | None = None,
    ):
        self.provider = provider
        self.ephemeral_provider_args = (
            ephemeral_provider_args if ephemeral_provider_args is not None else {}
        )


class SecretsContext(BasePayload):
    __slots__ = (
        "team",
        "sops_file_override",
        "secrets_file_override",
        "provider_config",
        "i_know_what_im_doing",
    )

    def __init__(
        self,
        team: str | None = None,
        sops_file_override: str | None = None,
        secrets_file_override: str | None = None,
        provider_config: ProviderConfigPayload | None = None,
        i_know_what_im_doing: bool = False,
    ):
        self.team = team
        self.sops_file_override = sops_file_override
        self.secrets_file_override = secrets_file_override
        self.provider_config = provider_config
        self.i_know_what_im_doing = i_know_what_im_doing


class ProviderExportArgs(BasePayload):
    __slots__ = ()

    def __init__(self):
        pass


class ProviderImportArgs(BasePayload):
    __slots__ = ()

    def __init__(self):
        pass


class SecretsExportPayload(BasePayload):
    __slots__ = (
        "provider_name",
        "key_type",
        "no_import",
        "save_to_config",
        "item_name",
        "keys",
        "vault_addr",
        "fingerprints",
        "provider_specific_args",
    )

    def __init__(
        self,
        provider_name: str,
        key_type: Literal["age", "gpg", "vault"],
        no_import: bool,
        save_to_config: bool,
        item_name: str | None = None,
        keys: str | None = None,
        vault_addr: str | None = None,
        fingerprints: list[str] | None = None,
        provider_specific_args: ProviderExportArgs | None = None,
    ):
        self.provider_name = provider_name
        self.key_type = key_type
        self.no_import = no_import
        self.save_to_config = save_to_config
        self.item_name = item_name
        self.keys = keys
        self.vault_addr = vault_addr
        self.fingerprints = fingerprints
        self.provider_specific_args = (
            provider_specific_args
            if provider_specific_args is not None
            else ProviderExportArgs()
        )


class SecretsImportPayload(BasePayload):
    __slots__ = ("provider_name", "key_type", "item_id", "provider_specific_args")

    def __init__(
        self,
        provider_name: str,
        key_type: Literal["age", "gpg", "vault"],
        item_id: str | None = None,
        provider_specific_args: ProviderImportArgs | None = None,
    ):
        self.provider_name = provider_name
        self.key_type = key_type
        self.item_id = item_id
        self.provider_specific_args = (
            provider_specific_args
            if provider_specific_args is not None
            else ProviderImportArgs()
        )


class SecretsRotatePayload(BasePayload):
    __slots__ = ("type", "keys", "context", "index", "pgp_server", "create")

    def __init__(
        self,
        type: Literal["age", "pgp", "vault"],
        keys: list[str],
        context: SecretsContext,
        index: int | None = None,
        pgp_server: str | None = None,
        create: bool = False,
    ):
        self.type = type
        self.keys = keys
        self.context = context
        self.index = index
        self.pgp_server = pgp_server
        self.create = create


class SecretsListPayload(BasePayload):
    __slots__ = ("type", "context", "no_pretty", "json", "value")

    def __init__(
        self,
        type: Literal["age", "pgp", "vault"],
        context: SecretsContext,
        no_pretty: bool = False,
        json: bool = False,
        value: bool = False,
    ):
        self.type = type
        self.context = context
        self.no_pretty = no_pretty
        self.json = json
        self.value = value


class SecretsEditPayload(BasePayload):
    __slots__ = ("context", "edit_sops_file")

    def __init__(self, context: SecretsContext, edit_sops_file: bool = False):
        self.context = context
        self.edit_sops_file = edit_sops_file


class SecretsPrintPayload(BasePayload):
    __slots__ = ("context", "print_sops_file", "as_json")

    def __init__(
        self,
        context: SecretsContext,
        print_sops_file: bool = False,
        as_json: bool = False,
    ):
        self.context = context
        self.print_sops_file = print_sops_file
        self.as_json = as_json


class SecretsCatPayload(BasePayload):
    __slots__ = ("keys", "context", "cat_sops_file", "as_json", "value_only")

    def __init__(
        self,
        keys: list[str],
        context: SecretsContext,
        cat_sops_file: bool = False,
        as_json: bool = False,
        value_only: bool = False,
    ):
        self.keys = keys
        self.context = context
        self.cat_sops_file = cat_sops_file
        self.as_json = as_json
        self.value_only = value_only


class SecretsSetShamirPayload(BasePayload):
    __slots__ = ("index", "share", "context")

    def __init__(self, index: int, share: int, context: SecretsContext):
        self.index = index
        self.share = share
        self.context = context


class RambleCreatePayload(BasePayload):
    __slots__ = ("target", "context", "encrypt", "keys")

    def __init__(
        self,
        target: str,
        context: SecretsContext,
        encrypt: bool,
        keys: list[str] | None = None,
    ):
        self.target = target
        self.context = context
        self.encrypt = encrypt
        self.keys = keys


class RambleEditPayload(BasePayload):
    __slots__ = ("target", "context", "edit_sops_file")

    def __init__(
        self, target: str, context: SecretsContext, edit_sops_file: bool = False
    ):
        self.target = target
        self.context = context
        self.edit_sops_file = edit_sops_file


class RambleEncryptPayload(BasePayload):
    __slots__ = ("target", "context", "keys")

    def __init__(
        self,
        target: str,
        context: SecretsContext,
        keys: list[str] | None = None,
    ):
        self.target = target
        self.context = context
        self.keys = keys


class RambleReadPayload(BasePayload):
    __slots__ = ("targets", "context", "no_pretty", "json", "values")

    def __init__(
        self,
        targets: list[str],
        context: SecretsContext,
        no_pretty: bool = False,
        json: bool = False,
        values: list[str] | None = None,
    ):
        self.targets = targets
        self.context = context
        self.no_pretty = no_pretty
        self.json = json
        self.values = values


class RambleFindPayload(BasePayload):
    __slots__ = ("context", "find_term", "tag", "no_pretty", "json")

    def __init__(
        self,
        context: SecretsContext,
        find_term: str | None = None,
        tag: str | None = None,
        no_pretty: bool = False,
        json: bool = False,
    ):
        self.context = context
        self.find_term = find_term
        self.tag = tag
        self.no_pretty = no_pretty
        self.json = json


class RambleMovePayload(BasePayload):
    __slots__ = ("old", "new", "context")

    # Since we use a singular "ramble_context" for all ramble operations,
    # we can reduce code duplication by passing the whole context instead of just the team
    # just be known that we use _only_ the team attribute of the context in the ramble move operation
    def __init__(self, old: str, new: str, context: SecretsContext):
        self.old = old
        self.new = new
        self.context = context


class RambleDeletePayload(BasePayload):
    __slots__ = ("ramble", "context")

    # Same as the above
    def __init__(self, ramble: str, context: SecretsContext):
        self.ramble = ramble
        self.context = context


class RambleUpdateEncryptPayload(BasePayload):
    __slots__ = ("context",)

    # ye, only context
    def __init__(self, context: SecretsContext):
        self.context = context
