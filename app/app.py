import json
import yfinance as yf
import pandas as pd
from io import StringIO


def lambda_handler(event, context):
    print("Received event: " + json.dumps(event, indent=2))

    # Extract parameters
    max_time_window = event.get("max_time_window", 1)
    ticker_symbol = event.get("ticker_symbol", "AAPL")
    interval = event.get("interval", "1h")

    print(f"Max Time Window: {max_time_window}")
    print(f"Ticker Symbol: {ticker_symbol}")
    print(f"Interval: {interval}")

    # Fetch stock data
    stock_data = yf.download(
        ticker_symbol, period=f"{max_time_window}d", interval=interval
    )

    # Convert stock data to JSON
    stock_data_json = stock_data.to_json()
    # print(stock_data_json)

    # Load stock data JSON to DataFrame
    stock_data_df = pd.read_json(StringIO(stock_data_json))

    # Change column names
    stock_data_df.columns = [
        "Close",
        "High",
        "Low",
        "Open",
        "Volume",
    ]

    # Convert DataFrame to JSON
    stock_data_json = stock_data_df.to_json()
    print(stock_data_json)

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
                "stock_data": stock_data_json,
            }
        ),
    }
