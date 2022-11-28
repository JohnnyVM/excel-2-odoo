from PyQt6.QtWidgets import QTableView

from ..model.odoomodel import OdooModel
from .delegate.odoocomboboxdelegate import OdooMany2OneDelegate, OdooMany2ManyDelegate


class OdooTableView(QTableView):

    def __init__(self, parent=None):
        QTableView.__init__(self, parent)

    def setModel(self, model: OdooModel):
        super().setModel(model)
        for column, attributes in enumerate(model._fields.values()):
            if 'relation' in attributes and attributes['type'] == 'many2one':
                self.setItemDelegateForColumn(column, OdooMany2OneDelegate(parent=self))
            if 'relation' in attributes and attributes['type'] == 'many2many':
                self.setItemDelegateForColumn(column, OdooMany2ManyDelegate(parent=self))
