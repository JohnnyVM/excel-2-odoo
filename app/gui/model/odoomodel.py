import concurrent.futures
from typing import Any
from functools import partial

from PyQt6.QtCore import (
    QAbstractTableModel,
    QObject,
    QModelIndex,
    Qt,
    qInfo,
    qDebug,
    QVariant)

import odoorpc


class OdooModel(QAbstractTableModel):
    """
    Load odoo Model data and relations
    """
    _name: str
    _conn: odoorpc.ODOO
    domain: list = [[]]
    _fields: dict
    _data: list[dict]
    _relational_data: dict = {}
    _company_id: int | None

    def __init__(self, conn: odoorpc.ODOO, name: str, parent: QObject = None, **kwargs):
        """ """
        QAbstractTableModel.__init__(self, parent)
        self._name = name
        self._conn = conn

        if 'domain' in kwargs:
            self.domain = kwargs['domain']

        if 'company_id' in kwargs:
            self._company_id = kwargs['company_id']

        fields = []
        if 'fields' in kwargs:
            fields = kwargs['fields']

        qInfo(f"{self.__class__.__name__}: {self._name} fields_get {fields}")
        self._fields = self._conn.execute_kw(
            self._name,
            'fields_get',
            [fields])
        self._load()
        self._loadRelationalData()

    def _loadRelationalField(self, field: str, **value) -> dict:
        search_fields = ('id', 'display_name')
        domain = []
        if value['company_dependent'] and self._company_id:
            field_domain = value['domain'][0] if value['domain'] else [[]]
            domain = [field_domain + [('company_id', '=', self._company_id)]]
        qInfo(f"{self.__class__.__name__}: Relation {value['relation']} search_read {value['domain']} {search_fields}")
        relational_model = self._conn.execute_kw(
            value['relation'],
            "search_read",
            domain,
            {'fields': search_fields})
        n_records = len(relational_model)
        qDebug(f"{self.__class__.__name__}: Fetched {n_records} records from relation {value['relation']}")
        return relational_model

    def _loadRelationalData(self):
        def update_relational_data(relational, idx, future):
            relational[idx] = future.result()

        futures = []
        with concurrent.futures.ThreadPoolExecutor() as exec:
            for field, attributes in self._fields.items():
                if 'relation' in attributes:
                    future = exec.submit(self._loadRelationalField, field, **attributes)
                    future.add_done_callback(partial(
                        update_relational_data,
                        self._relational_data,
                        field))
                    futures.append(future)

        for future in futures:
            if future.exception():
                raise future.exception()

    def _load(self):
        search_fields = tuple(field for field in self._fields.keys())
        qInfo(f"{self.__class__.__name__}: {self._name} search_read {self.domain} {search_fields}")
        self._data = self._conn.execute_kw(
            self._name,
            "search_read",
            self.domain,
            {'fields': search_fields})
        n_records = len(self._data)
        qDebug(f"{self.__class__.__name__}: Fetched {n_records} records from {self._name}")

    def columnCount(self, parent: QModelIndex = ...) -> int:
        return len(self._fields)

    def rowCount(self, index: QModelIndex = ...) -> int:
        return len(self._data)

    def data(self, index: QModelIndex, role: int = ...) -> Any:
        if not index.isValid():
            return QVariant()

        if role == Qt.ItemDataRole.DisplayRole:
            field_name = tuple(self._fields.keys())[index.column()]
            return self._data[index.row()][field_name]

        return QVariant()

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = ...) -> Any:
        if orientation == Qt.Orientation.Horizontal:
            if section > self.columnCount():
                raise IndexError()

            if role == Qt.ItemDataRole.DisplayRole:
                return tuple(field for field in self._fields.values())[section]['string']

        if orientation == Qt.Orientation.Vertical:
            if section > self.rowCount():
                raise IndexError()

        return super().headerData(section, orientation, role)

    def fieldNameColumn(self, name: str) -> int:
        """ Helper to return the column index by name """
        return tuple(self._fields.keys()).index(name)
