from PyQt6.QtWidgets import QStyledItemDelegate
from PyQt6.QtCore import QObject, QWidget, QStyleOptionViewItem, QModelIndex

from ..odoocombobox import OdooComboBox


class OdooComboBoxDelegate(QStyledItemDelegate):

    def __init__(self, parent: QObject = None):
        QStyledItemDelegate.__init__(self, parent)

    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex):
        model = parent.model()
        relational_model = model._
        editor = OdooComboBox()
