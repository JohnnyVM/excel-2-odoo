import os

from PyQt6.QtCore import qDebug, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget,
    QHeaderView,
    QFileDialog,
    QDialogButtonBox,
    QVBoxLayout)

from ... import settings
from ...dependencies import get_odoo

from ..model.odoomodel import OdooModel
from ..widget.odoocombobox import OdooComboBox
from ..widget.odootableview import OdooTableView
from ...controller import FIELDS, factoryExcelOdooModel


class MainWindow(QWidget):
    _company_id: int | None = None
    changeCompany = pyqtSignal(int)
    loadExcel = pyqtSignal(str)

    def mainButtonsBehaviour(self, button):
        # TODO search other way different to check the text
        if button.text() == "Apply":
            raise NotImplementedError()

        if button.text() == "Open":
            excelfile, _ = QFileDialog.getOpenFileName(
                self,
                'Select Excel file',
                os.getcwd(),
                "Excel files (*.xlsx *.xlsm)")
            model = factoryExcelOdooModel(excelfile)
            self.purchaseTable.setModel(model)
            return

        raise NotImplementedError("Unknown button")

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

        self.mainButtons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Apply | QDialogButtonBox.StandardButton.Open)
        self.mainButtons.clicked.connect(self.mainButtonsBehaviour)

        product_model = OdooModel(
            conn=conn,
            name='Excel load',
            company_id=self.company_selector.currentData(),
            autoload=False,
            fields=FIELDS)
        self.changeCompany.connect(product_model.updateCompany)
        self.purchaseTable = OdooTableView(parent=self)
        self.purchaseTable.setModel(product_model)
        self.purchaseTable.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        layout = QVBoxLayout()
        layout.addWidget(self.company_selector)
        layout.addWidget(self.purchaseTable)
        layout.addWidget(self.mainButtons)

        self.setLayout(layout)
