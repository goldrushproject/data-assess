import math
import pandas as pd
import numpy as np
import boto3
from decimal import Decimal

def lambda_handler(event, context):
    # Extract sampled data from event
    sampled_data_package = event.get("clean_sampled_data", []) 
    ticker_symbol = sampled_data_package.get("ticker_symbol", None)
    sampled_data = sampled_data_package.get("data", [])
    sample_df = pd.DataFrame(sampled_data)
    pe_ratio = sampled_data_package.get("pe_ratio", None)
    eps = sampled_data_package.get("eps", None)
    market_cap = sampled_data_package.get("market_cap", None)
    beta = sampled_data_package.get("beta", None)
    dividend_yield = sampled_data_package.get("dividend_yield", None)
    sector = sampled_data_package.get("sector", None)
    industry = sampled_data_package.get("industry", None)
    country = sampled_data_package.get("country", None)

    # Extract predicted data from event
    predicted_data_package = event.get("clean_predicted_data", [])  
    short_term_trend = predicted_data_package.get("short_term_trend", None)
    mid_term_trend = predicted_data_package.get("mid_term_trend", None)
    long_term_trend = predicted_data_package.get("long_term_trend", None)
    
    # Compute average trade volume overall
    sample_df['Volume'] = sample_df['Volume'].astype(float)  # Ensure Volume is float
    mean_volume = sample_df['Volume'].mean()

    # Compute volatility
    def compute_volatility(data):
        return data.pct_change().std()
    sample_df['Volatility'] = compute_volatility(sample_df['Close'])
    mean_volatility = sample_df['Volatility'].mean()

    # Compute efficiency ratio with adaptive window based on volatility
    def dynamic_er_window(data, base_window=14):
        """Adjust ER window based on volatility."""
        volatility = data.pct_change().rolling(window=14).std().iloc[-1]  # Use std dev of returns
        scaled_vol = min(volatility * 10, 1)  # Normalize between 0 and 1
        return int(base_window * (1 + 0.5 * scaled_vol))  # Scale window size adaptively

    def efficiency_ratio(data):
        """Calculates the Efficiency Ratio (ER) with adaptive window."""
        adaptive_window = dynamic_er_window(data)
        change = abs(data.iloc[-1] - data.iloc[-adaptive_window])
        volatility = sum(abs(data.diff().iloc[-adaptive_window:]))
        return change / volatility if volatility != 0 else 0
    er = efficiency_ratio(sample_df['Close'])

    # Compute ADX with adaptive lookback based on volatility and efficiency ratio
    def compute_adx(data, er, base_period=14):
        """Compute ADX with adaptive lookback based on volatility and efficiency ratio."""
        
        # Normalize volatility (assume volatility is standard deviation of returns)
        volatility = data['Close'].pct_change().rolling(window=14).std().iloc[-1]
        volatility_scaled = min(volatility * 10, 1)  # Scale between 0-1
        
        # Adaptive ADX window based on both volatility & efficiency ratio
        adaptive_period = int(base_period * (1 + 0.5 * volatility_scaled + 0.5 * er))
        adaptive_period = max(5, min(adaptive_period, 30))  # Keep within reasonable range

        # Compute True Range (TR) & ATR
        high, low, close = data['High'], data['Low'], data['Close']
        tr = pd.concat([high - low, abs(high - close.shift()), abs(low - close.shift())], axis=1).max(axis=1)
        atr = tr.rolling(window=adaptive_period).mean()

        # Compute +DM and -DM
        plus_dm = high.diff()
        minus_dm = low.diff()
        
        # Set negative values to 0 for +DM and positive values to 0 for -DM
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm > 0] = 0
        
        # Compute Directional Indicators (+DI, -DI)
        plus_di = 100 * (plus_dm.rolling(window=adaptive_period).mean() / atr)
        minus_di = abs(100 * (minus_dm.rolling(window=adaptive_period).mean() / atr))

        # Compute ADX
        dx = abs(plus_di - minus_di) / (plus_di + minus_di + 1e-10)  # Avoid division by zero
        adx = dx.rolling(window=adaptive_period).mean()

        # Return all three values
        return plus_di, minus_di, adx
    sample_df['+DI'], sample_df['-DI'], sample_df['ADX'] = compute_adx(sample_df, er)
    current_adx = sample_df['ADX'].iloc[-1]

    # Compute RSI with lookback period based on ADX
    def compute_rsi_trend_based(data, adx, base_period=14):
        adjusted_period = int(base_period * (1.5 if adx > 25 else 0.8 if adx < 20 else 1))
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=adjusted_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=adjusted_period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    sample_df['RSI'] = compute_rsi_trend_based(sample_df['Close'], sample_df['ADX'].iloc[-1])
    mean_rsi = sample_df["RSI"].mean()

    # Compute MACD with windows based on ADX
    def compute_macd(data, adx, short_window=12, long_window=26, signal_window=9):
        # Scale ADX between 0 and 1 (assuming typical range 0-50+)
        adx_scaled = min(adx / 50, 1)  # Normalize ADX (50 is a strong trend threshold)

        # Adjust MACD windows dynamically
        adjusted_short_window = max(5, int(short_window * (1 + 0.5 * adx_scaled)))
        adjusted_long_window = max(10, int(long_window * (1 + 0.5 * adx_scaled)))
        adjusted_signal_window = max(5, int(signal_window * (1 + 0.3 * adx_scaled)))  # Less reactive

        # Compute MACD
        short_ema = data.ewm(span=adjusted_short_window, adjust=False).mean()
        long_ema = data.ewm(span=adjusted_long_window, adjust=False).mean()
        macd = short_ema - long_ema  # MACD Line
        signal = macd.ewm(span=adjusted_signal_window, adjust=False).mean()  # Signal Line
        
        return macd, signal
    sample_df['MACD'], sample_df['Signal'] = compute_macd(sample_df['Close'], sample_df['ADX'].iloc[-1])
    latest_macd = sample_df['MACD'].iloc[-1]
    latest_histogram = sample_df['MACD'].iloc[-1] - sample_df['Signal'].iloc[-1]
    average_histogram = (sample_df['MACD'] - sample_df['Signal']).rolling(window=14).mean().iloc[-1]
    smoothed_macd = sample_df['MACD'].rolling(window=14).mean().iloc[-1]
    macd_signal_ratio = sample_df['MACD'].iloc[-1] / sample_df['Signal'].iloc[-1]
    last_crossover = "Bullish" if sample_df['MACD'].iloc[-1] > sample_df['Signal'].iloc[-1] else "Bearish"
    smoothed_macd_ema = sample_df['MACD'].ewm(span=14, adjust=False).mean().iloc[-1]

    # Compute ATR with adaptive window based on trend (ADX)
    def compute_atr(data, adx, base_period=14):
        # Calculate volatility (scaled between 0-1) and normalize ADX
        volatility_scaled = min(data['Close'].pct_change().rolling(14).std().iloc[-1] * 10, 1)
        adx_normalized = adx / 100
        # Determine adaptive window size based on volatility and ADX
        adaptive_period = max(5, min(int(base_period * (1 + 0.5 * volatility_scaled + 0.5 * adx_normalized)), 30))
        # Calculate True Range and ATR using adaptive window
        tr = pd.concat([data['High'] - data['Low'], abs(data['High'] - data['Close'].shift()), abs(data['Low'] - data['Close'].shift())], axis=1).max(axis=1)
        return tr.rolling(window=adaptive_period).mean().iloc[-1]
    atr = compute_atr(sample_df, sample_df['ADX'].iloc[-1])

    # Drop the 'Volatility' column to avoid confusion
    sample_df.drop(columns=['Volatility'], inplace=True)

    # Print first n rows of the DataFrame for debugging
    n = 30
    print(f"Sampled DataFrame (first n rows):\n{sample_df.head(n)}")

    # Construct output payload
    output = {
        "symbol": ticker_symbol,
        "pe_ratio": pe_ratio,
        "eps": eps,
        "market_cap": market_cap,
        "beta": beta,
        "dividend_yield": dividend_yield,
        "sector": sector,
        "industry": industry,
        "country": country,
        "short_term_trend": short_term_trend,
        "mid_term_trend": mid_term_trend,
        "long_term_trend": long_term_trend,
        "volatility": mean_volatility,
        "average_trade_volume": mean_volume,
        "efficiency_ratio": er,
        "current_adx": current_adx,
        "mean_rsi": mean_rsi,
        "latest_macd": latest_macd,
        "latest_histogram": latest_histogram,
        "average_histogram": average_histogram,
        "smoothed_macd": smoothed_macd,
        "macd_signal_ratio": macd_signal_ratio,
        "last_crossover": last_crossover,
        "smoothed_macd_ema": smoothed_macd_ema,
        "atr": atr,
        "Open": sample_df["Open"].tolist(),
        "High": sample_df["High"].tolist(),
        "Low": sample_df["Low"].tolist(),
        "Close": sample_df["Close"].tolist(),
        "Volume": sample_df["Volume"].tolist(),
        "MA50": sample_df["Close"].rolling(window=50).mean().tolist(),
        "MA200": sample_df["Close"].rolling(window=200).mean().tolist(),
        "RSI": sample_df["RSI"].tolist(),
        "+DI": sample_df["+DI"].tolist(),
        "-DI": sample_df["-DI"].tolist(),
        "ADX": sample_df["ADX"].tolist(),
        "MACD": sample_df["MACD"].tolist(),
        "Signal": sample_df["Signal"].tolist()
    }

    # Compute a overall recommendation index based on composite factors in output
    def compute_recommendation_index(data, fundamental_weight=0.5, technical_weight=0.5):
        pe_score       = 1 / data["pe_ratio"] if data["pe_ratio"] > 0 else 0
        eps_score      = np.clip(data["eps"] / 10, 0, 1)
        dividend_score = np.clip(data["dividend_yield"] / 10, 0, 1)
        beta_score     = 1 / data["beta"] if data["beta"] > 0 else 0
        efficiency_score = np.clip(data["efficiency_ratio"] / 100, 0, 1)
        fundamental = np.mean([pe_score, eps_score, dividend_score, beta_score, efficiency_score])
        
        trend  = np.mean([data["short_term_trend"], data["mid_term_trend"], data["long_term_trend"]])
        adx    = np.clip(data["current_adx"] / 50, 0, 1)
        rsi    = 1 - np.clip(abs(data["mean_rsi"] - 50) / 50, 0, 1)
        macd   = np.clip((data["macd_signal_ratio"] + 1) / 2, 0, 1)
        technical = np.mean([trend, adx, rsi, macd])
        
        return fundamental_weight * fundamental + technical_weight * technical
    recommendation = compute_recommendation_index(output, fundamental_weight=0.6, technical_weight=0.4)
    output["recommendation"] = recommendation
    
    # Print non-list members of the output for debugging
    print("output metrics:")
    for key, value in output.items():
        if not isinstance(value, list):
            print(f"{key}: {value}")

    # Convert all float values in the output to Decimal for DynamoDB compatibility, and handle NaN/Infinity
    def enforce_dynamodb_types(data):
        """Recursively convert all float values in a dictionary to Decimal, handling Infinity and NaN."""
        if isinstance(data, dict):
            return {key: enforce_dynamodb_types(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [enforce_dynamodb_types(item) for item in data]
        elif isinstance(data, float):
            if math.isnan(data) or math.isinf(data):
                return None  # or use 0, depending on your preference
            return Decimal(str(data))  # Convert float to Decimal
        else:
            return data

    # Upload output to DynamoDB (PUT)
    dynamodb = boto3.resource('dynamodb')
    table_name = "StocksEDAResults" 
    table = dynamodb.Table(table_name)

    # Convert all float values in the 'output' dictionary to Decimal
    output = enforce_dynamodb_types(output)

    # Now upload the converted 'output' to DynamoDB
    table.put_item(Item=output)
    
    return {
        "statusCode": 200
    }
