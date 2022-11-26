from PyQt6 import QtCore
from PyQt6.QtWidgets import (
        QWidget,
        QComboBox)

from ..model.odoomodel import OdooModel


class OdooComboBox(QComboBox):
    """ """
    def __init__(self, parent: QWidget = None):
        QComboBox.__init__(self, parent)

    def setModel(self, model: OdooModel, display_field: str = "display_name") -> None:
        column = 1
        fields = iter(model._fields.keys())
        while (field := next(fields, None)) is not None and field != display_field:
            column += 1
        
        if field != display_field:
            raise ValueError(__name__ + f": {display_field} Invalid field")

        super().setModel(model)
        self.setModelColumn(column)