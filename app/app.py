import json
import pandas as pd

def lambda_handler(event, context):

    # Extract parameters
    max_time_window = event.get("max_time_window", 1)
    ticker_symbol = event.get("ticker_symbol", "AAPL")
    interval = event.get("interval", "1h")
    test_data = event.get("test_data", {})

    print(f"Max Time Window: {max_time_window}")
    print(f"Ticker Symbol: {ticker_symbol}")
    print(f"Interval: {interval}")

    # Load test data into DataFrame
    stock_data_df = pd.DataFrame(test_data)

    # Calculate volatility index (example calculation)
    stock_data_df['Volatility'] = stock_data_df['High'] - stock_data_df['Low']
    volatility_index = stock_data_df['Volatility'].mean()
    print(f"Volatility Index: {volatility_index}")

    # Example processing
    message = f"Hello from Lambda! Received ticker {ticker_symbol} with a time window of {max_time_window} and interval {interval}."

    # Return a response
    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "message": message,
                "max_time_window": max_time_window,
                "ticker_symbol": ticker_symbol,
                "interval": interval,
                "volatility": volatility_index
            }
        ),
    }
