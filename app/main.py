#!/bin/env python
"""
    Docstring
"""

# Only needed for access to command line arguments
import sys
import logging

from PyQt6.QtWidgets import (
        QApplication,
        QWidget,
        QTableWidget,
        QVBoxLayout,
        QDialogButtonBox)

__version__ = "0.0.1"

logger = logging.getLogger(__name__)
columnList = ("barcode", "name", "price", "cost")

class TableView(QTableWidget):
    def __init__(self, *args):
        QTableWidget.__init__(self, *args)
        columnNumber = len(columnList)
        self.setColumnCount(columnNumber)
        self.setHorizontalHeaderLabels(columnList)


class Window(QWidget):
    def __init__(self, *args):
        QWidget.__init__(self, *args)
        layout = QVBoxLayout()
        table = TableView()
        mainButtons = QDialogButtonBox(
                QDialogButtonBox.StandardButton.Apply
                | QDialogButtonBox.StandardButton.Open)
        mainButtons.clicked.connect(self.mainButtonsBehaviour)
        layout.addWidget(table)
        layout.addWidget(mainButtons)
        self.setLayout(layout)

    def mainButtonsBehaviour(self, button):
        # TODO search other way
        if button.text() == "Apply":
            logger.info("click 1")
            return

        if button.text() == "Open":
            logger.info("click 2")
            return

        raise NotImplementedError("Unknown button")


# You need one (and only one) QApplication instance per application.
# Pass in sys.argv to allow command line arguments for your app.
# If you know you won't use command line arguments QApplication([]) works too.
app = QApplication(sys.argv)

# Create a Qt widget, which will be our window.
window = Window()

window.show()  # IMPORTANT!!!!! Windows are hidden by default.

# Start the event loop.
app.exec()
