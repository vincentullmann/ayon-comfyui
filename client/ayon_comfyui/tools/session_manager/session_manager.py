from __future__ import annotations
import json

# IMPORT THIRD PARTY LIBRARIES
from qtpy import QtCore, QtWidgets

# IMPORT LOCAL LIBRARIES
from ayon_comfyui.tools.session_manager.instance_list import InstanceList
from ayon_comfyui.tools.session_manager.controller import InstanceController


class SessionManager(QtWidgets.QWidget):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)

        self.resize(970, 460)

        self._instance_list = InstanceList()
        instance_list_selection_model = self._instance_list.selectionModel()
        instance_list_selection_model.selectionChanged.connect(self._on_instance_selection_changed)

        self._controller = InstanceController()

        self._button_open = QtWidgets.QPushButton("Open")
        self._button_open.clicked.connect(self._on_button_open_clicked)

        self._button_refresh = QtWidgets.QPushButton("Refresh")
        self._button_refresh.clicked.connect(self._refresh_instances)

        instances_layout = QtWidgets.QVBoxLayout()
        instances_layout.addWidget(self._instance_list)
        instances_layout.addWidget(self._button_open)
        instances_layout.addWidget(self._button_refresh)
        instances_widget = QtWidgets.QWidget()
        instances_widget.setLayout(instances_layout)

        self._input_instance = QtWidgets.QLineEdit()
        self._input_instance.setReadOnly(True)
        self._input_instance.setEnabled(False)
        self._input_instance.setPlaceholderText("Select an instance")

        self._input_session = QtWidgets.QLineEdit()
        self._input_session.setReadOnly(True)
        self._input_session.setEnabled(False)
        self._input_session.setPlaceholderText("Select a session")

        self._input_node_id = QtWidgets.QSpinBox()
        self._input_node_id.valueChanged.connect(self._on_node_id_changed)
        self._input_project = QtWidgets.QLineEdit()
        self._input_project.textChanged.connect(self._on_project_changed)
        self._input_folder = QtWidgets.QLineEdit()
        self._input_folder.textChanged.connect(self._on_folder_changed)
        self._input_product = QtWidgets.QLineEdit()
        self._input_product.textChanged.connect(self._on_product_changed)
        self._input_version = QtWidgets.QSpinBox()
        self._input_version.valueChanged.connect(self._on_version_changed)

        self._input_filepath = QtWidgets.QLineEdit()
        self._input_filepath.textChanged.connect(self._on_filepath_changed)

        inputs_layout = QtWidgets.QFormLayout()
        inputs_layout.addRow("Instance", self._input_instance)
        inputs_layout.addRow("Session", self._input_session)

        inputs_layout.addRow(QtWidgets.QLabel("Parameters:"))
        inputs_layout.addRow("Node ID", self._input_node_id)
        inputs_layout.addRow("Project", self._input_project)
        inputs_layout.addRow("Folder", self._input_folder)
        inputs_layout.addRow("Product", self._input_product)
        inputs_layout.addRow("Version", self._input_version)

        inputs_layout.addRow(QtWidgets.QLabel("Out:"))
        inputs_layout.addRow("Filepath", self._input_filepath)

        inputs_widget = QtWidgets.QWidget()
        inputs_widget.setLayout(inputs_layout)

        spliter = QtWidgets.QSplitter(orientation=QtCore.Qt.Orientation.Horizontal)
        spliter.addWidget(instances_widget)
        spliter.addWidget(inputs_widget)

        main_layout = QtWidgets.QVBoxLayout()
        main_layout.addWidget(spliter)
        self.setLayout(main_layout)

        self._refresh_timer = QtCore.QTimer()
        self._refresh_timer.timeout.connect(self._refresh_instances)
        self._refresh_timer.setInterval(1000)
        self._refresh_timer.start()

        self._load_instances()
        self._refresh_instances()

    def _on_instance_selection_changed(self) -> None:
        if instance := self._instance_list.get_selected_instance():
            self._input_instance.setText(instance.url)
        else:
            self._input_instance.setText("")

        if session := self._instance_list.get_selected_session():
            self._input_session.setText(session.id)
        else:
            self._input_session.setText("")

        self.request_node_values()

    def request_node_values(self) -> None:

        instance = self._instance_list.get_selected_instance()
        session = self._instance_list.get_selected_session()
        node_id = self._input_node_id.value()
        if not all([instance, session, node_id]):
            return

        instance.get_node_values(
            session_id=session.id,
            node_id=str(node_id),
        )

    def onClose(self) -> None:
        pass

    def _on_button_open_clicked(self) -> None:
        print("open seelcted instance")

    def _load_instances(self) -> None:
        instances = self._controller.get_instances()
        self._instance_list.set_instances(instances)

        for instance in instances:
            instance.on_event.append(self._on_instance_event)

    def _refresh_instances(self) -> None:
        self._controller.update_instances()

    def set_node_values(self, **kwargs) -> None:
        """Set multiple input values."""
        session = self._instance_list.get_selected_session()
        if not session:
            return
        instance = self._instance_list.get_selected_instance()
        if not instance:
            return

        instance.set_node_values(
            session_id=session.id,
            node_id=self._input_node_id.value(),
            params=kwargs,
        )

    def set_node_value(self, input_name: str, value: str) -> None:
        """Set the value of a single input."""
        self.set_node_values(**{input_name: value})

    def _on_node_id_changed(self, value):
        self.request_node_values()

    def _on_node_values_received(self, **kwargs) -> None:
        print("node values received", kwargs)

        values_str = kwargs.get("values", "")
        if not values_str:
            return
        values = json.loads(values_str)

        if version := values.get("version"):
            try:
                version = int(version)
            except ValueError:
                version = 0
            self._input_version.setValue(version)
        if project := values.get("project"):
            self._input_project.setText(project)
        if folder := values.get("folder_path"):
            self._input_folder.setText(folder)
        if product := values.get("product"):
            self._input_product.setText(product)
        if filepath := values.get("filepath"):
            self._input_filepath.setText(filepath)

    def _on_project_changed(self, value):
        self.set_node_value("project", value)

    def _on_folder_changed(self, value):
        self.set_node_value("folder_path", value)

    def _on_product_changed(self, value):
        self.set_node_value("product", value)

    def _on_version_changed(self, value):
        self.set_node_value("version", value)

    def _on_filepath_changed(self, value):
        instance = self._instance_list.get_selected_instance()
        if not instance:
            return

        instance.filepath = value

    def _on_instance_event(self, event: str, **kwargs) -> None:
        if event == "node_values_received":
            self._on_node_values_received(**kwargs)
