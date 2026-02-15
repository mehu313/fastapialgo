from abc import ABC
from .base import BrokerBase
from binance.client import Client
import pandas as pd

class BinanceBroker(BrokerBase):
    def __init__(self):
        # Public client (no API key)
        self.client = Client()
        self.INTERVAL_MAP = {
            "1m": Client.KLINE_INTERVAL_1MINUTE,
            "5m": Client.KLINE_INTERVAL_5MINUTE,
            "15m": Client.KLINE_INTERVAL_15MINUTE,
            "1h": Client.KLINE_INTERVAL_1HOUR
        }

    # Helper: fetch OHLC data
    def get_ohlc(self, symbol: str, timeframe: str = "5m", limit: int = 100) -> pd.DataFrame:
        klines = self.client.get_klines(
            symbol=symbol,
            interval=self.INTERVAL_MAP[timeframe],
            limit=limit
        )
        df = pd.DataFrame(klines, columns=[
            'open_time','open','high','low','close','volume',
            'close_time','qav','num_trades','taker_base_vol',
            'taker_quote_vol','ignore'
        ])
        df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
        df = df[['open_time','open','high','low','close','volume']]
        df[['open','high','low','close','volume']] = df[['open','high','low','close','volume']].astype(float)
        return df

    # === BrokerBase abstract methods ===

    def place_order(
        self,
        symbol: str,
        side: str,
        quantity: int,
        order_type: str = "market",
        price: float | None = None
    ):
        # Without API keys we cannot place orders
        raise NotImplementedError("Place order requires Binance API keys")

    def square_off(self, symbol: str):
        # Without API keys we cannot square off
        raise NotImplementedError("Square off requires Binance API keys")

    def get_positions(self):
        # Public data only → no positions
        return []

    # Optional: get last close as "live price"
    def get_ltp(self, symbol: str) -> float:
        df = self.get_ohlc(symbol, "1m", 1)
        return df['close'].iloc[-1]
