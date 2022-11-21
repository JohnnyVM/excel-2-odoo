from typing import Any
from PyQt6.QtCore import qInfo
from PyQt6.QtWidgets import (
        QTableWidget,
        QTableWidgetItem)

from .. import schema
from .. import settings
from ..dependencies import get_odoo
from .odoocombobox import OdooComboBox


class TableWidget(QTableWidget):
    headerNames = (
            "barcode", "default_code", "name", "list_price", "standard_price")
    comboHeaderNames = {
            "taxes_id": "account.tax",
            "supplier_taxes_id": "account.tax",
            "categ_id": "product.category"}
    __envList: dict = {}  # OdooComboBox table cache

    def _updateComboColumn(self, column, userData: int):
        for row in range(self.rowCount()):
            combo = self.cellWidget(row, column)
            idx = combo.findData(userData)
            combo.setCurrentIndex(idx)

    def update_sales_column(self, userData: int):
        self._updateComboColumn(5, userData)

    def update_purchase_column(self, userData: int):
        self._updateComboColumn(6, userData)

    def update_category_column(self, userData: int):
        self._updateComboColumn(7, userData)

    def __init__(self, *args):
        QTableWidget.__init__(self, *args)
        len_hn = len(self.headerNames)
        len_chn = len(self.comboHeaderNames)
        self.setColumnCount(len_hn + len_chn)
        self.setHorizontalHeaderLabels(
                self.headerNames + tuple(self.comboHeaderNames.keys()))

        odoo = get_odoo(settings.conf)
        for key, value in self.comboHeaderNames.items():
            #fields = odoo.execute_kw(
            #        key, 'fields_get', [], {'attributes': []})
            #if 'company_id' in fields:
            #    domain = [('company_id', '=', )]
            domain = []
            if value not in self.__envList:
                self.__envList[value] = []
                ids = odoo.env[value].search([])
                qInfo("Loading model:"
                      " {name} with domain {domain} records: {ids}"
                      .format(name=value, domain=domain, ids=ids))
                models = odoo.execute_kw(
                            value,
                            'read',
                            [ids], {'fields': ['id', 'display_name']})
                for m in models:
                    cls = getattr(
                            schema, schema.OdooModel.odooClassName(value))
                    self.__envList[value].append(cls(**m))

    def setItem(self, row: int, column: int, item: Any):
        if item is None:
            return
        super().setItem(row, column, QTableWidgetItem(str(item)))

    def rowEmpty(self, row: int):
        for i in range(self.columnCount()):
            if self.item(row, i) is not None:
                return False
        return True

    def rowAt(self, row: int):
        return [self.item(row, column) for column in range(self.columnCount())]

    def columnAt(self, column: int):
        return [self.item(row, column) for row in range(self.rowCount())]

    def headers(self):
        return [self.horizontalHeaderItem(idx)
                for idx in range(len(self.headerNames))]

    def setRowCount(self, rows: int):
        """ Add by default the column iva provider, iva sales and category """
        current_rows = super().rowCount()
        super().setRowCount(rows)
        if current_rows >= rows:
            return

        len_hn = len(self.headerNames)
        len_chn = len(self.comboHeaderNames)
        for row in range(current_rows, rows, 1):
            i = 0
            items = tuple(self.comboHeaderNames.items())

            for column in range(len_hn, len_hn+len_chn, 1):
                combo = OdooComboBox(items[i][1])
                combo.loadModels(self.__envList[items[i][1]])
                self.setCellWidget(row, column, combo)
                i += 1
