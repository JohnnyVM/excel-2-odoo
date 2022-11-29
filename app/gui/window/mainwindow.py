from PyQt6.QtCore import qDebug, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget,
    QHeaderView,
    QVBoxLayout)

from ... import settings
from ...dependencies import get_odoo

from ..model.odoomodel import CustomOdooModel, OdooModel
from ..widget.odoocombobox import OdooComboBox
from ..widget.odootableview import OdooTableView
from ...controller.excel import FIELDS


class MainWindow(QWidget):
    _company_id: int | None = None
    changeCompany = pyqtSignal(int)

    def set_company(self, index: int) -> None:
        company_id = self.company_selector.itemData(index)
        if company_id != self._company_id:
            qDebug(f"{self.__class__.__name__}: Change company {self._company_id} -> {company_id}")
            self._company_id = company_id
            self.changeCompany.emit(company_id)

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

        product_model = CustomOdooModel(
            conn=conn,
            name='Excel load',
            domain=[[
                ('sale_ok', '=', True),
                ('purchase_ok', '=', True),
                ('active', '=', True)
            ]],
            company_id=self.company_selector.currentData(),
            fields=FIELDS)
        # fields=(
        #     'barcode',
        #     'default_code',
        #     'name',
        #     'categ_id',
        #     'taxes_id',
        #     'list_price'))
        self.changeCompany.connect(product_model.updateCompany)
        self.purchaseTable = OdooTableView(parent=self)
        self.purchaseTable.setModel(product_model)
        self.purchaseTable.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        layout = QVBoxLayout()
        layout.addWidget(self.company_selector)
        layout.addWidget(self.purchaseTable)

        self.setLayout(layout)
