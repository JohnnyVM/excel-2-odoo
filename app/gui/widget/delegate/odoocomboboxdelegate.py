from PyQt6.QtWidgets import (
    QStyledItemDelegate,
    QWidget,
    QStyleOptionViewItem)
from PyQt6.QtGui import QPainter
from PyQt6.QtCore import Qt, QObject, QModelIndex

from ..odoocombobox import OdooComboBox
from ...model.odoomodel import OdooModel

# QUESTION: this should be moved to a editor factory?


class OdooMany2OneDelegate(QStyledItemDelegate):
    def __init__(self, parent: QObject = None):
        QStyledItemDelegate.__init__(self, parent)

    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex):
        model = index.model()
        field = [val for val in model._fields.keys()][index.column()]
        relational_model = model._relational_model[field]
        editor = OdooComboBox(parent=parent)
        editor.setModel(relational_model)

        return editor

    def setEditorData(self, editor: QWidget, index: QModelIndex):
        data = index.model().data(index, Qt.ItemDataRole.EditRole)
        index = editor.findData(data[0])
        editor.setCurrentIndex(index)

    def setModelData(self, editor: QWidget, model: OdooModel, index: QModelIndex):
        idm = editor.currentData()
        text = editor.currentText()
        model.setData(index, [idm, text], Qt.ItemDataRole.EditRole)

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
        idx, value = index.data()
        super().paint(painter, option, index)
        painter.drawText(option.rect, Qt.AlignmentFlag.AlignCenter, value)


class OdooMany2ManyDelegate(QStyledItemDelegate):
    def __init__(self, parent: QObject = None):
        QStyledItemDelegate.__init__(self, parent)

    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex):
        model = index.model()
        field = [val for val in model._fields.keys()][index.column()]
        relational_model = model._relational_model[field]
        editor = OdooComboBox(parent=parent)
        editor.setModel(relational_model)

        return editor

    def setEditorData(self, editor: QWidget, index: QModelIndex):
        data = index.model().data(index, Qt.ItemDataRole.EditRole)
        index = editor.findData(data[0])
        editor.setCurrentIndex(index)

    def setModelData(self, editor: QWidget, model: OdooModel, index: QModelIndex):
        idm = editor.currentData()
        model.setData(index, [idm], Qt.ItemDataRole.EditRole)

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
        model = index.model()
        field_name = [f for f in model._fields.keys()][index.column()]
        rel_model = model._relational_model[field_name]
        texts = []
        for ids in index.data():
            for rel_row in rel_model._data:
                if ids == rel_row['id']:
                    texts.append(tuple(rel_row.values())[1])

        super().paint(painter, option, index)
        painter.drawText(option.rect, Qt.AlignmentFlag.AlignCenter, ', '.join(texts))
