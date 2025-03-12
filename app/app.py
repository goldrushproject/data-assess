import json
import pandas as pd

def lambda_handler(event, context):

    try:
        # Extract parameters
        sample_time_window = event.get("sample_time_window", 5)
        prediction_time_window = event.get("prediction_time_window", 5)
        ticker_symbol = event.get("ticker_symbol", "AAPL")
        interval = event.get("interval", "1h")
        sampled_data = event.get("sample_data", {}) # Sample of stock pricing data for the given time window
        predicted_data = event.get("predicted_data", {}) # Predicted stock pricing data for the given time window

        # Calculate volatility index given sample data
        data_df = pd.DataFrame(sampled_data)
        data_df['Volatility'] = data_df['High'] - data_df['Low']
        volatility_index = data_df['Volatility'].mean()

        # Calculate index of price trend given predicted data
        predicted_df = pd.DataFrame(predicted_data, columns=['Close'])
        predicted_df['Price_Trend'] = predicted_df['Close'].diff().fillna(0)
        price_trend_index = predicted_df['Price_Trend'].mean()

        # Return a response
        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "sample_time_window": sample_time_window,
                    "prediction_time_window": prediction_time_window,
                    "ticker_symbol": ticker_symbol,
                    "interval": interval,
                    "volatility": volatility_index,
                    "price_trend_index": price_trend_index
                }
            ),
        }
    except Exception as e:
        print(f"Error: {e}")
        print(f"Event: {event}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e), "event": event}),
        }
