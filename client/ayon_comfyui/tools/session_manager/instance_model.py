from __future__ import annotations

# IMPORT STANDARD LIBRARIES
import dataclasses
import datetime
from enum import Enum
import json
from typing import Callable, Any

# IMPORT THIRD PARTY LIBRARIES
from qtpy import QtWebSockets


@dataclasses.dataclass
class Session:

    class Status(Enum):
        IDLE = "idle"
        RENDERING = "rendering"
        FOCUSED = "focused"
        CLOSED = "closed"
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

    # TMP
    filepath: str = ""

    _ws: QtWebSockets.QWebSocket = dataclasses.field(init=False)
    """WebSocket connection to the ComfyUI instance"""

    on_update: list[Callable[[Instance], None]] = dataclasses.field(init=False)
    on_event: list[Callable[[str, Any], None]] = dataclasses.field(init=False)

    def __post_init__(self) -> None:
        self.on_update = []
        self.on_event = []
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

    @property
    def session_ids(self) -> list[str]:
        return [session.id for session in self.sessions]

    def get_session(self, session_id: str) -> Session | None:
        for session in self.sessions:
            if session.id == session_id:
                return session
        return None

    def _emit_updated(self) -> None:
        """Triger all on_update callbacks"""
        for callback in list(self.on_update):
            callback(self)

    def emit_event(self, event: str, **kwargs) -> None:
        for callback in list(self.on_event):
            callback(event, **kwargs)

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

        if data.get("type") not in ["ayon", "ayon-reply"]:
            return

        params = data.get("params", {})
        message_id = data.get("message_id")
        function = data.get("function")

        result = None
        if function == "get_instance_status":
            result = data.get("result", None)
            result = self._update_status(result)
        if function == "get_representation":
            result = self._get_representation(**params)
        if function == "session_update":
            self._session_update(**params)

        if result:
            print("SENDING REPLY", message_id, result)
            self._ws.sendTextMessage(json.dumps({
                "type": "ayon-reply",
                "message_id": message_id,
                "result": result,
            }))

        # self.status = self.Status.ONLINE
        # self._emit_updated()

    ############################################################################
    # Helper functions

    def connect(self) -> None:
        if self.status == self.Status.ONLINE:
            return
        self._ws.open(self.ws_url)

    def fetch_status(self) -> None:
        self._ws.sendTextMessage(json.dumps({
            "type": "ayon",
            "function": "get_instance_status",
        }))

    def _update_status(self, data: dict) -> None:
        self.sessions = [Session(id=session) for session in data["sessions"]]
        self._emit_updated()

    def _get_representation(self, **params: dict) -> dict:
        print("GET REPRESENTATION", params)

        project = params.get("project", "")
        folder_path = params.get("folder_path", "")
        version = params.get("version", "")

        path = f"{folder_path}/{version}/{self.filepath}"

        return {
            "filepath": path,
        }

    def _session_update(self, session_id: str, status: str = "", **kwargs) -> None:
        session = self.get_session(session_id)

        # ignore closed sessions
        # sometimes we might get update events for closed sessions
        # we need to ignore them
        if session and session.status == Session.Status.CLOSED:
            return

        # new session
        if session is None:
            session = Session(id=session_id)
            self.sessions.append(session)

        try:
            session.status = Session.Status[status.upper()]
        except KeyError:
            print("invalid status", status)

        self._emit_updated()

    def set_node_values(
        self,
        session_id: str,
        node_id: str | int,
        params: dict,
    ) -> None:
        """Set the values of a node.

        Args:
            session_id: The id of the session
            node_id: The id of the node
            params: A dictionary of the parameters to set
        """
        self._ws.sendTextMessage(json.dumps({
            "type": "ayon",
            "function": "set_node_values",
            "target": "frontend",

            # where
            "session_id": session_id,
            "node_id": str(node_id),   # comfyui expects a string

            # what
            "params": params,
        }))
