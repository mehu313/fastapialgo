from .base import bollinger_bands
from app.brokers.binance import get_ohlc


def bollinger_reversal_mtf(df_5m, symbol):
    df_1m = get_ohlc(symbol, "1m", 5)

    if df_1m is None or len(df_1m) < 3 or len(df_5m) < 25:
        return []

    df_5m = bollinger_bands(df_5m)

    last_5m = df_5m.iloc[-1]
    last_1m = df_1m.iloc[-1]
    prev_1m = df_1m.iloc[-2]

    candle_id = last_5m.open_time.strftime("%Y%m%d%H%M")

    signal = "NONE"

    # SELL
    if (
        last_5m.open > last_5m.upper and last_5m.close < last_5m.open and
        last_1m.close < prev_1m.low
    ):
        signal = "SELL"

    # BUY
    elif (
        last_5m.open < last_5m.lower and last_5m.close > last_5m.open and
        last_1m.close > prev_1m.high
    ):
        signal = "BUY"

    return [{
        "symbol": symbol,
        "timeframe": "5m",
        "strategy": "BOLLINGER_REVERSAL_MTF",
        "signal": signal,
        "price": float(last_1m.close),
        "candle_id": candle_id
    }]
