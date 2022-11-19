#!/bin/env python
"""
    Docstring
"""

# Only needed for access to command line arguments
import sys
import configparser

from PyQt6.QtWidgets import QApplication

from app.widget import mainWindow
from app.settings import Settings

DEFAULT_CONFIG_FILE = 'config.ini'

__version__ = "0.0.2"


if __name__ == "__main__":
    # Start the app

    # necesary
    app = QApplication(sys.argv)
    app.setApplicationVersion(__version__)
    app.setApplicationName("excel-2-odoo")

    # settings
    config = configparser.ConfigParser()
    config.read(DEFAULT_CONFIG_FILE)

    settings = Settings(config=config)

    window = mainWindow.MainWindow(settings)
    window.show()  # IMPORTANT!!!!! Windows are hidden by default.

    sys.exit(app.exec())
