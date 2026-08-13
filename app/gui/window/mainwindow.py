import os

from PyQt6.QtCore import qDebug, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget,
    QFileDialog,
    QDialogButtonBox,
    QVBoxLayout,
    QTabWidget)

from ... import settings
from ...dependencies import get_odoo

from ..model.odoomodel import OdooModel
from ..widget.odoocombobox import OdooComboBox
from ..widget.odootableview import OdooTableView
from ..widget.odooformwidget import OdooFormWidget
from ...controller.purchase import create_purchase_order
from ...controller.factorymodel import factoryExcelOdooModel
from ...controller.model2odoo import (
    valid_model,
    create_products_from_model,
    update_products_from_model)
from ..widget.productformwidget import ProductFormWidget


class MainWindow(QWidget):
    company_id: int | None = None
    changeCompany = pyqtSignal(int)
    loadExcel = pyqtSignal(str)
    __update_company_connection = None

    def mainButtonsBehaviour(self, button):
        # TODO search other way different to check the text
        if button.text() == "Apply":
            model = self.purchaseTable.model()
            if not model:
                return
            if not valid_model(model):
                return
            create_products_from_model(model)
            update_products_from_model(model)
            create_purchase_order(model._conn, self.supplier_form.model(), model)
            return

        if button.text() == "Open":
            excelfile, _ = QFileDialog.getOpenFileName(
                self,
                'Select spreadsheet file',
                os.getcwd(),
                "Spreadsheet files (*.xlsx *.xlsm *.csv);;Excel files (*.xlsx *.xlsm);;CSV files (*.csv)")
            if not excelfile:
                return
            model = factoryExcelOdooModel(excelfile, self)
            if not model:
                return
            if self.__update_company_connection:
                self.changeCompany.disconnect(self.__update_company_connection)
            self.__update_company_connection = self.changeCompany.connect(model.updateCompany)
            self.purchaseTable.setModel(model)
            return

        raise NotImplementedError("Unknown button")

    def set_company(self, index: int) -> None:
        company_id = self.company_selector.itemData(index)
        if company_id != self.company_id:
            qDebug(f"{self.__class__.__name__}: Change company {self.company_id} -> {company_id}")
            self.company_id = company_id
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

        self.supplier_form = OdooFormWidget(parent=self)
        self.changeCompany.connect(self.supplier_form.changeCompany)

        self.mainButtons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Apply | QDialogButtonBox.StandardButton.Open)

        self.purchaseTable = OdooTableView(parent=self)
        self.purchaseTable.horizontalHeader().setStretchLastSection(True)
        self.mainButtons.clicked.connect(self.mainButtonsBehaviour)

        purchase_tab = QWidget(self)
        purchase_layout = QVBoxLayout(purchase_tab)
        purchase_layout.addWidget(self.company_selector)
        purchase_layout.addWidget(self.supplier_form)
        purchase_layout.addWidget(self.purchaseTable)
        purchase_layout.addWidget(self.mainButtons)

        tabs = QTabWidget(self)
        tabs.addTab(purchase_tab, "Purchase import")
        tabs.addTab(ProductFormWidget(self), "Create product")

        layout = QVBoxLayout(self)
        layout.addWidget(tabs)
        self.setLayout(layout)
