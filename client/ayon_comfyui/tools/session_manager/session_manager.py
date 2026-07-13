from __future__ import annotations

# IMPORT STANDARD LIBRARIES
import json
import sys

# IMPORT THIRD PARTY LIBRARIES
from qtpy import QtCore, QtNetwork, QtWebSockets, QtWidgets

# IMPORT LOCAL LIBRARIES
from ayon_comfyui.tools.session_manager.instance_list import InstanceList
from ayon_comfyui.tools.session_manager.controller import InstanceController


class SessionManager(QtWidgets.QWidget):

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)

        self._instance_list = InstanceList()
        self._controller = InstanceController()

        self._button_open = QtWidgets.QPushButton("Open")
        self._button_open.clicked.connect(self._on_button_open_clicked)

        self._button_refresh = QtWidgets.QPushButton("Refresh")
        self._button_refresh.clicked.connect(self._on_button_refresh_clicked)

        main_layout = QtWidgets.QVBoxLayout()
        main_layout.addWidget(self._instance_list)
        main_layout.addWidget(self._button_open)
        main_layout.addWidget(self._button_refresh)
        self.setLayout(main_layout)

        self._refresh_timer = QtCore.QTimer()
        self._refresh_timer.timeout.connect(self._refresh_instances)
        self._refresh_timer.setInterval(1000)
        self._refresh_timer.start()

        # initial refresh
        self._refresh_instances()

    def _on_button_open_clicked(self) -> None:
        print("open seelcted instance")

    def _on_button_refresh_clicked(self) -> None:
        self._refresh_instances()

    def _refresh_instances(self) -> None:
        print("refresh instance list")
        instances = self._controller.get_instances()
        self._instance_list.set_instances(instances)


################################################################################
# TEST

def main() -> int:
    app = QtWidgets.QApplication(sys.argv)

    # widget = WsClientWidget(URL)
    widget = SessionManager()
    widget.resize(460, 330)
    widget.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
