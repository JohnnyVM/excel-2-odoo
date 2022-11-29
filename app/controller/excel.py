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


class Excel():
    pass
