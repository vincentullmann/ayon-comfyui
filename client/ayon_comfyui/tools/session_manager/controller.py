from __future__ import annotations

from ayon_comfyui.tools.session_manager.instance_model import Instance, Session


class InstanceController:
    def __init__(self) -> None:
        pass

    def open_instance(self, instance: Instance) -> None:
        pass

    def close_instance(self, instance: Instance) -> None:
        pass

    def get_instances(self) -> list[Instance]:
        return [

            Instance(
                url="localhost:8188",
                sessions=[
                    Session(id="abcd-efgh-ijkl-mnop"),
                    Session(id="pqrs-tuvw-xyz-1234"),
                ]
            ),
            Instance(
                url="10.0.0.100:8188",
                sessions=[
                    Session(id="abcd-efgh-ijkl-mnop"),
                ]
            ),
            Instance(
                url="10.0.0.101:8188",
                sessions=[]
            ),
        ]

    def get_instance(self, instance_id: str) -> Instance | None:
        return None
