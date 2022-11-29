from PyQt6.QtCore import (
    QAbstractTableModel,
    QObject,
    QModelIndex,
    Qt)

import odoorpc
import openpyxl

from .odoomodel import OdooModel


class ExcelOdooModel(OdooModel):
    """
    Convenience function to overload __init__
    self._fields = {
        'taxes_id': {
            'string': 'Impuestos cliente',
            'help': 'Impuestos cliente',
            'type': 'many2many',
            'relation': 'account.tax',
            'domain': (("type_tax_use", "=", "sale"),)
        },
    }
    """

    def __init__(self, conn: odoorpc.ODOO, parent: QObject = None, fields: dict = {}, **kwargs):
        """ """
        QAbstractTableModel.__init__(self, parent)
        self._name = "CustomOdooModel"
        self._conn = conn

        if 'name' in kwargs:
            self._name = kwargs['name']

        if 'domain' in kwargs:
            self.domain = kwargs['domain']

        if 'company_id' in kwargs:
            self.company_id = kwargs['company_id']

        self._fields = fields

        self._loadRelationalData()

    def loadExcel(self, excel_file: str):
        pass
