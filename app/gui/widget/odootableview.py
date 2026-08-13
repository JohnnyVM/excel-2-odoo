from PyQt6.QtCore import QPoint, Qt, pyqtSignal
from PyQt6.QtWidgets import QComboBox, QHeaderView, QTableView

from ..model.odoomodel import OdooModel
from .delegate.odoocomboboxdelegate import OdooMany2OneDelegate, OdooMany2ManyDelegate


class _ColumnSelectorHeader(QHeaderView):
    clickedSection = pyqtSignal(int, QPoint)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            position = event.position().toPoint()
            section = self.logicalIndexAt(position)
            if section >= 0:
                start = self.sectionViewportPosition(section)
                width = self.sectionSize(section)
                # Leave the resize handle to QHeaderView. Normal header
                # clicks continue to open the field selector.
                near_boundary = abs(position.x() - start) <= 5 or abs(position.x() - (start + width)) <= 5
                if not near_boundary:
                    self.clickedSection.emit(section, position)
                    return
        super().mousePressEvent(event)


class OdooTableView(QTableView):

    def __init__(self, parent=None):
        QTableView.__init__(self, parent)
        self._column_header = _ColumnSelectorHeader(Qt.Orientation.Horizontal, self)
        self._column_header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.setHorizontalHeader(self._column_header)
        self._selector = None

    def setModel(self, model: OdooModel):
        old_model = self.model()
        try:
            self._column_header.clickedSection.disconnect(self._show_column_selector)
        except TypeError:
            pass
        if old_model:
            old_model.removeRows(0, old_model.rowCount())
        super().setModel(model)
        self._column_header.clickedSection.connect(self._show_column_selector)
        for column in range(model.columnCount()):
            field = model.headerData(column, Qt.Orientation.Horizontal, Qt.ItemDataRole.UserRole)
            if not field:
                continue
            attributes = tuple(field.values())[0]
            if 'relation' in attributes and attributes['type'] == 'many2one':
                self.setItemDelegateForColumn(column, OdooMany2OneDelegate(parent=self))
            if 'relation' in attributes and attributes['type'] == 'many2many':
                self.setItemDelegateForColumn(column, OdooMany2ManyDelegate(parent=self))

    def _show_column_selector(self, column: int, position: QPoint):
        if not self.model():
            return
        if self._selector:
            self._selector.deleteLater()
        selector = QComboBox()
        selector.setWindowFlags(Qt.WindowType.Popup)
        self._selector = selector
        selector.addItem('(Ignore column)', None)
        for field in self.model().availableColumnNames():
            attributes = self.model()._field_attributes(field)
            selector.addItem(attributes.get('string', field), field)
        selected = self.model().columnSelection()[column]
        selector.setCurrentIndex(selector.findData(selected))
        selector.setMinimumWidth(max(220, self.columnWidth(column)))
        selector.activated.connect(lambda index: self._column_selected(column, selector, index))
        global_pos = self._column_header.mapToGlobal(
            QPoint(self._column_header.sectionViewportPosition(column), self._column_header.height())
        )
        selector.move(global_pos)
        selector.show()
        selector.showPopup()

    def _column_selected(self, column: int, selector: QComboBox, index: int):
        self.model().setColumnSelection(column, selector.itemData(index))
        selector.hide()
        selector.deleteLater()
        self._selector = None
