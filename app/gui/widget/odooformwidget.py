from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QLineEdit,
    QWidget,
    QFormLayout)

from ... import settings
from ...dependencies import get_odoo
from ..model.odoomodel import OdooModel
from ..widget.odoocombobox import OdooComboBox


class OdooFormWidget(QWidget):
    """
    TODO: Automatically load a form widget
    """
    changeCompany = pyqtSignal(int)
    __model: OdooModel = None
    fields: list[str] = []

    def __init__(self, parent: QWidget = None):
        QWidget.__init__(self, parent)
        conn = get_odoo(settings.conf)
        self.supplier_selector = OdooComboBox(parent=self)
        supplier_model = OdooModel(
            conn=conn,
            name='res.partner',
            domain=(
                [
                    ('vat', '!=', False),
                    ('company_type', '=', 'company'),
                    '|',
                    ('company_id', '=', False),
                    ('company_id', '=', parent.company_id)
                ],
            ),
            fields=('id', 'display_name'))
        self.changeCompany.connect(supplier_model.updateCompany)
        self.supplier_selector.setModel(supplier_model)
        self.company_id = getattr(parent, "company_id", None)
        self.changeCompany.connect(self._set_company)

        self.reference = QLineEdit()

        layout = QFormLayout()
        layout.addRow("Supplier", self.supplier_selector)
        layout.addRow("Reference", self.reference)

        self.setLayout(layout)

    def model(self):
        # return self.__model
        values = {
            '_data': [{
                'partner_id': self.supplier_selector.currentData(),
                'partner_ref': self.reference.text(),
                'state': 'draft'
            }]
        }
        if self.company_id is not None:
            values['_data'][0]['company_id'] = self.company_id
        return values

    def _set_company(self, company_id: int):
        self.company_id = company_id

    def setModel(self, model: OdooModel):
        self.__model = model
