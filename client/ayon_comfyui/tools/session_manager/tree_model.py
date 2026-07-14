"""Widget to display a list of ComfyUI instances and sessions."""

from __future__ import annotations

# IMPORT STANDARD LIBRARIES
import typing

# IMPORT THIRD PARTY LIBRARIES
from qtpy import QtCore

if typing.TYPE_CHECKING:
    TModelIndex = QtCore.QModelIndex | QtCore.QPersistentModelIndex


class Treeitem:
    def __init__(self, parent: Treeitem | None = None) -> None:
        self.parent = parent
        self.children: list[Treeitem] = []

    def child(self, row: int) -> Treeitem | None:
        if 0 <= row < len(self.children):
            return self.children[row]
        return None

    def row(self) -> int:
        if self.parent is None:
            return 0
        try:
            return self.parent.children.index(self)
        except ValueError:
            return 0

    def data(
        self,
        index: QtCore.QModelIndex | QtCore.QPersistentModelIndex,
        role: int = QtCore.Qt.ItemDataRole.DisplayRole,
    ) -> str | None:
        pass


class TreeModel(QtCore.QAbstractItemModel):

    header_labels: list[str] = []

    def __init__(self) -> None:
        super().__init__()
        self._root = Treeitem()

    def index(
        self,
        row: int,
        column: int,
        parent: TModelIndex = QtCore.QModelIndex(),
    ) -> QtCore.QModelIndex:

        item = parent.internalPointer()
        if item is None:  # is the root item
            item = self._root

        if isinstance(item, Treeitem):
            if child_item := item.child(row):
                return self.createIndex(row, column, child_item)

        return QtCore.QModelIndex()

    def parent(self, index: TModelIndex) -> QtCore.QModelIndex:  # ty:ignore[invalid-method-override]  # pyright: ignore[reportIncompatibleMethodOverride]
        """Return the parent of the item at the given index."""
        if not index.isValid():
            return QtCore.QModelIndex()

        item = index.internalPointer()
        if item == self._root:
            return QtCore.QModelIndex()

        if isinstance(item, Treeitem):
            if parent := item.parent:
                return self.createIndex(parent.row(), 0, parent)

        return QtCore.QModelIndex()

    def rowCount(self, parent: TModelIndex = QtCore.QModelIndex()) -> int:
        if not parent.isValid():
            item = self._root
        else:
            item = parent.internalPointer()

        if isinstance(item, Treeitem):
            return len(item.children)

        return 0

    def columnCount(self, parent: TModelIndex = QtCore.QModelIndex()) -> int:
        """Return the number of columns for the given parent."""
        return len(self.header_labels)

    def data(
        self,
        index: TModelIndex,
        role: int = QtCore.Qt.ItemDataRole.DisplayRole,
    ) -> str | None:
        if not index.isValid():
            return None

        node = index.internalPointer()
        if isinstance(node, Treeitem):
            return node.data(index, role)

        return None

    def headerData(
        self,
        section: int,
        orientation: QtCore.Qt.Orientation,
        role: int = QtCore.Qt.ItemDataRole.DisplayRole,
    ) -> str | None:

        # we only show horizontal headers
        if orientation != QtCore.Qt.Orientation.Horizontal:
            return None
        if role != QtCore.Qt.ItemDataRole.DisplayRole:
            return None

        try:
            return self.header_labels[section]
        except IndexError:
            return None
