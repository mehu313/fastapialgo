import pandas as pd

def bollinger_reversal(df, symbol, timeframe, period=20, std_dev=2):

    if len(df) < period + 5:
        return None

    df = df.copy()
    df['mb'] = df['close'].rolling(period).mean()
    df['std'] = df['close'].rolling(period).std()
    df['upper'] = df['mb'] + std_dev * df['std']
    df['lower'] = df['mb'] - std_dev * df['std']

    last = df.iloc[-1]

    open_price = last["open"]
    close_price = last["close"]
    upper_band = last["upper"]
    lower_band = last["lower"]

    signal = None

    if open_price < lower_band and close_price > open_price:
        signal = "BUY"
    elif open_price > upper_band and close_price < open_price:
        signal = "SELL"

    if not signal:
        return None

    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "strategy": "bollinger",
        "signal": signal,
        "price": float(close_price),
        "candle_id": df['open_time'].iloc[-1]
    }
