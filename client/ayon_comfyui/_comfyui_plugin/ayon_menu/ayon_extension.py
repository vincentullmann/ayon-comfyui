"""Define Entrypoint for all AYON related plugins and nodes.

Using the V3 API to remain compatible for a loooooong time.
"""

import asyncio
from comfy_api.latest import ComfyExtension, io
from typing_extensions import override

from .nodes.context_node import AyonContextNode
from .nodes.load_generic import AyonLoadGenericNode
from .nodes.load_nodes import (
    AyonLoad3DModelNode,
    AyonLoadImageNode,
    AyonLoadVideoNode,
)
from .nodes.publish_nodes import (
    AyonSave3DModelNode,
    AyonSaveNode,
    AyonSaveVideoNode,
)


class AyonComfyUIExtension(ComfyExtension):
    """Main Ayon Extension"""

    """
    def __init__(self):
        print("AyonComfyUIExtension __init__")

        self.ws_app = get_app()
        self.app_runner = web.AppRunner(self.ws_app)
    """

    @override
    async def get_node_list(self) -> list[type[io.ComfyNode]]:
        return [
            AyonSaveNode,
            AyonSaveVideoNode,
            AyonSave3DModelNode,
            AyonContextNode,
            AyonLoadGenericNode,
            AyonLoadImageNode,
            AyonLoadVideoNode,
            AyonLoad3DModelNode,
        ]


async def comfy_entrypoint() -> AyonComfyUIExtension:
    print("Running internal websocket server for Ayon...")
    # Thread(target=run_server).start()
    return AyonComfyUIExtension()
