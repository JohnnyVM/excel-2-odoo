from typing import Any

from PyQt6.QtCore import QAbstractTableModel, QObject, QModelIndex, Qt, qInfo, QVariant

import odoorpc


class OdooModel(QAbstractTableModel):
    """ Docstring """
    _name: str
    _conn: odoorpc.ODOO
    domain: list = [[]]
    _fields: dict
    __data: list[dict]

    def __init__(
        self, conn: odoorpc.ODOO, name: str, parent: QObject = None, **kwargs):
        """ """
        QAbstractTableModel.__init__(self, parent)
        self._name = name
        self._conn = conn

        if 'domain' in kwargs:
            self.domain = kwargs['domain']

        fields = []
        if 'fields' in kwargs:
            fields = kwargs['fields']

        qInfo(f"{self.__class__.__name__}: {self._name} fields_get {fields}")
        self._fields = self._conn.execute_kw(self._name, 'fields_get', [fields], {})
        self._load()

    def _load(self):
        search_fields = tuple(field for field in self._fields.keys())
        qInfo(f"{self.__class__.__name__}: {self._name} search_read {self.domain} {search_fields}")
        self.__data = self._conn.execute_kw(self._name, "search_read", self.domain, {'fields': search_fields})
    
    def columnCount(self, parent: QModelIndex = ...) -> int:
        return len(self._fields)

    def rowCount(self, index: QModelIndex = ...) -> int:
        return len(self.__data)

    def data(self, index: QModelIndex, role: int = ...) -> Any:
        if not index.isValid():
            return QVariant()
        if role == Qt.ItemDataRole.DisplayRole:
            field_name = tuple(self._fields.keys())[index.column()]
            return self.__data[index.row()][field_name]

        return QVariant()

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = ...) -> Any:
        if orientation == Qt.Orientation.Horizontal:
            if section > self.columnCount():
                raise IndexError()
            if role == Qt.DisplayRole:
                return tuple(field for field in self._fields)[section]

        if orientation == Qt.Orientation.Vertical:
            if section > self.rowCount():
                raise IndexError()
                

        return super().headerData(section, orientation, role)
