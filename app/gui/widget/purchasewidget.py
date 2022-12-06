from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QLineEdit,
    QWidget,
    QFormLayout)

from ... import settings
from ...dependencies import get_odoo
from ..model.odoomodel import OdooModel
from ..widget.odoocombobox import OdooComboBox


class PurchaseWidget(QWidget):
    changeCompany = pyqtSignal(int)

    def __init__(self, parent: QWidget = None):
        QWidget.__init__(self, parent)
        conn = get_odoo(settings.conf)
        self.supplier_selector = OdooComboBox(parent=self)
        supplier_model = OdooModel(
            conn=conn,
            name='res.partner',
            domain=(('|', ('company_id', '=', False), ('company_id', '=', parent.company_id)),),
            fields=('id', 'display_name'))
        self.changeCompany.connect(supplier_model.updateCompany)
        self.supplier_selector.setModel(supplier_model)

        self.reference = QLineEdit()

        layout = QFormLayout()
        layout.addRow("Supplier", self.supplier_selector)
        layout.addRow("Reference", self.reference)

        self.setLayout(layout)
