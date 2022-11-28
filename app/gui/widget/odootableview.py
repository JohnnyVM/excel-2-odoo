from PyQt6.QtWidgets import QTableView

from ..model.odoomodel import OdooModel
from .delegate.odoocomboboxdelegate import OdooComboBoxDelegate


class OdooTableView(QTableView):

    def __init__(self, parent=None):
        QTableView.__init__(self, parent)

    def setModel(self, model: OdooModel):
        super().setModel(model)
        for column, attributes in enumerate(model._fields.values()):
            if 'relation' in attributes:
                self.setItemDelegateForColumn(column, OdooComboBoxDelegate(parent=self))
