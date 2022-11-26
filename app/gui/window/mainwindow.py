from PyQt6.QtWidgets import (
        QWidget,
        QVBoxLayout)

from ... import settings
from ...dependencies import get_odoo

from ..model.odoomodel import OdooModel
from ..widget.odoocombobox import OdooComboBox


class MainWindow(QWidget):
    def __init__(self, parent: QWidget = None):
        QWidget.__init__(self, parent)

        conn = get_odoo(settings.conf)

        self.company = OdooComboBox()
        company_model = OdooModel(conn=conn, name='res.company', fields=('id', 'display_name'))
        self.company.setModel(company_model)

        layout = QVBoxLayout()
        layout.addWidget(self.company)

        self.setLayout(layout)