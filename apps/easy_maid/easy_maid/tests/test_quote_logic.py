import unittest

from easy_maid.easy_maid.quote_logic import clean_quote_request_payload


class TestQuoteLogic(unittest.TestCase):
    def test_clean_payload_marks_honeypot(self):
        cleaned = clean_quote_request_payload(
            {
                "full_name": "Alice",
                "email": "alice@example.com",
                "address": "123 Main St",
                "city": "Jersey City",
                "details": "Need recurring clean",
                "website": "spam.example",
            }
        )
        self.assertTrue(cleaned["is_honeypot"])

    def test_missing_required_fields_raises(self):
        with self.assertRaises(ValueError):
            clean_quote_request_payload({"email": "x@example.com"})

    def test_invalid_email_raises(self):
        with self.assertRaises(ValueError):
            clean_quote_request_payload(
                {
                    "full_name": "Alice",
                    "email": "alice-at-example.com",
                    "address": "123 Main St",
                    "city": "Jersey City",
                    "details": "Need recurring clean",
                }
            )


if __name__ == "__main__":
    unittest.main()
