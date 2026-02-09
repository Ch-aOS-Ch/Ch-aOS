from dataclasses import dataclass
from typing import List, Optional


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
