#!/usr/bin/env python3
"""
Demo script for the Trading Agent Backtester
"""

import os
import sys
from datetime import datetime, timedelta

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def run_demo():
    """Run a complete demo of the trading agent"""
    print("🚀 Trading Agent Backtester - Demo")
    print("=" * 50)
    
    try:
        from dsl import DSL, Indicator, Signals, Risk
        from compiler_btp import compile_btp
        from data_fetcher import DataFetcher
        from backtest_runner import run_backtestingpy
        
        print("1️⃣ Creating strategy DSL...")
        
        # Create a more sophisticated strategy
        dsl = DSL(
            name="Golden Cross Strategy with ATR Stop",
            symbols=["SPY"],
            timeframe="1d",
            indicators=[
                Indicator(id="ema_fast", fn="EMA", params={"period": 20}),
                Indicator(id="ema_slow", fn="EMA", params={"period": 50}),
                Indicator(id="atr", fn="ATR", params={"period": 14})
            ],
            signals=Signals(
                entry_long="cross(ema_fast, ema_slow)",
                exit_long="cross_down(ema_fast, ema_slow)",
                entry_short="cross_down(ema_fast, ema_slow)",
                exit_short="cross(ema_fast, ema_slow)"
            ),
            risk=Risk(
                risk_per_trade_pct=2.0,
                stop="atr * 2",
                take_profit="2R"
            ),
            framework="backtestingpy"
        )
        
        print(f"   Strategy: {dsl.name}")
        print(f"   Symbols: {dsl.symbols}")
        print(f"   Timeframe: {dsl.timeframe}")
        print(f"   Risk per trade: {dsl.risk.risk_per_trade_pct}%")
        
        print("\n2️⃣ Compiling strategy to code...")
        
        code = compile_btp(dsl)
        print(f"   Generated {len(code)} characters of code")
        print("   ✅ Code compilation successful")
        
        print("\n3️⃣ Fetching market data...")
        
        fetcher = DataFetcher()
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)  # 1 year of data
        
        df = fetcher.fetch_data(
            symbol="SPY",
            start=start_date.isoformat(),
            end=end_date.isoformat(),
            timeframe="1d"
        )
        
        print(f"   Fetched {df.shape[0]} data points")
        print(f"   Date range: {df.index[0].strftime('%Y-%m-%d')} to {df.index[-1].strftime('%Y-%m-%d')}")
        
        # Save data
        csv_path = fetcher.save_to_csv(df, "SPY", "1d")
        print(f"   Data saved to: {csv_path}")
        
        print("\n4️⃣ Running backtest...")
        
        result = run_backtestingpy(csv_path, code, "1d")
        
        if result["ok"]:
            print("   ✅ Backtest completed successfully!")
            
            metrics = result["metrics"]
            summary = metrics.get("summary", {})
            
            print(f"\n📊 Results Summary:")
            print(f"   Starting Portfolio: ${summary.get('pv_start', 100000):,.2f}")
            print(f"   Final Portfolio: ${result['final_value']:,.2f}")
            print(f"   Total Return: {summary.get('strategy_return_pct', 0):.2f}%")
            print(f"   Max Drawdown: {summary.get('strategy_max_dd_pct', 0):.2f}%")
            print(f"   Sharpe Ratio: {metrics.get('sharpe', 0):.2f}")
            print(f"   Win Rate: {summary.get('win_rate_pct', 0):.1f}%")
            print(f"   Total Trades: {summary.get('total_trades', 0)}")
            
            # Show some trades
            trades = result.get("trades", [])
            if trades:
                print(f"\n📈 Recent Trades:")
                for i, trade in enumerate(trades[-5:]):  # Last 5 trades
                    print(f"   {i+1}. {trade['type'].upper()} at ${trade['price']:.2f} - P&L: {trade['pnl']:.2f}%")
            
        else:
            print(f"   ❌ Backtest failed: {result['error']}")
            if 'traceback' in result:
                print(f"   Traceback: {result['traceback'][:200]}...")
        
        print("\n🎉 Demo completed!")
        print("\n💡 To run the full system:")
        print("   1. Set your OpenAI API key: export OPENAI_API_KEY=your_key")
        print("   2. Start the server: python3 main.py")
        print("   3. Open http://localhost:8000 in your browser")
        print("   4. Enter your strategy description and run backtests!")
        
        return True
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_demo()
    sys.exit(0 if success else 1) 