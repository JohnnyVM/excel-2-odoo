from PyQt6.QtWidgets import QTableView


class OdooTable(QTableView):
    def __init__(self, parent=None):
        QTableView.__init__(parent)
