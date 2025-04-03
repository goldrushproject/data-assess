import unittest
import json
from app.app import lambda_handler

class TestApp(unittest.TestCase):
    def test_app(self):
        with open('./data_assess_input.json') as f:
            test_data = json.load(f)

        event = test_data
        context = {}
        response = lambda_handler(event, context)
        self.assertEqual(response["statusCode"], 200)

if __name__ == "__main__":
    unittest.main()
