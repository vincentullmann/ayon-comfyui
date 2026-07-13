"""Widget to display a list of ComfyUI instances and sessions."""

# IMPORT STANDARD LIBRARIES
import typing

# IMPORT THIRD PARTY LIBRARIES
from qtpy import QtWidgets, QtCore

# IMPORT LOCAL LIBRARIES
from ayon_comfyui.tools.session_manager.instance_model import Instance


TModelIndex = QtCore.QModelIndex | QtCore.QPersistentModelIndex


# region ViewModel


class InstanceViewModel(QtCore.QAbstractTableModel):

    COLUMN_URL = 0
    COLUMN_SESSIONS = 1

    def __init__(self) -> None:
        super().__init__()
        self._instances: list[Instance] = []

    def rowCount(self, parent: TModelIndex = QtCore.QModelIndex()) -> int:
        return len(self._instances)

    def columnCount(self, parent: TModelIndex = QtCore.QModelIndex()) -> int:
        return 2

    def data(
        self,
        index: TModelIndex,
        role: int = QtCore.Qt.ItemDataRole.DisplayRole,
    ) -> typing.Any:

        if not index.isValid():
            return None

        column = index.column()
        row = index.row()
        instance = self._instances[row]

        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            if column == self.COLUMN_URL:
                return instance.url
            elif column == self.COLUMN_SESSIONS:
                return str(len(instance.sessions))

        return None

    def headerData(self, section: int, orientation: QtCore.Qt.Orientation, role: int = QtCore.Qt.ItemDataRole.DisplayRole) -> typing.Any:
        """Get the header data for a given section and orientation."""

        # only handle display role (for now)
        if role != QtCore.Qt.ItemDataRole.DisplayRole:
            return None

        # only handle horizontal orientation (for now)
        if orientation != QtCore.Qt.Orientation.Horizontal:
            return None

        if section == self.COLUMN_URL:
            return "URL"
        if section == self.COLUMN_SESSIONS:
            return "Sessions"

        return None

    # custom methods

    def set_instances(self, instances: list[Instance]) -> None:
        self.beginResetModel()
        self._instances = instances
        self.endResetModel()


# region Widget


class InstanceList(QtWidgets.QTreeView):
    """List of ComfyUI instances and sessions."""
    def __init__(self) -> None:
        super().__init__()
        # self.setWindowFlags(QtCore.Qt.WindowType.WindowStaysOnTopHint)

        self._model = InstanceViewModel()
        self.setModel(self._model)

        header = self.header()
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.ResizeToContents)

    def set_instances(self, instances: list[Instance]) -> None:
        self._model.set_instances(instances)
