import unittest
from main import main


class TestMain(unittest.TestCase):
    def test_main_returns_expected_message(self):
        self.assertIn("essenn", main())


if __name__ == "__main__":
    # Let this be the only line we're not covering
    unittest.main()  # pragma: no cover
