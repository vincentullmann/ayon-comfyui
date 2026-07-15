from __future__ import annotations
from qtpy import QtCore

from ayon_comfyui.tools.session_manager.instance_model import Instance


class InstanceController(QtCore.QObject):

    instance_updated = QtCore.Signal(Instance)  # ruff:ignore[report-unsupported-signal-type]

    def __init__(self) -> None:
        super().__init__()

        self._instances: list[Instance] = []

        # test
        self._instances = [
            Instance(url="http://127.0.0.1:8188"),
            Instance(url="http://127.0.0.1:8189"),
            Instance(url="http://192.168.1.32:8188"),
        ]

    def _on_instance_updated(self, instance: Instance) -> None:
        self.instance_updated.emit(instance)

    def open_instance(self, instance: Instance) -> None:
        pass

    def close_instance(self, instance: Instance) -> None:
        pass

    def get_instances(self) -> list[Instance]:
        return self._instances

    def get_instance(self, url: str) -> Instance | None:
        for instance in self._instances:
            if instance.url.lower() == url.lower():
                return instance
        return None

    def update_instance(self, instance: Instance) -> None:
        print("update_instance", instance.url)
        instance.connect()
        instance.fetch_status()

    def update_instances(self) -> None:
        for instance in self._instances:
            self.update_instance(instance)
