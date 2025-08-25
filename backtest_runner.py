import json
import traceback
import os
import sys
import signal
import resource
import time
import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, Optional
import backtrader as bt

logger = logging.getLogger(__name__)

def limit_resources(cpu_seconds=30, mem_mb=2048):
    """Limit CPU and memory usage"""
    try:
        # CPU time limit
        resource.setrlimit(resource.RLIMIT_CPU, (cpu_seconds, cpu_seconds))
        
        # Memory limit
        mem_bytes = mem_mb * 1024 * 1024
        resource.setrlimit(resource.RLIMIT_AS, (mem_bytes, mem_bytes))
    except Exception:
        pass  # Resource limits not available on all systems

def run_backtestingpy(csv_path: str, code_str: str, timeframe: str = "1h") -> Dict[str, Any]:
    """Run backtesting.py strategy in sandboxed environment"""
    
    try:
        # Set resource limits
        limit_resources()
        
        # Read and prepare data
        df = pd.read_csv(csv_path, parse_dates=True, index_col=0).sort_index()
        
        # Ensure required columns exist
        required_cols = ['Open', 'High', 'Low', 'Close']
        if not all(col in df.columns for col in required_cols):
            # Try to find alternative column names
            col_mapping = {
                'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close',
                'o': 'Open', 'h': 'High', 'l': 'Low', 'c': 'Close'
            }
            for old_col, new_col in col_mapping.items():
                if old_col in df.columns:
                    df[new_col] = df[old_col]
        
        # Add Volume column if missing
        if 'Volume' not in df.columns:
            df['Volume'] = 1000000  # Default volume
        
        # Clean data
        df = df.dropna()
        if len(df) < 100:  # Need minimum data
            raise ValueError("Insufficient data for backtesting")
        
        # Execute the strategy code
        namespace = {}
        exec(code_str, namespace, namespace)
        
        # Get the strategy class
        if 'GeneratedStrategy' not in namespace:
            raise ValueError("GeneratedStrategy class not found in code")
        
        StrategyClass = namespace['GeneratedStrategy']
        
        # Run backtest
        bt = Backtest(
            df, 
            StrategyClass, 
            cash=100000, 
            commission=0.001,  # 0.1% commission
            exclusive_orders=True
        )
        
        # Run optimization (single run)
        stats = bt.run()
        
        # Extract metrics
        metrics = {
            "sharpe": stats.get('Sharpe Ratio', 0),
            "drawdown": {
                "max": {"drawdown": stats.get('Max. Drawdown [%]', 0)},
                "drawdown": stats.get('Max. Drawdown [%]', 0)
            },
            "returns": {
                "rtot": stats.get('Return [%]', 0) / 100,
                "rtot100": stats.get('Return [%]', 0)
            },
            "trades": {
                "total": {
                    "closed": stats.get('# Trades', 0),
                    "total": stats.get('# Trades', 0)
                }
            },
            "sqn": {
                "sqn": stats.get('SQN', 0)
            },
            "summary": {
                "pv_start": 100000,
                "pv_end": stats.get('Equity Final [$]', 100000),
                "strategy_return_pct": stats.get('Return [%]', 0),
                "buy_hold_return_pct": stats.get('Buy & Hold Return [%]', 0),
                "strategy_vs_buy_hold_pct": stats.get('Return [%]', 0) - stats.get('Buy & Hold Return [%]', 0),
                "strategy_max_dd_pct": stats.get('Max. Drawdown [%]', 0),
                "buy_hold_max_dd_pct": stats.get('Buy & Hold Max. Drawdown [%]', 0),
                "drawdown_diff_pct": stats.get('Max. Drawdown [%]', 0) - stats.get('Buy & Hold Max. Drawdown [%]', 0),
                "win_rate_pct": stats.get('Win Rate [%]', 0),
                "total_trades": stats.get('# Trades', 0),
                "won_trades": int(stats.get('# Trades', 0) * stats.get('Win Rate [%]', 0) / 100),
                "lost_trades": int(stats.get('# Trades', 0) * (100 - stats.get('Win Rate [%]', 0)) / 100),
                "avg_pnl_per_trade": stats.get('Avg. Trade [%]', 0),
                "largest_win": stats.get('Best Trade [%]', 0),
                "largest_loss": stats.get('Worst Trade [%]', 0)
            }
        }
        
        # Get trade history
        trades = []
        if hasattr(bt, '_trades') and bt._trades:
            for trade in bt._trades:
                if trade.is_closed:
                    trades.append({
                        "time": trade.exit_time.isoformat() if hasattr(trade, 'exit_time') else "",
                        "type": "buy" if trade.is_long else "sell",
                        "size": trade.size,
                        "price": trade.exit_price,
                        "pnl": trade.pl_pct
                    })
        
        # Get equity curve for charting
        equity_curve = bt._equity_curve if hasattr(bt, '_equity_curve') else None
        
        return {
            "ok": True,
            "metrics": metrics,
            "trades": trades,
            "equity_curve": equity_curve,
            "final_value": stats.get('Equity Final [$]', 100000)
        }
        
    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }

