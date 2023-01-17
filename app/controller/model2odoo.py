import concurrent.futures
from copy import deepcopy

from PyQt6.QtCore import qWarning, qInfo

from ..gui.model.odoomodel import OdooModel


MANDATORY_FIELDS = ['barcode', 'name', 'taxes_id', 'supplier_taxes_id', 'list_price']

DEFAULT_PRODUCT_VALUES = {
    'type': 'product',
    'available_in_pos': True,
}


def valid_model(model: OdooModel):
    valid = True
    barcodes = tuple(row['barcode'] for row in model._data)
    if len(barcodes) != len(set(barcodes)):
        qWarning('Duplicated barcodes.')
        valid = False
    for idx, row in enumerate(model._data):
        for field in MANDATORY_FIELDS:
            if row[field] is None:
                qWarning(f"{model.name} missing value {field} in row {idx}")
                valid = False
    return valid


def create_products_from_model(model: OdooModel):
    # barcodes are strings
    for row in model._data:
        row['barcode'] = str(row['barcode'])
    barcodes = tuple(str(row['barcode']) for row in model._data)
    odoo_barcodes = model._conn.execute_kw(
        'product.template',
        "search_read",
        ((('barcode', 'in', barcodes),),),
        {'fields': ['barcode']})
    barcodes = set(barcodes)
    odoo_barcodes = set(map(lambda r: r['barcode'], odoo_barcodes))
    create_barcodes = barcodes - odoo_barcodes

    data = deepcopy(model._data)
    # fields from other models removed
    product_fields = model._conn.execute_kw(
        'product.template',
        'fields_get',
        [], {'attributes': ['name']})

    # Fields many2one must be edited
    for field, attributes in model._fields.items():
        if attributes.get('type', False) == 'many2one':
            for p in data:
                if p[field]:
                    p[field] = p[field][0]

    for product in data:
        for key in tuple(product.keys()):
            if key not in product_fields.keys():
                del product[key]
        for key, value in DEFAULT_PRODUCT_VALUES.items():
            if key not in product.keys():
                product.update({key: value})

    data = tuple(filter(lambda p: p['barcode'] in create_barcodes, data))
    new_products = len(data)
    qInfo(f"product.template: {new_products} product news")

    def __create_product(model, product):
        pid = model._conn.execute_kw('product.template', 'create', [product])
        qInfo(f"Created products {pid}")

    with concurrent.futures.ThreadPoolExecutor() as exec:
        for product in data:
            exec.submit(__create_product, model, product)


def update_products_from_model(model: OdooModel):
    # barcodes are strings
    for row in model._data:
        row['barcode'] = str(row['barcode'])
    barcodes = tuple(str(row['barcode']) for row in model._data)
    odoo_products = model._conn.execute_kw(
        'product.template',
        "search_read",
        ((('barcode', 'in', barcodes),),),
        {'fields': ['id', 'barcode']})
    barcodes = set(barcodes)
    odoo_barcodes = set(map(lambda r: r['barcode'], odoo_products))
    update_barcodes = barcodes & odoo_barcodes
    new_products = len(update_barcodes)
    qInfo(f"product.template: {new_products} product to update")

    data = deepcopy(model._data)
    # fields from other models removed
    product_fields = model._conn.execute_kw(
        'product.template',
        'fields_get',
        [], {'attributes': ['name']})

    # Fields many2one must be edited
    for field, attributes in model._fields.items():
        if attributes.get('type', False) == 'many2one':
            for p in data:
                if p[field]:
                    p[field] = p[field][0]

    # ids asigned
    update_products = []
    for product in data:
        for key in tuple(product.keys()):
            if key not in product_fields.keys():
                del product[key]
        ids = None
        for odoo_product in odoo_products:
            if odoo_product['barcode'] == product['barcode']:
                ids = odoo_product['id']
                break
        update_products.append([[ids], {'list_price': product['list_price']}])

    def __update_product(model, product):
        model._conn.execute_kw('product.template', 'write', product)
        qInfo(str(f"Update product {product[0][0]}. Price: {product[1]['list_price']}".encode('utf-8')))

    with concurrent.futures.ThreadPoolExecutor() as exec:
        for product in update_products:
            exec.submit(__update_product, model, product)
