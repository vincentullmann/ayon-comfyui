from __future__ import annotations

# IMPORT STANDARD LIBRARIES
import dataclasses
import datetime
from enum import Enum
import json
from typing import Callable

# IMPORT THIRD PARTY LIBRARIES
from qtpy import QtWebSockets


@dataclasses.dataclass
class Session:

    class Status(Enum):
        IDLE = "idle"
        RENDERING = "rendering"
        UNKNOWN = "unknown"

    id: str
    user: str = ""
    status: Status = Status.UNKNOWN
    last_updated: datetime.datetime = datetime.datetime.min

    @classmethod
    def from_dict(cls, data: dict) -> Session:
        return cls(
            id=data.get("id", ""),
            user=data.get("user", ""),
            status=data.get("status", cls.Status.UNKNOWN),
            last_updated=data.get("last_updated", datetime.datetime.min),
        )


@dataclasses.dataclass
class Instance:

    class Status(Enum):
        ONLINE = "online"
        OFFLINE = "offline"
        UNKNOWN = "unknown"

    url: str
    sessions: list[Session] = dataclasses.field(default_factory=list)
    status: Status = Status.UNKNOWN
    last_updated: datetime.datetime = datetime.datetime.min

    _ws: QtWebSockets.QWebSocket = dataclasses.field(init=False)
    """WebSocket connection to the ComfyUI instance"""

    on_update: list[Callable[[Instance], None]] = dataclasses.field(init=False)

    def __post_init__(self) -> None:
        self.on_update = []
        self.on_update.append(self._on_updated)

        # initialize the WebSocket connection
        self._ws = QtWebSockets.QWebSocket()
        self._ws.open(self.ws_url)
        self._ws.connected.connect(self._on_connected)
        self._ws.disconnected.connect(self._on_disconnected)
        self._ws.textMessageReceived.connect(self._on_text_message)

    @property
    def ws_url(self) -> str:
        url = self.url.removeprefix("http")  # we leave the "s://" part from "https://"
        return f"ws{url}/ayon/ws"

    def _emit_updated(self) -> None:
        """Triger all on_update callbacks"""
        for callback in list(self.on_update):
            callback(self)

    ############################################################################
    # WebSocket callbacks

    def _on_updated(self, instance: Instance) -> None:
        self.last_updated = datetime.datetime.now()

    def _on_connected(self, *args, **kwargs) -> None:
        print("CONNECTED", args, kwargs)
        self.status = self.Status.ONLINE
        self._emit_updated()

    def _on_disconnected(self) -> None:
        self.status = self.Status.OFFLINE
        self._emit_updated()

    def _on_text_message(self, message: str) -> None:
        print("TEXT MESSAGE", message)

        try:
            data = json.loads(message)
        except json.JSONDecodeError:
            print("JSON DECODE ERROR", message)
            return

        if data["type"] != "ayon":
            return

        result = data.get("result", None)

        if data["function"] == "get_instance_status":
            self._update_status(result)

        self.status = self.Status.ONLINE
        self._emit_updated()

    ############################################################################
    # Helper functions

    def fetch_status(self) -> None:
        self._ws.sendTextMessage(json.dumps({
            "type": "ayon",
            "function": "get_instance_status",
        }))

    def _update_status(self, data: dict) -> None:
        self.sessions = [Session(id=session) for session in data["sessions"]]
