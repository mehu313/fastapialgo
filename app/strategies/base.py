import pandas as pd

# ---- Indicators ----
def bollinger_bands(df: pd.DataFrame, period: int = 20, std_dev: int = 2) -> pd.DataFrame:
    df['MA'] = df['close'].rolling(period).mean()
    df['STD'] = df['close'].rolling(period).std()
    df['upper'] = df['MA'] + std_dev * df['STD']
    df['lower'] = df['MA'] - std_dev * df['STD']
    return df

def rsi(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    delta = df['close'].diff()
    gain = delta.clip(lower=0)
    loss = -1 * delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    df['rsi'] = 100 - (100 / (1 + rs))
    return df
