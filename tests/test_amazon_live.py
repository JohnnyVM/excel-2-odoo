import os
import unittest
import importlib.util


_live_enabled = os.getenv("LIVE_TEST") == "1"
_playwright_available = importlib.util.find_spec("playwright") is not None


@unittest.skipUnless(
    _live_enabled and _playwright_available,
    "set LIVE_TEST=1 and install playwright to run the real Amazon lookup",
)
class TestAmazonLive(unittest.TestCase):
    def test_barcode_9788484454588(self):
        from app.services.amazon import AmazonScraper

        scraper = AmazonScraper()
        self.assertTrue(scraper.chromium_installed())
        result = scraper.search("9788484454588")
        self.assertIsNotNone(result)
        self.assertTrue(result.name or result.description or result.image)


if __name__ == "__main__":
    unittest.main()
