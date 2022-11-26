from PyQt6.QtWidgets import QTableView


class OdooTableView(QTableView):
    def __init__(self, parent=None):
        QTableView.__init__(parent)