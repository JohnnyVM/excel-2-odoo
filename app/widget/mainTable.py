from typing import Any

from PyQt6.QtWidgets import (
        QTableWidget,
        QComboBox,
        QTableWidgetItem)


class ComboWidget(QComboBox):
    """ """

    def loadItems(self):
        self.addItem("test 1", userData=1)
        self.addItem("test 3", userData=3)

    def __init__(self, name: str, fields: tuple[str]):
        QComboBox.__init__(self)
        self.loadItems()


class TableWidget(QTableWidget):
    headerNames = (
            "barcode", "default_code", "name", "list_price", "standard_price")
    comboHeaderNames = ("taxes_id", "supplier_taxes_id", "categ_id")

    def __init__(self, *args):
        QTableWidget.__init__(self, *args)
        len_hn = len(self.headerNames)
        len_chn = len(self.comboHeaderNames)
        self.setColumnCount(len_hn + len_chn)
        self.setHorizontalHeaderLabels(
                self.headerNames + self.comboHeaderNames)

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
        """ Add by default the column iva_provider, iva sales and category """
        current_rows = super().rowCount()
        super().setRowCount(rows)
        if current_rows >= rows:
            return

        len_hn = len(self.headerNames)
        len_chn = len(self.comboHeaderNames)
        for row in range(current_rows, rows, 1):
            for column in range(len_hn, len_hn+len_chn+1, 1):
                self.setCellWidget(row, column, ComboWidget("lal", ("trara",)))
