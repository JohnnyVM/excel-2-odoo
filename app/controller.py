import openpyxl

from . import settings
from .dependencies import get_odoo
from .gui.model.odoomodel import OdooModel

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


def factoryExcelOdooModel(excel_file: str, parent):
    wb = openpyxl.load_workbook(
        filename=excel_file, read_only=True, data_only=True)
    sheet = wb[wb.sheetnames[0]]  # only the first

    iter_rows = sheet.iter_rows()
    model = OdooModel(
        conn=get_odoo(settings.conf),
        name='Excel load',
        company_id=parent._company_id,
        autoload=False)
    headers = next(iter_rows)  # discard header
    for idx, header in enumerate(headers):
        val = header.value
        if val:
            value = {'string': val}
            model._fields.update({val: value})
    for row in iter_rows:
        model._data.append(dict(zip(model._fields.keys(), map(lambda r: r.value, row))))

    wb.close()
    return model
