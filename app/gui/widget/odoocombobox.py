from PyQt6.QtCore import Qt
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
        if role == Qt.ItemDataRole.UserRole:
            model = self.model()
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
