import unittest
from app.app import lambda_handler


class TestApp(unittest.TestCase):
    def test_app(self):
        event = {"max_time_window": 2, "ticker_symbol": "AAPL", "interval": "1h"}
        context = {}
        response = lambda_handler(event, context)
        self.assertEqual(response["statusCode"], 200)
        self.assertIn("Hello from Lambda!", response["body"])
        self.assertIn("AAPL", response["body"])
        self.assertIn("2", response["body"])


if __name__ == "__main__":
    unittest.main()
