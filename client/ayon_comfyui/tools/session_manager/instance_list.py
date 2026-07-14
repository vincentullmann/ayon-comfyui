"""Widget to display a list of ComfyUI instances and sessions."""

from __future__ import annotations

# IMPORT STANDARD LIBRARIES
import typing

# IMPORT THIRD PARTY LIBRARIES
from qtpy import QtGui, QtWidgets, QtCore
from ayon_core.tools.utils.lib import get_qt_icon
from ayon_core.lib.icon_definitions import MaterialSymbolsIcon

# IMPORT LOCAL LIBRARIES
from ayon_comfyui.tools.session_manager.instance_model import Instance, Session
from ayon_comfyui.tools.session_manager.tree_model import Treeitem, TreeModel

if typing.TYPE_CHECKING:
    TModelIndex = QtCore.QModelIndex | QtCore.QPersistentModelIndex


STATUS_COLORS = {
    Instance.Status.ONLINE: "#29cc29",
}

STATUS_ICONS = {
    Instance.Status.ONLINE: MaterialSymbolsIcon(
        name="play_circle",
        color="#29cc29",
    ),
    Instance.Status.OFFLINE: MaterialSymbolsIcon(
        name="block",
        color="#ff0000",
    ),
    Instance.Status.UNKNOWN: MaterialSymbolsIcon(
        name="question_mark",
        color="#ccc",
    ),
}

# region ViewModel


class RootTreeNode(Treeitem):

    def __init__(self, instances: list[Instance]) -> None:
        super().__init__(parent=None)
        self.children = [InstanceTreeNode(i, self) for i in instances]


class InstanceTreeNode(Treeitem):

    children: list[SessionTreeNode] = []

    def __init__(self, instance: Instance, parent: RootTreeNode) -> None:
        super().__init__(parent)
        self.instance = instance
        self.children = [SessionTreeNode(s, self) for s in instance.sessions]  # pyright: ignore[reportIncompatibleVariableOverride]

    def update(self, instance: Instance, index: TModelIndex) -> None:
        """Update the instance tree item"""
        model = index.model()

        self.instance = instance
        new_sessions = instance.sessions
        old_sessions = [child.session for child in self.children]
        add_sessions = [s for s in new_sessions if s not in old_sessions]
        rem_sessions = [s for s in old_sessions if s not in new_sessions]

        # remove old
        for row, child in enumerate(self.children[:]):
            if child.session in rem_sessions:
                model.beginRemoveRows(index, row, row)
                self.children.pop(row)
                model.endRemoveRows()

        # add new
        for row, session in enumerate(new_sessions):
            if session not in add_sessions:
                continue

            model.beginInsertRows(index, row, row)

            node = SessionTreeNode(session, self)
            self.children.insert(row, node)

            model.endInsertRows()

    def data(
        self,
        index: TModelIndex,
        role: int = QtCore.Qt.ItemDataRole.DisplayRole,
    ) -> typing.Any:
        column = index.column()

        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            if column == 0:
                return self.instance.url
            if column == 2:
                return self.instance.status.value
            if column == 3:
                return self.instance.last_updated.isoformat()

        if role == QtCore.Qt.ItemDataRole.DecorationRole:
            if column == 0:
                if icon_def := STATUS_ICONS.get(self.instance.status, None):
                    return get_qt_icon(icon_def)


class SessionTreeNode(Treeitem):
    def __init__(self, session: Session, parent: InstanceTreeNode) -> None:
        super().__init__(parent)
        self.session = session
        self.instance = parent.instance

        self.font = QtGui.QFont()
        self.font.setStyleHint(QtGui.QFont.StyleHint.Monospace)

        # shorten the session id a bit
        start, end = session.id[:8], session.id[-8:]
        self._short_id = f"{start}...{end}"

    def data(
        self,
        index: TModelIndex,
        role: int = QtCore.Qt.ItemDataRole.DisplayRole,
    ) -> typing.Any:
        column = index.column()
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            if column == 0:
                return self._short_id

        if role == QtCore.Qt.ItemDataRole.FontRole:
            if column == 0:
                return self.font


class InstanceViewModel(TreeModel):
    header_labels = [
        "URL",
        "User",
        "Status",
        "last updated",
    ]

    def __init__(self) -> None:
        super().__init__()
        self._root = RootTreeNode([])

    def set_instances(self, instances: list[Instance]) -> None:
        self.beginResetModel()
        self._root = RootTreeNode(instances)
        self.endResetModel()

        for instance in instances:
            instance.on_update.append(self.update_instance)

    def get_instance_tree_item(
        self,
        instance: Instance,
    ) -> InstanceTreeNode | None:
        for child in self._root.children:
            if (
                isinstance(child, InstanceTreeNode)
                and child.instance.url == instance.url
            ):
                return child
        return None

    def update_instance(self, instance: Instance) -> None:

        node = self.get_instance_tree_item(instance)
        if node is None:
            return

        row = node.row()
        index = self.index(row, 0)  # index of the instance
        node.update(instance, index)

        index_l = self.index(row, 0)
        index_r = self.index(row, self.columnCount() - 1)
        self.dataChanged.emit(index_l, index_r)


# region Widget


class InstanceList(QtWidgets.QTreeView):
    """List of ComfyUI instances and sessions."""

    def __init__(self) -> None:
        super().__init__()

        self._model = InstanceViewModel()
        self.setModel(self._model)

        header = self.header()
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.ResizeToContents)  # ruff:ignore[reportUnknownArgument]

    def set_instances(self, instances: list[Instance]) -> None:
        self._model.set_instances(instances)

    def get_selected_nodes(self) -> list[InstanceTreeNode | SessionTreeNode]:
        selection_model = self.selectionModel()
        indexes = selection_model.selectedIndexes()
        if not indexes:
            return []
        return [index.internalPointer() for index in indexes]

    def get_selected_instance(self) -> Instance | None:
        nodes = self.get_selected_nodes()
        for node in nodes:
            # both InstanceTreeNode and SessionTreeNode have an instance attrib
            return node.instance

    def get_selected_session(self) -> Session | None:
        nodes = self.get_selected_nodes()
        for node in nodes:
            if isinstance(node, SessionTreeNode):
                return node.session