def run_backtrader(csv_path: str, code_str: str, timeframe: str = "1h", initial_capital: float = 100000.0) -> Dict[str, Any]:
    """Run backtrader strategy - more robust than backtesting.py"""
    
    logger.info(f"Starting backtrader with initial capital: {initial_capital}")
    
    try:
        # Set resource limits
        limit_resources()
        
        # Read and prepare data
        df = pd.read_csv(csv_path, parse_dates=True, index_col=0).sort_index()
        
        # Ensure proper datetime index
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)
        
        # Convert to naive UTC if timezone-aware
        if df.index.tz is not None:
            df = df.tz_convert("UTC").tz_localize(None)
        
        # Backtrader expects specific column names: open, high, low, close, volume
        # But it's flexible and can handle variations
        col_mapping = {
            'open': 'open', 'high': 'high', 'low': 'low', 'close': 'close', 'volume': 'volume',
            'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close', 'Volume': 'volume'
        }
        
        # Rename columns to lowercase (backtrader standard)
        for old_col, new_col in col_mapping.items():
            if old_col in df.columns:
                df[new_col] = df[old_col]
        
        # Ensure we have the required columns
        required_cols = ['open', 'high', 'low', 'close']
        if not all(col in df.columns for col in required_cols):
            raise ValueError(f"Missing required columns. Available: {list(df.columns)}")
        
        # Add volume if missing
        if 'volume' not in df.columns:
            df['volume'] = 1000000  # Default volume
        
        # Clean data
        df = df.dropna()
        if len(df) < 100:  # Need minimum data
            raise ValueError("Insufficient data for backtesting")
        
        # Execute the strategy code
        namespace = {}
        exec(code_str, namespace, namespace)
        
        # Get the strategy class
        if 'GeneratedStrategy' not in namespace:
            raise ValueError("GeneratedStrategy class not found in code")
        
        StrategyClass = namespace['GeneratedStrategy']
        
        # Create backtrader engine
        cerebro = bt.Cerebro()
        
        # Add data feed - Backtrader expects specific column names
        data_feed = bt.feeds.PandasData(
            dataname=df,
            datetime=None,  # Use index as datetime
            open='open',
            high='high',
            low='low',
            close='close',
            volume='volume',
            openinterest=None
        )
        cerebro.adddata(data_feed)
        
        # Add strategy
        cerebro.addstrategy(StrategyClass)
        
        # Set initial cash
        cerebro.broker.setcash(initial_capital)
        
        # Set commission
        cerebro.broker.setcommission(commission=0.001)
        
        # Add analyzers
        cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
        cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
        cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
        cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
        cerebro.addanalyzer(bt.analyzers.SQN, _name='sqn')
        
        # Run backtest
        results = cerebro.run()
        strat = results[0]
        
        # Extract metrics
        metrics = {}
        try:
            # Sharpe Ratio
            sharpe = strat.analyzers.sharpe.get_analysis()
            metrics["sharpe"] = sharpe.get('sharperatio', 0)
            
            # Drawdown
            drawdown = strat.analyzers.drawdown.get_analysis()
            metrics["drawdown"] = {
                "max": {"drawdown": drawdown.get('max', {}).get('drawdown', 0)},
                "drawdown": drawdown.get('max', {}).get('drawdown', 0)
            }
            
            # Returns
            returns = strat.analyzers.returns.get_analysis()
            metrics["returns"] = {
                "rtot": returns.get('rtot', 0),
                "rtot100": returns.get('rtot100', 0)
            }
            
            # Trades
            trade_analysis = strat.analyzers.trades.get_analysis()
            total_trades = trade_analysis.get('total', {}).get('total', 0)
            metrics["trades"] = {
                "total": {
                    "closed": total_trades,
                    "total": total_trades
                }
            }
            
            # SQN
            sqn = strat.analyzers.sqn.get_analysis()
            metrics["sqn"] = {
                "sqn": sqn.get('sqn', 0)
            }
            
            # Summary
            final_value = cerebro.broker.getvalue()
            metrics["summary"] = {
                "pv_start": initial_capital,
                "pv_end": final_value,
                "strategy_return_pct": returns.get('rtot100', 0),
                "buy_hold_return_pct": 0,  # Would need to calculate separately
                "strategy_vs_buy_hold_pct": returns.get('rtot100', 0),
                "strategy_max_dd_pct": drawdown.get('max', {}).get('drawdown', 0),
                "buy_hold_max_dd_pct": 0,  # Would need to calculate separately
                "drawdown_diff_pct": drawdown.get('max', {}).get('drawdown', 0),
                "win_rate_pct": trade_analysis.get('won', {}).get('total', 0) / max(total_trades, 1) * 100,
                "total_trades": total_trades,
                "won_trades": trade_analysis.get('won', {}).get('total', 0),
                "lost_trades": trade_analysis.get('lost', {}).get('total', 0),
                "avg_pnl_per_trade": 0,  # Would need to calculate from trade details
                "largest_win": trade_analysis.get('won', {}).get('pnl', {}).get('max', 0),
                "largest_loss": trade_analysis.get('lost', {}).get('pnl', {}).get('max', 0)
            }
            
        except Exception as e:
            logger.warning(f"Error extracting metrics: {e}")
            # Provide basic metrics
            metrics = {
                "sharpe": 0,
                "drawdown": {"max": {"drawdown": 0}, "drawdown": 0},
                "returns": {"rtot": 0, "rtot100": 0},
                "trades": {"total": {"closed": 0, "total": 0}},
                "sqn": {"sqn": 0},
                "summary": {
                    "pv_start": initial_capital,
                    "pv_end": cerebro.broker.getvalue(),
                    "strategy_return_pct": 0,
                    "buy_hold_return_pct": 0,
                    "strategy_vs_buy_hold_pct": 0,
                    "strategy_max_dd_pct": 0,
                    "buy_hold_max_dd_pct": 0,
                    "drawdown_diff_pct": 0,
                    "win_rate_pct": 0,
                    "total_trades": 0,
                    "won_trades": 0,
                    "lost_trades": 0,
                    "avg_pnl_per_trade": 0,
                    "largest_win": 0,
                    "largest_loss": 0
                }
            }
        
        # Get trade history
        trades = []
        try:
            # Check if there are any trades in the strategy
            if hasattr(strat, 'trades') and strat.trades:
                for trade in strat.trades:
                    if isinstance(trade, dict) and trade.get('status') == 'completed':
                        trades.append({
                            "time": trade.get('timestamp', '').isoformat() if hasattr(trade.get('timestamp', ''), 'isoformat') else str(trade.get('timestamp', '')),
                            "type": trade.get('type', 'unknown'),
                            "size": trade.get('size', 0),
                            "price": trade.get('price', 0),
                            "pnl": trade.get('pnl', 0)
                        })
            # Also check Backtrader's built-in trade tracking
            elif hasattr(strat, '_trades') and strat._trades:
                for trade in strat._trades:
                    if hasattr(trade, 'status') and trade.status == trade.Closed:
                        trades.append({
                            "time": trade.dtclose.isoformat() if hasattr(trade, 'dtclose') else "",
                            "type": "buy" if trade.isclosed else "sell",
                            "size": trade.size,
                            "price": trade.price,
                            "pnl": trade.pnl
                        })
            else:
                logger.info("No trades were executed by the strategy")
        except Exception as e:
            logger.warning(f"Could not extract trade history: {e}")
        
        return {
            "ok": True,
            "metrics": metrics,
            "trades": trades,
            "equity_curve": None,  # Backtrader doesn't provide this directly
            "final_value": cerebro.broker.getvalue()
        }
        
    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        } 