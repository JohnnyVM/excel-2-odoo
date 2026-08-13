import unittest

from app.controller.fuzzyfinder import match_headers, selectable_odoo_fields


FIELDS = {
    "barcode": {"string": "Código de barras"},
    "list_price": {"string": "Sales Price"},
    "default_code": {"string": "Referencia interna"},
}


class TestFuzzyFinder(unittest.TestCase):
    def test_matches_technical_and_display_names(self):
        self.assertEqual(
            match_headers(("barcode", "Sales price", "Referencia interna"), FIELDS),
            ("barcode", "list_price", "default_code"),
        )

    def test_ignores_accents_and_case(self):
        self.assertEqual(match_headers(("CÓDIGO DE BARRAS",), FIELDS), ("barcode",))

    def test_does_not_reuse_a_field(self):
        self.assertEqual(match_headers(("Barcode", "Barcode"), FIELDS), ("barcode", None))

    def test_leaves_uncertain_headers_unmatched(self):
        self.assertEqual(match_headers(("warehouse notes",), FIELDS), (None,))

    def test_common_barcode_terms_match_barcode(self):
        self.assertEqual(match_headers(("EAN",), {"barcode": FIELDS["barcode"]}), ("barcode",))

    def test_isbn_matches_internal_reference_not_barcode(self):
        fields = {
            "barcode": FIELDS["barcode"],
            "default_code": FIELDS["default_code"],
        }
        self.assertEqual(match_headers(("ISBN",), fields), ("default_code",))

    def test_spanish_price_and_tax_aliases(self):
        fields = {
            "list_price": {"string": "Sales Price"},
            "taxes_id": {"string": "Customer Taxes"},
        }
        self.assertEqual(match_headers(("PVP", "IVA"), fields), ("list_price", "taxes_id"))

    def test_selectable_fields_exclude_unwanted_types(self):
        fields = {
            "tags": {"type": "many2many"},
            "active": {"type": "boolean"},
            "image_128": {"type": "binary"},
            "image_1920": {"type": "binary"},
            "name": {"type": "char"},
        }
        self.assertEqual(
            tuple(selectable_odoo_fields(fields)),
            ("image_1920", "name"),
        )


if __name__ == "__main__":
    unittest.main()
