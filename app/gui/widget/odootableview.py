from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QTableView

from ..model.odoomodel import OdooModel
from .delegate.odoocomboboxdelegate import OdooMany2OneDelegate, OdooMany2ManyDelegate


class OdooTableView(QTableView):

    def __init__(self, parent=None):
        QTableView.__init__(self, parent)

    def setModel(self, model: OdooModel):
        old_model = self.model()
        if old_model:
            old_model.removeRows(0, old_model.rowCount())
        super().setModel(model)
        for column in range(model.columnCount()):
            field = model.headerData(column, Qt.Orientation.Horizontal, Qt.ItemDataRole.UserRole)
            attributes = tuple(field.values())[0]
            if 'relation' in attributes and attributes['type'] == 'many2one':
                self.setItemDelegateForColumn(column, OdooMany2OneDelegate(parent=self))
            if 'relation' in attributes and attributes['type'] == 'many2many':
                self.setItemDelegateForColumn(column, OdooMany2ManyDelegate(parent=self))
