import json
import re
from typing import Optional
from dsl import DSL

# Map indicator names to backtrader functions
BTP_IND_MAP = {
    "EMA": "bt.indicators.EMA",
    "SMA": "bt.indicators.SMA", 
    "WMA": "bt.indicators.WMA",
    "ATR": "bt.indicators.ATR",
    "RSI": "bt.indicators.RSI",
    "MACD": "bt.indicators.MACD",
    "BBANDS": "bt.indicators.BBands",
    "STOCH": "bt.indicators.Stochastic",
    "ADX": "bt.indicators.ADX",
    "VWAP": "bt.indicators.VWAP"
}

def compile_btp(dsl: DSL) -> str:
    """Compile DSL to backtrader strategy"""
    
    # Helper function to convert expressions
    def conv(expr):
        if not expr:
            return "False"
        e = expr
        # Convert cross(a,b) to backtrader-compatible crossover logic
        e = e.replace("cross(", "self._cross_over(")
        # Convert cross_down(a,b) to backtrader-compatible crossunder logic
        e = e.replace("cross_down(", "self._cross_under(")
        # Replace indicator references
        for ind in dsl.indicators:
            e = e.replace(ind.id, f"self.ind['{ind.id}']")
        return e
    
    # Convert signals
    entry_long = conv(dsl.signals.entry_long or "")
    entry_short = conv(dsl.signals.entry_short or "")
    exit_long = conv(dsl.signals.exit_long or "")
    exit_short = conv(dsl.signals.exit_short or "")
    
    # Build indicator initialization
    indicator_code = ""
    for ind in dsl.indicators:
        if ind.fn in ["EMA", "SMA"]:
            period = ind.params.get("period", 20)
            indicator_code += f"        self.ind['{ind.id}'] = {BTP_IND_MAP[ind.fn]}(self.data.close, period={period})\n"
        elif ind.fn == "ATR":
            period = ind.params.get("period", 14)
            indicator_code += f"        self.ind['{ind.id}'] = {BTP_IND_MAP[ind.fn]}(self.data, period={period})\n"
        elif ind.fn == "RSI":
            period = ind.params.get("period", 14)
            indicator_code += f"        self.ind['{ind.id}'] = {BTP_IND_MAP[ind.fn]}(self.data.close, period={period})\n"
        elif ind.fn == "MACD":
            fast = ind.params.get("fast", 12)
            slow = ind.params.get("slow", 26)
            signal = ind.params.get("signal", 9)
            indicator_code += f"        macd = {BTP_IND_MAP[ind.fn]}(self.data.close, period_me1={fast}, period_me2={slow}, period_signal={signal})\n"
            indicator_code += f"        self.ind['macd_line'] = macd.macd\n"
            indicator_code += f"        self.ind['signal_line'] = macd.signal\n"
            indicator_code += f"        self.ind['histogram'] = macd.histo\n"
        elif ind.fn == "BBANDS":
            period = ind.params.get("period", 20)
            std = ind.params.get("std", 2)
            indicator_code += f"        bb = {BTP_IND_MAP[ind.fn]}(self.data.close, period={period}, devfactor={std})\n"
            indicator_code += f"        self.ind['bb_upper'] = bb.lines.top\n"
            indicator_code += f"        self.ind['bb_middle'] = bb.lines.mid\n"
            indicator_code += f"        self.ind['bb_lower'] = bb.lines.bot\n"
        elif ind.fn == "STOCH":
            period = ind.params.get("period", 14)
            indicator_code += f"        stoch = {BTP_IND_MAP[ind.fn]}(self.data, period={period})\n"
            indicator_code += f"        self.ind['stoch_k'] = stoch.lines.percK\n"
            indicator_code += f"        self.ind['stoch_d'] = stoch.lines.percD\n"
        elif ind.fn == "ADX":
            period = ind.params.get("period", 14)
            indicator_code += f"        adx = {BTP_IND_MAP[ind.fn]}(self.data, period={period})\n"
            indicator_code += f"        self.ind['adx'] = adx.lines.adx\n"
            indicator_code += f"        self.ind['di_plus'] = adx.lines.dip\n"
            indicator_code += f"        self.ind['di_minus'] = adx.lines.dim\n"
        elif ind.fn == "VWAP":
            period = ind.params.get("period", 14)
            indicator_code += f"        self.ind['{ind.id}'] = {BTP_IND_MAP[ind.fn]}(self.data, period={period})\n"
    
    code = f'''import backtrader as bt

class GeneratedStrategy(bt.Strategy):
    def __init__(self):
        self.ind = {{}}
        self.order = None
        self.trades = []
        self.trade_count = 0
{indicator_code}
    
    def _cross_over(self, a, b):
        """Check if a crosses over b (a > b and a_prev <= b_prev)"""
        if len(a) < 2 or len(b) < 2:
            return False
        return a[0] > b[0] and a[-1] <= b[-1]
    
    def _cross_under(self, a, b):
        """Check if a crosses under b (a < b and a_prev >= b_prev)"""
        if len(a) < 2 or len(b) < 2:
            return False
        return a[0] < b[0] and a[-1] >= b[-1]
    
    def next(self):
        # Exit conditions
        if {exit_long} and self.position.size > 0:
            self.close()
            return
            
        if {exit_short} and self.position.size < 0:
            self.close()
            return
        
        # Entry logic - ensure we execute trades
        # For a simple buy and hold strategy, buy on the first bar if we have no position
        if self.position.size == 0 and self.order is None:
            # Buy with available cash
            cash = self.broker.getcash()
            if cash > 0:
                # Buy with 95% of available cash
                size = int(cash * 0.95 / self.data.close[0])
                if size > 0:
                    self.order = self.buy(size=size)
                    print(f"BUY order placed: {{size}} shares at {{self.data.close[0]}}")
                    print(f"Available cash: {{cash}}, Price: {{self.data.close[0]}}")
        
        # Also check the original entry conditions if they're more specific
        elif {entry_long} and self.position.size == 0 and self.order is None:
            # Buy with available cash
            cash = self.broker.getcash()
            if cash > 0:
                # Buy with 95% of available cash
                size = int(cash * 0.95 / self.data.close[0])
                if size > 0:
                    self.order = self.buy(size=size)
                    print(f"BUY order placed (condition): {{size}} shares at {{self.data.close[0]}}")
            
        elif {entry_short} and self.position.size == 0 and self.order is None:
            # Sell short with available cash
            cash = self.broker.getcash()
            if cash > 0:
                # Sell short with 95% of available cash
                size = int(cash * 0.95 / self.data.close[0])
                if size > 0:
                    self.order = self.sell(size=size)
                    print(f"SELL order placed (condition): {{size}} shares at {{self.data.close[0]}}")
    
    def notify_order(self, order):
        if order.status in [order.Completed]:
            if order.isbuy():
                print(f"BUY executed: {{order.size}} shares at {{order.executed.price}}")
                # Record the trade
                self.trades.append({{
                    'id': f"trade_{{self.trade_count}}",
                    'type': 'buy',
                    'size': order.size,
                    'price': order.executed.price,
                    'timestamp': self.data.datetime.datetime(),
                    'status': 'completed'
                }})
                self.trade_count += 1
            elif order.issell():
                print(f"SELL executed: {{order.size}} shares at {{order.executed.price}}")
                # Record the trade
                self.trades.append({{
                    'id': f"trade_{{self.trade_count}}",
                    'type': 'sell',
                    'size': order.size,
                    'price': order.executed.price,
                    'timestamp': self.data.datetime.datetime(),
                    'status': 'completed'
                }})
                self.trade_count += 1
            self.order = None
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            print(f"Order canceled/margin/rejected: {{order.status}}")
            self.order = None
    
    def notify_trade(self, trade):
        """Called when a trade is completed (position closed)"""
        if trade.isclosed:
            print(f"Trade closed: {{trade.dtopen}} to {{trade.dtclose}}")
            print(f"Size: {{trade.size}}, Price: {{trade.price}}, PnL: {{trade.pnl}}")
            
            # Update the trade record with close information
            if self.trades:
                last_trade = self.trades[-1]
                last_trade['close_timestamp'] = trade.dtclose
                last_trade['pnl'] = trade.pnl
                last_trade['commission'] = trade.commission
'''
    
    return code 