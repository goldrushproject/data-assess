import json
import pandas as pd

def lambda_handler(event, context):
    # Extract parameters
    parameters = event.get("parameters", {})
    sample_time_window = parameters.get('sample_time_window', 'N/A')
    prediction_time_window = parameters.get('prediction_time_window', 'N/A')
    ticker_symbol = parameters.get('ticker_symbol', 'N/A')
    interval = parameters.get('interval', 'N/A')
    
    # Extract data from event
    sampled_data = event.get("sample_data", [])['data']  # list of dicts containing historical price data
    predicted_data = event.get("predicted_data", [])  # list of predicted close prices

    # Ensure sample_data is available
    if not sampled_data:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "No sample data provided"})
        }
    
    # Convert sampled data to DataFrame
    sample_df = pd.DataFrame(sampled_data)
    
    # Calculate volatility index from sample data
    sample_df['Volatility'] = sample_df['High'] - sample_df['Low']
    volatility_index = sample_df['Volatility'].mean()
    
    # 1. Trend Indices based on available data
    # 1-day Trend: percentage change in the sample data (assuming sample covers 1 day)
    first_close = sample_df['Close'].iloc[0]
    last_close = sample_df['Close'].iloc[-1]
    trend_1_day = (last_close - first_close) / first_close * 100
    
    # 1-week and 1-month Trends from predicted data (assuming each entry represents an end-of-day price)
    predicted_df = pd.DataFrame(predicted_data, columns=['Close'])
    trend_1_week = None
    trend_1_month = None
    if len(predicted_df) >= 5:
        week_first = predicted_df['Close'].iloc[0]
        week_last = predicted_df['Close'].iloc[4]
        trend_1_week = (week_last - week_first) / week_first * 100
    if len(predicted_df) >= 20:
        month_first = predicted_df['Close'].iloc[0]
        month_last = predicted_df['Close'].iloc[19]
        trend_1_month = (month_last - month_first) / month_first * 100

    # 2. Risk Index: standard deviation of percentage returns from sample data
    sample_df['Return'] = sample_df['Close'].pct_change().fillna(0)
    risk_index = sample_df['Return'].std() * 100  # expressed as percentage

    # 3. Potential Gain: percentage difference between predicted maximum price and last sample price
    if not predicted_df.empty:
        predicted_max = predicted_df['Close'].max()
        potential_gain = (predicted_max - last_close) / last_close * 100
    else:
        potential_gain = 0

    # 4. Recommendation Level:
    # A simple heuristic: combine the 1-day trend and potential gain and adjust by risk.
    # (Higher positive value => buy recommendation, negative => sell recommendation)
    # Adding a small epsilon to risk to avoid division by zero.
    epsilon = 1e-5
    recommendation_level = (trend_1_day + potential_gain) / (risk_index + epsilon)
    
    # Additional custom indicator: Average RSI from the sample (if available)
    avg_rsi = sample_df['RSI'].mean() if 'RSI' in sample_df.columns else None

    # Construct response payload
    response_body = {
        "sample_time_window": sample_time_window,
        "prediction_time_window": prediction_time_window,
        "ticker_symbol": ticker_symbol,
        "interval": interval,
        "volatility": volatility_index,
        "trend_indices": {
            "1_day_trend_percentage": trend_1_day,
            "1_week_trend_percentage": trend_1_week,
            "1_month_trend_percentage": trend_1_month
        },
        "risk_index_percentage": risk_index,
        "potential_gain_percentage": potential_gain,
        "recommendation_level": recommendation_level,
        "average_RSI": avg_rsi
    }
    
    return {
        "statusCode": 200,
        "body": json.dumps(response_body)
    }
