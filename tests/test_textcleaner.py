import unittest

from app.controller.textcleaner import clean_import_text


class TestTextCleaner(unittest.TestCase):
    def test_repairs_mojibake_and_preserves_accents(self):
        self.assertEqual(clean_import_text("CÃ³digo de barras"), "Código de barras")

    def test_removes_control_and_symbol_characters(self):
        self.assertEqual(clean_import_text("Name\u0000 ™"), "Name")

    def test_preserves_non_text_values(self):
        self.assertEqual(clean_import_text(12.5), 12.5)


if __name__ == "__main__":
    unittest.main()
