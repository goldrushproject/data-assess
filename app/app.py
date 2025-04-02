import json
import pandas as pd

def lambda_handler(event, context):
    # Extract parameters
    parameters = event.get("parameters", {})
    ticker_symbol = parameters.get('ticker_symbol', 'N/A')
    
    # Extract data from event
    sampled_data = event.get("clean_sampled_data", [])  # list of dicts containing historical price data
    predicted_data = event.get("clean_predicted_data", [])  # list of predicted close prices
    
    # Convert data to DataFrame
    sample_df = pd.DataFrame(sampled_data)
    predicted_df = pd.DataFrame(predicted_data, columns=['Close'])
    
    # Calculate volatility index from sample data
    sample_df['Volatility'] = sample_df['High'] - sample_df['Low']
    volatility_index = sample_df['Volatility'].mean()
    
    # Calculate risk index: standard deviation of percentage returns from sample data
    sample_df['Return'] = sample_df['Close'].pct_change().fillna(0)
    risk_index = sample_df['Return'].std() * 100  # expressed as percentage

    # potential gain: percentage difference between predicted maximum price and last sample price
    predicted_max = predicted_df['Close'].max()
    potential_gain = (predicted_max - last_close) / last_close * 100

    # Calculate recommendation level:
    # A simple heuristic: combine the 1-day trend and potential gain and adjust by risk.
    # (Higher positive value => buy recommendation, negative => sell recommendation)
    # Adding a small epsilon to risk to avoid division by zero.
    epsilon = 1e-5
    recommendation_level = (trend_1_day + potential_gain) / (risk_index + epsilon)
    
    # Additional custom indicator: Average RSI from the sample (if available)
    avg_rsi = sample_df['RSI'].mean() if 'RSI' in sample_df.columns else None

    # Calculate trend indices from predicted data
    # 1-day Trend: percentage change in the sample data (assuming sample covers 1 day)
    first_close = sample_df['Close'].iloc[0]
    last_close = sample_df['Close'].iloc[-1]
    trend_1_day = (last_close - first_close) / first_close * 100
    
    # 1-week and 1-month Trends from predicted data (assuming each entry represents an end-of-day price)
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

    # Construct response payload
    response_body = {
        "ticker_symbol": ticker_symbol,
        "volatility": volatility_index,
        "trend_indices": {
            "one_day_trend_percentage": trend_1_day,
            "one_week_trend_percentage": trend_1_week,
            "one_month_trend_percentage": trend_1_month
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
