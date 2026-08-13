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
        self._column_selection = None
        self._column_sources = None
        self._available_fields = None

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

    def availableColumnNames(self) -> tuple[str, ...]:
        """Return Odoo fields available as output keys."""
        return tuple((self._available_fields or self._fields).keys())

    def columnSelection(self) -> tuple[str | None, ...]:
        """Return the source field selected for each displayed column."""
        if self._column_selection is None:
            return self.availableColumnNames()
        return tuple(self._column_selection)

    def _column_source(self, column: int) -> str:
        if self._column_sources is None:
            return self.availableColumnNames()[column]
        return self._column_sources[column]

    def _field_attributes(self, field: str) -> dict:
        return (self._available_fields or self._fields)[field]

    def setColumnSelection(self, column: int, field: str | None) -> bool:
        """Change the output key without changing the displayed values."""
        available = self.availableColumnNames()
        if column < 0 or column >= len(available) or (field is not None and field not in available):
            return False
        if self._column_selection is None:
            self._column_selection = list(available)
        self._column_selection[column] = field
        self.headerDataChanged.emit(Qt.Orientation.Horizontal, column, column)
        return True

    def exportFields(self) -> dict:
        """Return only selected output keys, while leaving the table untouched."""
        return {
            field: self._field_attributes(field)
            for field in self.columnSelection()
            if field is not None
        }

    def exportData(self) -> list[dict]:
        """Return selected rows mapped to output keys without deleting source values."""
        selection = self.columnSelection()
        sources = self._column_sources or self.availableColumnNames()
        return [
            {
                field: row.get(source)
                for field, source in zip(selection, sources)
                if field is not None
            }
            for row in self._data
        ]

    def applyColumnSelection(self) -> None:
        """Remove ignored columns and rebuild rows using the chosen columns."""
        selection = self.columnSelection()
        original_fields = self._fields
        original_data = self._data
        sources = self._column_sources or self.availableColumnNames()
        selected = [
            (field, self._field_attributes(field), source)
            for field, source in zip(selection, sources)
            if field is not None
        ]
        self.beginResetModel()
        self._fields = {field: attributes for field, attributes, _ in selected}
        self._data = [
            {field: row.get(source) for field, _, source in selected}
            for row in original_data
        ]
        self._column_selection = list(self._fields.keys())
        self._column_sources = list(self._fields.keys())
        self.endResetModel()

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
            field_name = self.columnSelection()[index.column()]
            if field_name is None:
                return None
            return self._data[index.row()][self._column_source(index.column())]

        return QVariant()

    def setData(self, index: QModelIndex, value: QVariant, role: int = ...):
        if not index.isValid():
            return False
        field_name = self.columnSelection()[index.column()]
        if field_name is None:
            return False
        self._data[index.row()][self._column_source(index.column())] = value
        self.dataChanged.emit(index, index, (role,))
        return True

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = ...) -> Any:
        if orientation == Qt.Orientation.Horizontal:
            if section > self.columnCount():
                raise IndexError()

            if role == Qt.ItemDataRole.DisplayRole:
                field_name = self.columnSelection()[section]
                if field_name is None:
                    return 'Ignored column'
                field = self._field_attributes(field_name)
                return field.get('string', field_name)

            if role == Qt.ItemDataRole.ToolTipRole:
                field_name = self.columnSelection()[section]
                if field_name is None:
                    return 'This column will be ignored when applying the import.'
                return self._fields[field_name].get('help', '')

            if role == Qt.ItemDataRole.UserRole:
                name = self.columnSelection()[section]
                if name is None:
                    return {}
                return {name: self._field_attributes(name)}

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
