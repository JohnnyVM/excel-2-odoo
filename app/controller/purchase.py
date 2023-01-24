from datetime import datetime
import concurrent.futures
from copy import deepcopy

from PyQt6.QtCore import qInfo

from ..gui.model.odoomodel import OdooModel

MANDATORY_FIELDS = ['product_qty', 'price_unit', 'supplier_taxes_id']


def create_purchase_order(conn, header: OdooModel, lines: OdooModel):
    order = header['_data'][0]

    pid = conn.execute_kw('purchase.order', 'create', [order])
    qInfo(f"Create order with id {pid}")

    # Get all products ids
    data = deepcopy(lines._data)
    for row in data:
        row['barcode'] = str(row['barcode'])
    barcodes = tuple(str(row['barcode']) for row in data)
    odoo_products = conn.execute_kw(
        'product.product',
        "search_read",
        ((('barcode', 'in', barcodes),),),
        {'fields': [
            'id',
            'barcode',
            'display_name',
            'uom_po_id',
            'product_variant_id']})

    def create_line(row: dict) -> dict:
        return {
            'order_id': pid,
            'product_id': row['id'],
            'product_qty': row['product_qty'],
            'price_unit': row['price_unit'],
            'name': row['display_name'],
            'taxes_id': row['supplier_taxes_id'],
            'product_uom': row['product_uom'],
            'date_planned': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }

    lines = []
    for row in data:
        for prod in odoo_products:
            if row['barcode'] == prod['barcode']:
                row.update({
                    'id': prod['id'],
                    'display_name': prod['display_name'],
                    'product_uom': prod['uom_po_id'][0],
                })
                lines.append(create_line(row))

    def create_order_line(product):
        qInfo(f"create order line for product {product}".encode('utf-8'))
        conn.execute_kw('purchase.order.line', 'create', [product])

    with concurrent.futures.ThreadPoolExecutor() as exec:
        for line in lines:
            # exec.submit(create_order_line, line)
            create_order_line(line)
