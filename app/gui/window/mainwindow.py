from PyQt6.QtCore import qDebug
from PyQt6.QtWidgets import (
        QWidget,
        QVBoxLayout)

from ... import settings
from ...dependencies import get_odoo

from ..model.odoomodel import OdooModel
from ..widget.odoocombobox import OdooComboBox


class MainWindow(QWidget):
    _company_id: int | None = None

    def set_company(self, index: int) -> None:
        company_id = self.company_selector.itemData(index)
        if company_id != self._company_id:
            qDebug(f"{self.__class__.__name__}: Change company {self._company_id} -> {company_id}")
            self._company_id = company_id

    def __init__(self, parent: QWidget = None):
        QWidget.__init__(self, parent)

        conn = get_odoo(settings.conf)

        self.company_selector = OdooComboBox(parent=self)
        company_model = OdooModel(
            conn=conn,
            name='res.company',
            fields=('id', 'display_name'))
        self.company_selector.currentIndexChanged.connect(self.set_company)
        self.company_selector.setModel(company_model)

        layout = QVBoxLayout()
        layout.addWidget(self.company_selector)

        self.setLayout(layout)
