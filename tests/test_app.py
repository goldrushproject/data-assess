import unittest
import json
from app.app import lambda_handler

class TestApp(unittest.TestCase):
    def test_app(self):
        with open('./tests/assessment_test_data.json') as f:
            test_data = json.load(f)
        
        event = {
            "max_time_window": 2,
            "ticker_symbol": "AAPL",
            "interval": "1h",
            "test_data": test_data
        }
        context = {}
        response = lambda_handler(event, context)
        self.assertEqual(response["statusCode"], 200)
        self.assertIn("volatility", response["body"])

if __name__ == "__main__":
    unittest.main()
