""""""
from __future__ import annotations

# IMPORT STANDARD LIBRARY
import asyncio
import json
import typing
from uuid import uuid4

# IMPORT THIRD PARTY LIBRARY MODULES
from aiohttp import web
from server import PromptServer  # pyright: ignore[reportAttributeAccessIssue]

# IMPORT LOCAL LIBRARY MODULES


if typing.TYPE_CHECKING:

    # ty keeps picking up the "server" module in the repo root,
    # while the one we want is from ComfyUI
    from ComfyUI.server import PromptServer

    from aiohttp._websocket.models import WSMessage


SERVER: PromptServer = PromptServer.instance  # ty:ignore[unresolved-attribute]

_CLIENTS: set[web.WebSocketResponse] = set()
"""Clients connected to the websocket server."""

_PENDING: dict[str, asyncio.Future] = {}
"""Pending responses."""

_RESPONSE_TIMEOUT = 2.0
"""Timeout for responses (in seconds)."""

HANDLERS: dict[str, typing.Callable] = {}


async def send_to_backend(data: dict, client: web.WebSocketResponse):
    """Send a message to the backend.

    Args:
        data: The data to send.
    """

    print("SENDING TO BACKEND", data)

    function_name = data.pop("function", None) or data.get("method", None)
    if not function_name:
        print("INVALID PAYLOAD", data)
        return

    message_id = data.pop("message_id", None) or data.pop("id", None)

    handler = HANDLERS.get(function_name)
    if not handler:
        print("HANDLER NOT FOUND", function_name)
        return

    result = handler(data)
    print("RESULT", result)

    if result:
        await send_message_to_client(
            payload={
                "type": "ayon",
                "function": function_name,
                "message_id": message_id,
                "result": result,
            },
            client=client,
        )


def send_to_frontend(data: dict):
    """Send a message to the frontend.

    see: https://docs.comfy.org/development/comfyui-server/comms_messages#custom-message-types

    Args:
        data: The data to send.
        sid: The session ID to send the message to.
            If not provided, the message will be sent to all clients.
.
    """
    sid = data.pop("session_id", None)
    SERVER.send_sync(event="ayon", data=data, sid=sid)


# def handle_result(pending: asyncio.Future, result: typing.Any):
#     """Resolve a pending response future if still waiting."""
#     if pending.done():
#         return
# 
#     pending.set_result(result)


async def handle_text_message(msg: WSMessage, client: web.WebSocketResponse):
    """Handle a text message from the websocket server."""
    try:
        payload = json.loads(msg.data)
    except json.JSONDecodeError:
        return

    if not isinstance(payload, dict):
        return

    print(f"[handle_text_message] {payload=}")
    if payload.get("type") not in ("ayon", "ayon-reply"):
        return

    if message_id := payload.get("message_id"):
        # check if this is a response to a previous request
        if pending := _PENDING.pop(message_id, None):

            if not pending.done():
                loop = pending.get_loop()
                loop.call_soon_threadsafe(
                    pending.set_result,
                    payload.get("result"),
                )

    if payload.get("target") == "frontend":
        send_to_frontend(payload)
        return
    else:
        return await send_to_backend(payload, client)


async def handle_message(msg: WSMessage, client: web.WebSocketResponse):
    """Handle a message from the websocket server."""
    if msg.type == web.WSMsgType.TEXT:
        return await handle_text_message(msg, client)
    if msg.type == web.WSMsgType.BINARY:
        print(msg.data)
    if msg.type == web.WSMsgType.ERROR:
        print(msg.data)


@SERVER.routes.get("/ayon/ws")
async def ayon_ws(request):
    """Handle incoming websocket connections."""
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    _CLIENTS.add(ws)  # track clients

    try:
        async for msg in ws:
            await handle_message(msg, ws)
    finally:
        _CLIENTS.discard(ws)

    return ws


async def send_message_to_client(
    payload: dict,
    timeout_seconds: float = _RESPONSE_TIMEOUT,
    client: web.WebSocketResponse | None = None,
):
    """Send a message from ComfyUI to the AYON websocket client(s).

    Args:
        message: The message to send.
        timeout_seconds: The timeout for the message.
        client: The client to send the message to.
            If not provided, the message will be sent to the first client.

    """
    if not client:
        client = next((ws for ws in _CLIENTS if not ws.closed), None)
    if client is None:
        # raise RuntimeError("No connected AYON websocket clients")
        print("[send] no ayon clients connected")
        return

    # send message
    print("[send]", payload)
    await client.send_json(payload)

    # wait for a response
    if message_id := payload.get("message_id"):
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        _PENDING[message_id] = future
        try:
            return await asyncio.wait_for(future, timeout=timeout_seconds)
        except asyncio.TimeoutError as exc:
            message = (
                "Timed out waiting for websocket response "
                f"for id '{message_id}'"
            )
            raise TimeoutError(message) from exc
        finally:
            _PENDING.pop(message_id, None)


@SERVER.routes.get("/ayon/sessions")
async def get_sessions(request: web.Request) -> web.Response:
    """Returns a list of all active sessions on this ComfyUI instance."""
    return web.json_response(list(SERVER.sockets.keys()))


def get_instance_status(data: dict) -> dict:
    """Get the status of an instance."""

    sessions = list(SERVER.sockets.keys())
    return {
        "sessions": sessions,
    }


HANDLERS["get_instance_status"] = get_instance_status


@SERVER.routes.patch("/ayon/session_update")
async def session_update(request: web.Request) -> web.Response:
    """Handle a session update event."""
    data = await request.post()
    await send_message_to_client(payload={
        "type": "ayon",
        "function": "session_update",
        "params": dict(data),
    })
    return web.json_response({})


@SERVER.routes.post("/ayon/node_values")
async def node_values(request: web.Request) -> web.Response:
    """Handle a session update event."""
    # TODO: message_id
    data = await request.post()
    await send_message_to_client(payload={
        "type": "ayon-reply",
        "function": "node_values",
        "params": dict(data),
    })
    return web.json_response({})
