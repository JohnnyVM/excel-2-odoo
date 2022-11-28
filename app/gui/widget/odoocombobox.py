from PyQt6.QtCore import Qt, QVariant
from PyQt6.QtWidgets import (QWidget, QComboBox)

from ..model.odoomodel import OdooModel


class OdooComboBox(QComboBox):
    """ """

    def __init__(self, parent: QWidget = None):
        QComboBox.__init__(self, parent)

    def setModel(
            self, model: OdooModel, display_field: str = "display_name") -> None:
        super().setModel(model)
        self.setModelColumn(model.fieldNameColumn(display_field))

    def itemData(self, index: int, role: int = Qt.ItemDataRole.UserRole):
        model = self.model()
        if role == Qt.ItemDataRole.UserRole:
            column = model.fieldNameColumn('id')
            return model.data(model.index(index, column), Qt.ItemDataRole.DisplayRole)

        return super().itemData(index, role)

    def currentData(self, role: int = Qt.ItemDataRole.UserRole):
        if role == Qt.ItemDataRole.UserRole:
            model = self.model()
            column = model.fieldNameColumn('id')
            index = self.currentIndex()
            return model.data(model.index(index, column), Qt.ItemDataRole.DisplayRole)

        return super().currentData(role)

    def findData(
            self,
            data: QVariant,
            role: int = Qt.ItemDataRole.UserRole,
            flags: int = Qt.MatchFlag.MatchExactly | Qt.MatchFlag.MatchCaseSensitive):
        if role == Qt.ItemDataRole.UserRole:
            model = self.model()
            for pos, row in enumerate(model._data):
                if row['id'] == data:
                    return pos
            return -1

        return super().findData(data, role, flags)
