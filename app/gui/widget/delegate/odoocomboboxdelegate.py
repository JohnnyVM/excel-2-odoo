from PyQt6.QtWidgets import QStyledItemDelegate, QWidget, QStyleOptionViewItem
from PyQt6.QtCore import QObject, QModelIndex

from ..odoocombobox import OdooComboBox


class OdooComboBoxDelegate(QStyledItemDelegate):

    def __init__(self, parent: QObject = None):
        QStyledItemDelegate.__init__(self, parent)

    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex):
        model = index.model()
        field = [val for val in model._fields.keys()][index.column()]
        relational_model = model._relational_model[field]
        editor = OdooComboBox(parent=parent)
        editor.setModel(relational_model)

        # editor.editingFinished.connnect()

        return editor

    def setEditorData(self, editor: QWidget, index: QModelIndex):
        data = index.data()[0]
        data_index = editor.findData(data)
        editor.setCurrentIndex(data_index)
