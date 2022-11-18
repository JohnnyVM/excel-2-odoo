#!/bin/env python
"""
    Docstring
"""

# Only needed for access to command line arguments

from configparser import ConfigParser
from PyQt6.QtWidgets import QApplication


from settings import Settings
from widget import mainWindow


__version__ = "0.0.1"

DEFAULT_CONFIG_FILE='config.ini'


# You need one (and only one) QApplication instance per application.
# Pass in sys.argv to allow command line arguments for your app.
# If you know you won't use command line arguments QApplication([]) works too.
app = QApplication([])
app.setApplicationVersion(__version__)
app.setApplicationName("excel-2-odoo")

if __name__=="__main__":
    config = ConfigParser()
    config.read(DEFAULT_CONFIG_FILE)

    settings = Settings(config=config)

    # Create a Qt widget, which will be our window.
    window = mainWindow.MainWindow(settings=settings)

    window.show()  # IMPORTANT!!!!! Windows are hidden by default.

    # Start the event loop.
    app.exec()
