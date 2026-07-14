from __future__ import annotations

# IMPORT STANDARD LIBRARIES
import typing
from uuid import uuid4

# IMPORT THIRD PARTY LIBRARIES
from comfy_api.latest import io

# IMPORT LOCAL LIBRARIES
from ._base_node import AyonBaseNode
from .. import api


class AyonLoadGenericNode(AyonBaseNode):
    """Container node loading a specified path."""

    node_id = "ayon.load.generic"
    display_name = "AYON Generic Loader"
    category = "AYON"

    @classmethod
    def define_inputs(cls) -> list[io.Input]:
        return [
            io.String.Input("project", "Project"),
            io.String.Input("folder_path", display_name="Folder Path"),
            io.String.Input("product", display_name="Product"),
            io.String.Input("version", display_name="Version"),
            io.String.Input("representation", display_name="Representation"),
            io.String.Input("representation_id", "Representation ID"),
            # io.String.Input("filepath", "Filepath"),
        ]

    @classmethod
    def define_outputs(cls) -> list[io.Output]:
        return [
            io.String.Output(
                id="filepath",
                display_name="Filepath",
                tooltip="main filepath to the representation",
            ),
        ]

    @classmethod
    def validate_inputs(cls, **kwargs) -> bool | str:
        # the default validation fails because our combo options
        # are dynamically generated
        return True

    @classmethod
    async def execute(  # ty:ignore[invalid-method-override]  # pyright: ignore[reportIncompatibleMethodOverride]
        cls,
        project: str,
        folder_path: str,
        product: str,
        version: str,
        representation: str,
        **kwargs: typing.Any,
    ) -> io.NodeOutput:

        print("------- execute -------")
        result = await api.send_message_to_client({
            "type": "ayon",
            "function": "get_representation",
            "message_id": str(uuid4()),
            "params": {
                "project": project,
                "folder_path": folder_path,
                "product": product,
                "version": version,
                "representation": representation,
            },
        })
        if not isinstance(result, dict):
            return io.NodeOutput("")

        print("--------------")
        # print("RESPONSE", response)
        # result = response.get("result", {})
        print("RESULT", result)
        filepath = result.get("filepath", "")
        print("--------------")
        print("FILEPATH", filepath)
        return io.NodeOutput(filepath)
