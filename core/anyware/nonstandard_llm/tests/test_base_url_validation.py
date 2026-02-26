import unittest

from core.anyware.nonstandard_llm.client import _validate_base_url


class TestBaseUrlValidation(unittest.TestCase):
    def test_accepts_https_url(self) -> None:
        value = _validate_base_url("https://api.deepseek.com")
        self.assertEqual(value, "https://api.deepseek.com")

    def test_rejects_file_scheme(self) -> None:
        with self.assertRaises(ValueError):
            _validate_base_url("file:///tmp/secret")


if __name__ == "__main__":
    unittest.main()
