from PyQt6 import QtCore


class OdooModel(QtCore.QAbstractTableModel):
    """
        Basic odoo model
        Auto load the spected info

        Note: When subclassing QAbstractTableModel, you must implement
        rowCount(), columnCount(), and data().
        Well behaved models will also implement headerData().
    """
    _odoo_model_name: str

    def __init__(self, model_name: str, **kwargs):
        """
            kwargs: fields: list[str] list of lields to load
        """
        QtCore.QAbstractTableModel.__init__()
        self._odoo_model_name = model_name

    def update(self, dataIn):
        self.datatable = dataIn

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self.datatable.index)

    def columnCount(self, parent=QtCore.QModelIndex()):
        return len(self.datatable.columns.values)

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.DisplayRole:
            i = index.row()
            j = index.column()
            return '{0}'.format(self.datatable.iget_value(i, j))
        else:
            return QtCore.QVariant()

    def flags(self, index):
        return QtCore.Qt.ItemIsEnabled
