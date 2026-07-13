from __future__ import annotations

import dataclasses
import datetime
from enum import Enum


class InstanceStatus(Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    UNKNOWN = "unknown"


@dataclasses.dataclass
class Session:
    id: str


@dataclasses.dataclass
class Instance:

    url: str
    sessions: list[Session] = dataclasses.field(default_factory=list)

    status: InstanceStatus = InstanceStatus.UNKNOWN
    last_updated: datetime.datetime = datetime.datetime.min


