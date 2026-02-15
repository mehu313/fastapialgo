import asyncio
from app.strategies.bollinger import bollinger_reversal
from app.strategies.rsi import rsi_strategy
from app.tasks.signal_dispatcher import dispatch_signal
from app.brokers.binance import BinanceBroker


class StrategyManager:

    def __init__(self):
        self.broker = BinanceBroker()
        self.strategies = {
            "bollinger": bollinger_reversal,
            "rsi": rsi_strategy,
        }
        self.running_strategies = {}
        self.symbols = ["BTCUSDT", "ETHUSDT"]
        self.timeframes = ["5m", "15m"]
        self.candle_lock = {}

    async def start_strategy(self, strategy_name):

        if strategy_name in self.running_strategies:
            print(f"{strategy_name} already running")
            return

        task = asyncio.create_task(self._run(strategy_name))
        self.running_strategies[strategy_name] = task

        print(f"✅ {strategy_name} started")

    async def stop_strategy(self, strategy_name):

        task = self.running_strategies.get(strategy_name)

        if task:
            task.cancel()
            del self.running_strategies[strategy_name]
            print(f"🛑 {strategy_name} stopped")

    async def _run(self, strategy_name):

        strategy_func = self.strategies[strategy_name]

        while True:
            for symbol in self.symbols:
                for tf in self.timeframes:
                    try:
                        df = self.broker.get_ohlc(symbol, tf, 200)
                        if df is None:
                            continue

                        result = strategy_func(df, symbol, tf)

                        if not result:
                            continue

                        key = f"{symbol}_{strategy_name}_{tf}"
                        candle_id = result["candle_id"]

                        # 🔥 Prevent duplicate execution per candle
                        if self.candle_lock.get(key) == candle_id:
                            continue

                        self.candle_lock[key] = candle_id

                        await dispatch_signal(result)

                    except Exception as e:
                        print(f"{strategy_name} error → {e}")

            await asyncio.sleep(5)
