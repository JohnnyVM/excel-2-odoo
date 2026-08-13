import unittest

from app.controller.fuzzyfinder import match_headers


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


if __name__ == "__main__":
    unittest.main()
