import unittest
import json
from app.app import lambda_handler

class TestApp(unittest.TestCase):
    def test_app(self):
        with open('./tests/sample_data.json') as f:
            test_sample_data = json.load(f)
        with open('./tests/predicted_data.json') as f:
            test_predicted_data = json.load(f)

        event = {
            "parameters": {
                "sample_time_window": 5,
                "prediction_time_window": 5,
                "ticker_symbol": "TSLA",
                "interval": "1m"
            },
            "clean_sampled_data": test_sample_data['data'],
            "clean_predicted_data": test_predicted_data
        }
        context = {}
        response = lambda_handler(event, context)
        response_body = json.loads(response['body'])

        # Write response body to a file
        with open('./sample_assessment.json', 'w') as outfile:
            json.dump(response_body, outfile, indent=4)

        print(response_body)
        self.assertEqual(response["statusCode"], 200)
        body = json.loads(response["body"])

if __name__ == "__main__":
    unittest.main()
