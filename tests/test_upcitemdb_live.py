import os
import unittest


@unittest.skipUnless(os.getenv("LIVE_TEST") == "1", "set LIVE_TEST=1 to run the real UPCitemdb lookup")
class TestUPCItemDBLive(unittest.TestCase):
    def test_barcode_9788484454588(self):
        from app.services.upcitemdb import UPCItemDB

        result = UPCItemDB().search("9788484454588")
        self.assertIsNotNone(result)
        self.assertTrue(result.name or result.description or result.image_url)


if __name__ == "__main__":
    unittest.main()
