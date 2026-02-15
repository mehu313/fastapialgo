from .base import rsi
import pandas as pd

def rsi_strategy(df: pd.DataFrame) -> str:
    df = rsi(df)
    last_rsi = df['rsi'].iloc[-1]
    prev_rsi = df['rsi'].iloc[-2]

    if prev_rsi <= 60 < last_rsi:
        return 'BUY'
    elif prev_rsi >= 40 > last_rsi:
        return 'SELL'
    else:
        return 'HOLD'
