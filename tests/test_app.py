import unittest
import json
from app.app import lambda_handler

class TestApp(unittest.TestCase):
    def test_app(self):
        with open('./tests/test_sample_data.json') as f:
            test_sample_data = json.load(f)
        with open('./tests/test_predicted_data.json') as f:
            test_predicted_data = json.load(f)

        event = {
            "parameters": {
                "sample_time_window": 5,
                "prediction_time_window": 5,
                "ticker_symbol": "AAPL",
                "interval": "1m"
            },
            "sample_data": test_sample_data,
            "predicted_data": test_predicted_data
        }
        context = {}
        response = lambda_handler(event, context)
        self.assertEqual(response["statusCode"], 200)
        body = json.loads(response["body"])
        self.assertIn("volatility", body)
        self.assertIn("price_trend_index", body)

if __name__ == "__main__":
    unittest.main()
