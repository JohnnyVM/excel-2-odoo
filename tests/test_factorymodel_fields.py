import os
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app.controller.factorymodel import IMPORT_FIELDS, factoryExcelOdooModel


class FakeOdooModel:
    def __init__(self, conn, **kwargs):
        self._conn = conn
        self._fields = {}
        self._data = []

    def _loadRelationalData(self):
        pass

    def columnCount(self):
        return len(self._fields)

    def columnSelection(self):
        return tuple(self._column_selection)

    def _field_attributes(self, field):
        return self._available_fields[field]

    def rowCount(self):
        return len(self._data)


class TestFactoryModelFields(unittest.TestCase):
    def test_import_field_allowlist_is_fixed(self):
        self.assertEqual(
            IMPORT_FIELDS,
            (
                "barcode", "name", "default_code", "list_price",
                "taxes_id", "supplier_taxes_id", "product_qty", "price_unit",
                "standard_price", "categ_id",
            ),
        )

    def test_import_uses_fallback_metadata_for_fields_missing_from_product_template(self):
        conn = SimpleNamespace(execute_kw=lambda *args, **kwargs: {})
        parent = SimpleNamespace(company_id=1)
        path = None
        try:
            with tempfile.NamedTemporaryFile(
                    mode="w", suffix=".csv", encoding="utf-8", delete=False) as csv_file:
                csv_file.write("product_qty\n2\n")
                path = csv_file.name

            with patch("app.controller.factorymodel.settings.conf", object(), create=True), \
                    patch("app.controller.factorymodel.get_odoo", return_value=conn), \
                    patch("app.controller.factorymodel.OdooModel", FakeOdooModel):
                model = factoryExcelOdooModel(path, parent)

            self.assertEqual(model._fields["product_qty"], {"string": "product_qty"})
            self.assertEqual(model._data, [{"product_qty": "2"}])
        finally:
            if path is not None:
                os.unlink(path)


if __name__ == "__main__":
    unittest.main()
