import unittest

from app.controller.factorymodel import IMPORT_FIELDS


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


if __name__ == "__main__":
    unittest.main()
