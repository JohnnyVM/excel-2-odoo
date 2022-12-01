import unittest

from copy import deepcopy

from . import odoomodel

FIELDS = {
    'barcode': {
        'string': 'Código de Barras',  # Display name
        'help': 'Código de barras',  # tooltip
        'type': 'string',  # many2one | many2many  require relation
    },
    'default_code': {
        'string': 'Código interno',
        'help': 'Código interno',
        'type': 'string',
    },
    'list_price': {
        'string': 'Precio de venta',
        'help': 'Precio de venta',
        'type': 'float',
    },
    'categ_id': {
        'string': 'Categoría de producto',
        'help': 'Categoría de producto',
        'type': 'many2one',
        'relation': 'product.category',
    },
    'taxes_id': {
        'string': 'Impuestos cliente',
        'help': 'Impuestos cliente',
        'type': 'many2many',
        'relation': 'account.tax',
        'domain': (("type_tax_use", "=", "sale"),)
    },
}


class TestOdooModel(unittest.TestCase):
    def test_columnCount(self):
        model = odoomodel.OdooModel(
            conn=None,
            name='test_columnCount',
            autoload=False)
        model._fields = deepcopy(FIELDS)
        self.assertEqual(len(FIELDS), model.columnCount())

    def test_removeColumns(self):
        model = odoomodel.OdooModel(
            conn=None,
            name='test_removeColumns',
            autoload=False)
        model._fields = deepcopy(FIELDS)
        model.removeColumns(model.columnCount() - 1, 1)  # remove latest
        self.assertEqual(len(FIELDS) - 1, model.columnCount())
        model.removeColumns(0, model.columnCount())  # remove latest
        self.assertEqual(0, model.columnCount())


if __name__ == '__main__':
    unittest.main()
