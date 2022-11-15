#!/bin/env python
"""
    Docstring
"""

# Only needed for access to command line arguments
import sys
import os

from typing import Any

from openpyxl import load_workbook
from openpyxl.worksheet._read_only import ReadOnlyWorksheet

from PyQt6.QtWidgets import (
        QApplication,
        QWidget,
        QTableWidget,
        QVBoxLayout,
        QFileDialog,
        QTableWidgetItem,
        QDialogButtonBox)

__version__ = "0.0.1"


class TableWidget(QTableWidget):
    def __init__(self, *args):
        columnList = ("barcode", "default_code", "name", "price", "cost")
        QTableWidget.__init__(self, *args)
        self.setColumnCount(len(columnList))
        self.setHorizontalHeaderLabels(columnList)

    def setItem(self, row: int, column: int, item: Any):
        if item is None:
            return
        super().setItem(row, column, QTableWidgetItem(str(item)))


class Window(QWidget):
    def searchColumn(workbook: ReadOnlyWorksheet, column_name: str):
        header_row = map(lambda x :x.value, next(workbook.rows))
        for header_column in header_row:
            pass


    def loadExcel(self):
        excelFile, _ = QFileDialog.getOpenFileName(
                self,
                'Select Excel file',
                os.getcwd(),
                "Excel files (*.xls *.xlsx *.xlsm)")
        if not excelFile:
            return
        wb = load_workbook(filename=excelFile, read_only=True, data_only=True)
        sheet = wb[wb.sheetnames[0]]  # only the first

        iter_rows = sheet.iter_rows()
        next(iter_rows)  # discard header
        for index, row in enumerate(iter_rows):
            self.mainTable.setRowCount(self.mainTable.rowCount() + 1)
            for column, item in enumerate(row):
                self.mainTable.setItem(index, column, item.value)

        wb.close()
        pass


    def mainButtonsBehaviour(self, button):
        # TODO search other way different to check the text
        if button.text() == "Apply":
            return

        if button.text() == "Open":
            self.loadExcel()
            return

        raise NotImplementedError("Unknown button")

    def __init__(self, *args):
        QWidget.__init__(self, *args)
        layout = QVBoxLayout()
        self.mainTable = TableWidget()
        mainButtons = QDialogButtonBox(
                QDialogButtonBox.StandardButton.Apply
                | QDialogButtonBox.StandardButton.Open)
        mainButtons.clicked.connect(self.mainButtonsBehaviour)
        layout.addWidget(self.mainTable)
        layout.addWidget(mainButtons)
        self.setLayout(layout)


# You need one (and only one) QApplication instance per application.
# Pass in sys.argv to allow command line arguments for your app.
# If you know you won't use command line arguments QApplication([]) works too.
app = QApplication(sys.argv)

# Create a Qt widget, which will be our window.
window = Window()

window.show()  # IMPORTANT!!!!! Windows are hidden by default.

# Start the event loop.
app.exec()
