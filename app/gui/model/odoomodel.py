import concurrent.futures
from threading import Event
from typing import Any
from copy import deepcopy
from itertools import repeat

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
    TODO:
        - cache field_get operation
    """
    name: str = None
    _conn: odoorpc.ODOO
    domain: list = [[]]
    _fields: dict = {}
    _data: list[dict] = []
    _relational_model: dict[str, 'OdooModel'] = {}
    company_id: int | None = None

    def __company_related(self, model: str) -> bool:
        if not model:
            return False
        # Hackish
        # Fields as taxes_id can have multiple values per company
        # in the current implementation allow only one company
        qInfo(f"{self.__class__.__name__}({self.name}): fields_get {{}}")
        fields = self._conn.execute_kw(model, 'fields_get', [], {})
        return 'company_id' in fields.keys()

    def __init__(self, conn: odoorpc.ODOO, parent: QObject = None, autoload: bool = True, **kwargs):
        """ """
        QAbstractTableModel.__init__(self, parent)
        self._conn = conn

        if 'domain' in kwargs:
            self.domain = kwargs['domain']

        if 'company_id' in kwargs:
            self.company_id = kwargs['company_id']

        fields = []
        if 'fields' in kwargs:
            fields = kwargs['fields']

        if 'name' in kwargs:
            self.name = kwargs['name']

        if autoload:
            qInfo(str(f"{self.__class__.__name__}({self.name}): fields_get {fields}".encode('utf-8')))
            self._fields = self._conn.execute_kw(
                self.name,
                'fields_get',
                [fields])
            self._loadRelationalData()
            self._load()

    def _loadRelationalField(self, field: str, **value) -> dict:
        search_fields = ('id', 'display_name')
        domain = []
        if 'domain' in value:
            domain = value['domain']

        qInfo(f"{self.name}: Relation {value['relation']} search_read {value['domain']} {search_fields}")
        relational_model = self._conn.execute_kw(
            value['relation'],
            "search_read",
            domain,
            {'fields': search_fields})
        n_records = len(relational_model)
        qDebug(f"{self.name}: Fetched {n_records} records from relation {value['relation']}")
        return relational_model

    @staticmethod
    def __wrap_thread(event, parent, field: str, attributes: dict):
        """ Wrap for call event """
        if not event.is_set():
            attr = deepcopy(attributes)
            if parent.company_id and (parent.__company_related(attributes.get('relation', None)) or attributes.get('company_dependent', False)):
                if 'domain' not in attr:
                    attr['domain'] = []
                attr['domain'].extend(['|', ('company_id', '=', parent.company_id), ('company_id', '=', False)])
                attr['domain'] = (attr['domain'],)
            parent._relational_model[field] = OdooModel(
                conn=parent._conn,
                name=attr['relation'],
                domain=attr.get('domain', []),
                fields=('id', 'display_name'))
            column = [f for f in parent._fields.keys()].index(field)
            nrows = parent.rowCount()
            parent.dataChanged.emit(
                parent.index(0, column),
                parent.index(nrows, column),
                [])

    def _loadRelationalData(self):
        futures = []
        event = Event()
        with concurrent.futures.ThreadPoolExecutor() as exec:
            for field, attributes in self._fields.items():
                if 'relation' in attributes:
                    # OdooModel.__wrap_thread(event, self, field, attributes)
                    future = exec.submit(OdooModel.__wrap_thread, event, self, field, attributes)
                    futures.append(future)
                done, not_done = concurrent.futures.wait(futures, return_when=concurrent.futures.FIRST_EXCEPTION)
                if len(done) > 0 and len(done) != len(futures):
                    future = done.pop()
                    if future.exception() is not None:
                        for future in futures:
                            future.cancel()
                        event.set()

    def _load(self, domain=None):
        search_fields = tuple(field for field in self._fields.keys())
        qInfo(f"{self.__class__.__name__}({self.name}): search_read {self.domain} {search_fields}")
        new_domain = list(deepcopy(self.domain))
        if domain:
            new_domain[0].extend(domain[0])
        self._data = self._conn.execute_kw(
            self.name,
            "search_read",
            new_domain,
            {'fields': search_fields})
        n_records = len(self._data)
        qDebug(f"{self.__class__.__name__}({self.name}): Fetched {n_records} records")
        self._loadRelationalData()
        self.dataChanged.emit(
            self.index(0, 0),
            self.index(n_records, len(search_fields)),
            [])

    def columnCount(self, parent: QModelIndex = ...) -> int:
        return len(self._fields)

    def removeColumns(self, column: int, count: int, parent: QModelIndex = QModelIndex()):
        keys = tuple(self._fields.keys())[column: column + count]
        self.beginRemoveColumns(parent, column, column + count - 1)
        for key in keys:
            del self._fields[key]
        self.endRemoveColumns()
        return True

    def rowCount(self, index: QModelIndex = ...) -> int:
        return len(self._data)

    def insertRows(self, row: int, count: int, parent: QModelIndex = QModelIndex()):
        res = dict(zip(self._fields.keys(), repeat(None)))
        self.beginInsertRows(parent, row, row + count - 1)
        for _ in repeat(None, count):
            self._data.insert(row, deepcopy(res))
        self.endInsertRows()
        return True

    def data(self, index: QModelIndex, role: int = ...) -> Any:
        if not index.isValid():
            return QVariant()

        if role == Qt.ItemDataRole.DisplayRole\
                or role == Qt.ItemDataRole.EditRole:
            field_name = tuple(self._fields.keys())[index.column()]
            return self._data[index.row()][field_name]

        return QVariant()

    def setData(self, index: QModelIndex, value: QVariant, role: int = ...):
        if not index.isValid():
            return False
        field_name = tuple(self._fields.keys())[index.column()]
        self._data[index.row()][field_name] = value
        self.dataChanged.emit(index, index, (role,))
        return True

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = ...) -> Any:
        if orientation == Qt.Orientation.Horizontal:
            if section > self.columnCount():
                raise IndexError()

            if role == Qt.ItemDataRole.DisplayRole:
                name = tuple(field for field in self._fields.values())[section]
                return tuple(field for field in self._fields.values())[section].get('string', name)

            if role == Qt.ItemDataRole.ToolTipRole:
                return tuple(field for field in self._fields.values())[section].get('help', '')

            if role == Qt.ItemDataRole.UserRole:
                name = tuple(field for field in self._fields.keys())[section]
                return {name: self._fields[name]}

        if orientation == Qt.Orientation.Vertical:
            if section > self.rowCount():
                raise IndexError()

        return super().headerData(section, orientation, role)

    def setHeaderData(self, section: int, orientation: Qt.Orientation, value: QVariant, role: int = ...) -> Any:
        if orientation == Qt.Orientation.Horizontal:
            if section > self.columnCount():
                raise IndexError()

            if role == Qt.ItemDataRole.DisplayRole:
                tuple(field for field in self._fields.values())[section]\
                    .update({'string': value})

            if role == Qt.ItemDataRole.ToolTipRole:
                tuple(field for field in self._fields.values())[section]\
                    .update({'help': value})

            if role == Qt.ItemDataRole.UserRole:
                name = tuple(field for field in self._fields.keys())[section]
                self._fields.update({name: value})

            self.headerDataChanged(orientation, section, section)
            return True

        if orientation == Qt.Orientation.Vertical:
            if section > self.rowCount():
                raise IndexError()

        return super().setHeaderData(section, orientation, role)

    def addField(self, name: str, attributes: dict[str, str]) -> bool:
        count = self.columnCount()
        self.beginInsertColumns(None, count, count)
        self._fields[name] = attributes
        self.endInsertColumn()
        return True

    def fieldNameColumn(self, name: str) -> int:
        """ Helper to return the column index by name """
        return tuple(self._fields.keys()).index(name)

    def flags(self, index: QModelIndex):
        return Qt.ItemFlag.ItemIsEditable\
            | Qt.ItemFlag.ItemIsEnabled\
            | Qt.ItemFlag.ItemIsSelectable

    def updateCompany(self, newcompany_id: int):
        """ TODO: the own records should be updated if company change """
        if newcompany_id != self.company_id:
            if self.name:
                model_fields = self._conn.execute_kw(
                    self.name,
                    'fields_get',
                    [], {'attributes': ['string']})
                if 'company_id' in model_fields.keys():
                    self._load(domain=[['|', ('company_id', '=', newcompany_id), ('company_id', '=', False)]])
            qDebug(f"{self.name}: Change company {self.company_id} -> {newcompany_id}")
            self.company_id = newcompany_id
            futures = []
            event = Event()
            with concurrent.futures.ThreadPoolExecutor() as exec:
                for field, attributes in self._fields.items():
                    if self.company_id and (self.__company_related(attributes.get('relation', None)) or attributes.get('company_dependent', False)):
                        future = exec.submit(OdooModel.__wrap_thread, event, self, field, attributes)
                        futures.append(future)
                    done, not_done = concurrent.futures.wait(futures, return_when=concurrent.futures.FIRST_EXCEPTION)
                    if len(done) > 0 and len(done) != len(futures):
                        future = done.pop()
                        if future.exception() is not None:
                            for future in futures:
                                future.cancel()
                            event.set()
