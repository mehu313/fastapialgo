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
        self.symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT"] # Scaled list
        self.timeframes = ["5m", "15m"]
        # Memory-efficient lock: stores only the latest candle_id per key
        self.candle_lock = {} 

    async def start_strategy(self, strategy_name):
        if strategy_name in self.running_strategies:
            return

        task = asyncio.create_task(self._run(strategy_name))
        self.running_strategies[strategy_name] = task
        print(f"✅ Strategy {strategy_name} started")

    async def stop_strategy(self, strategy_name):
        task = self.running_strategies.get(strategy_name)
        if task:
            task.cancel()
            del self.running_strategies[strategy_name]
            print(f"🛑 Strategy {strategy_name} stopped")

    async def _process_symbol(self, strategy_func, strategy_name, symbol, tf):
        """Processes a single symbol/timeframe in parallel."""
        try:
            df = self.broker.get_ohlc(symbol, tf, 200)
            if df is None or df.empty:
                return

            result = strategy_func(df, symbol, tf)
            if not result:
                return

            key = f"{symbol}_{strategy_name}_{tf}"
            candle_id = result.get("candle_id")

            # Prevents multiple trades on the same candle
            if self.candle_lock.get(key) == candle_id:
                return

            self.candle_lock[key] = candle_id
            await dispatch_signal(result)

        except Exception as e:
            print(f"Error in {strategy_name} ({symbol} {tf}): {e}")

    async def _run(self, strategy_name):
        strategy_func = self.strategies[strategy_name]

        while True:
            # Create a list of tasks for parallel execution
            tasks = [
                self._process_symbol(strategy_func, strategy_name, s, t) 
                for s in self.symbols for t in self.timeframes
            ]
            
            if tasks:
                # Run all market checks concurrently
                await asyncio.gather(*tasks, return_exceptions=True)

            await asyncio.sleep(5)