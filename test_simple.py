#!/usr/bin/env python3

import pandas as pd
from backtesting import Backtest
from backtesting.lib import crossover

# Create a simple strategy class
from backtesting import Strategy

class SimpleStrategy(Strategy):
    def init(self):
        pass
    
    def next(self):
        if not self.position:
            self.buy()

# Create simple test data
dates = pd.date_range('2024-01-01', periods=100, freq='D')
data = pd.DataFrame({
    'Open': [100] * 100,
    'High': [101] * 100,
    'Low': [99] * 100,
    'Close': [100.5] * 100,
    'Volume': [1000000] * 100
}, index=dates)

print("Data shape:", data.shape)
print("Data columns:", data.columns.tolist())
print("Data index type:", type(data.index))
print("First few rows:")
print(data.head())

try:
    # Test backtest
    bt = Backtest(data, SimpleStrategy, cash=100000, commission=0.001)
    stats = bt.run()
    print("Backtest successful!")
    print("Final value:", stats['Equity Final [$]'])
except Exception as e:
    print("Backtest failed with error:", str(e))
    import traceback
    traceback.print_exc() 