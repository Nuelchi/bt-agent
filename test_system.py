#!/usr/bin/env python3
"""
Test script for the Trading Agent Backtester
"""

import os
import sys
from datetime import datetime, timedelta

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_dsl():
    """Test DSL creation"""
    print("🧪 Testing DSL creation...")
    try:
        from dsl import DSL, Indicator, Signals, Risk
        
        # Create a simple DSL
        dsl = DSL(
            name="Test EMA Strategy",
            symbols=["EUR/USD"],
            timeframe="1h",
            indicators=[
                Indicator(id="ema_fast", fn="EMA", params={"period": 20}),
                Indicator(id="ema_slow", fn="EMA", params={"period": 50})
            ],
            signals=Signals(
                entry_long="cross(ema_fast, ema_slow)",
                exit_long="cross_down(ema_fast, ema_slow)"
            ),
            risk=Risk(risk_per_trade_pct=1.0, stop="atr * 2"),
            framework="backtestingpy"
        )
        
        print(f"✅ DSL created: {dsl.name}")
        print(f"   Symbols: {dsl.symbols}")
        print(f"   Timeframe: {dsl.timeframe}")
        print(f"   Framework: {dsl.framework}")
        return dsl
        
    except Exception as e:
        print(f"❌ DSL test failed: {e}")
        return None

def test_compiler(dsl):
    """Test code compilation"""
    print("\n🧪 Testing code compilation...")
    try:
        from compiler_btp import compile_btp
        
        code = compile_btp(dsl)
        print("✅ Code compiled successfully")
        print(f"   Code length: {len(code)} characters")
        
        # Check if key elements are present
        assert "class GeneratedStrategy" in code
        assert "def next(self):" in code
        assert "self.buy(" in code
        
        print("✅ Generated code contains required elements")
        return code
        
    except Exception as e:
        print(f"❌ Compiler test failed: {e}")
        return None

def test_data_fetcher():
    """Test data fetching"""
    print("\n🧪 Testing data fetcher...")
    try:
        from data_fetcher import DataFetcher
        
        fetcher = DataFetcher()
        
        # Test with a simple symbol
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        df = fetcher.fetch_data(
            symbol="AAPL",
            start=start_date.isoformat(),
            end=end_date.isoformat(),
            timeframe="1d"
        )
        
        print(f"✅ Data fetched successfully")
        print(f"   Shape: {df.shape}")
        print(f"   Columns: {list(df.columns)}")
        print(f"   Date range: {df.index[0]} to {df.index[-1]}")
        
        # Save to CSV for testing
        csv_path = fetcher.save_to_csv(df, "AAPL", "1d")
        print(f"   Saved to: {csv_path}")
        
        return csv_path
        
    except Exception as e:
        print(f"❌ Data fetcher test failed: {e}")
        return None

def test_backtest_runner(csv_path):
    """Test backtest execution"""
    print("\n🧪 Testing backtest execution...")
    try:
        from backtest_runner import run_backtestingpy
        
        # Simple test strategy
        test_code = '''
from backtesting import Strategy
from backtesting.lib import crossover
import pandas as pd

def SMA(series, n):
    return series.rolling(n).mean()

class GeneratedStrategy(Strategy):
    def init(self):
        self.sma20 = self.I(SMA, self.data.Close, 20)
        self.sma50 = self.I(SMA, self.data.Close, 50)
    
    def next(self):
        if not self.position and self.sma20[-1] > self.sma50[-1]:
            self.buy()
        elif self.position and self.sma20[-1] < self.sma50[-1]:
            self.position.close()
'''
        
        result = run_backtestingpy(csv_path, test_code, "1d")
        
        if result["ok"]:
            print("✅ Backtest executed successfully")
            print(f"   Final value: ${result['final_value']:.2f}")
            print(f"   Metrics: {len(result['metrics'])} items")
            print(f"   Trades: {len(result['trades'])} executed")
        else:
            print(f"❌ Backtest failed: {result['error']}")
            
        return result
        
    except Exception as e:
        print(f"❌ Backtest runner test failed: {e}")
        return None

def main():
    """Run all tests"""
    print("🚀 Trading Agent Backtester - System Test")
    print("=" * 50)
    
    # Test DSL
    dsl = test_dsl()
    if not dsl:
        return False
    
    # Test compiler
    code = test_compiler(dsl)
    if not code:
        return False
    
    # Test data fetcher
    csv_path = test_data_fetcher()
    if not csv_path:
        return False
    
    # Test backtest runner
    result = test_backtest_runner(csv_path)
    if not result:
        return False
    
    print("\n🎉 All tests passed! The system is working correctly.")
    print("\n💡 Next steps:")
    print("   1. Set your OpenAI API key: export OPENAI_API_KEY=your_key")
    print("   2. Run the server: python3 main.py")
    print("   3. Open http://localhost:8000 in your browser")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 