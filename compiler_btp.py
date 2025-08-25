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
    "VWAP": "bt.indicators.VWAP",
    "BB": "bt.indicators.BBands",
    "BOLLINGER": "bt.indicators.BBands"
}

def clean_expression(expr: str) -> str:
    """Clean and normalize expressions"""
    if not expr:
        return "False"
    
    # Remove extra whitespace and normalize
    expr = re.sub(r'\s+', ' ', expr.strip())
    
    # Handle common MQL/Pine Script patterns
    expr = expr.replace("&&", "and")
    expr = expr.replace("||", "or")
    expr = expr.replace("==", "==")
    expr = expr.replace("!=", "!=")
    expr = expr.replace("<=", "<=")
    expr = expr.replace(">=", ">=")
    
    # Handle function calls
    expr = re.sub(r'(\w+)\(', r'self._\1(', expr)
    
    # Handle array access
    expr = re.sub(r'(\w+)\[(\d+)\]', r'self.data.\1[\2]', expr)
    
    # Clean up any malformed expressions
    expr = re.sub(r'(\w+)_(\w+)_(\w+)', r'\1_\2_\3', expr)  # Fix double underscores
    
    return expr

def compile_btp(dsl: DSL) -> str:
    """Compile DSL to backtrader strategy"""
    
    # Track all indicators used
    used_indicators = set()
    
    # Helper function to convert expressions
    def conv(expr):
        if not expr:
            return "False"
        
        e = clean_expression(expr)
        
        # Handle common price/volume references
        price_volume_map = {
            "close": "self.data.close[0]",
            "volume": "self.data.volume[0]",
            "high": "self.data.high[0]",
            "low": "self.data.low[0]",
            "open": "self.data.open[0]",
            "price": "self.data.close[0]",
            "vol": "self.data.volume[0]",
            "c": "self.data.close[0]",
            "v": "self.data.volume[0]",
            "h": "self.data.high[0]",
            "l": "self.data.low[0]",
            "o": "self.data.open[0]"
        }
        
        for old, new in price_volume_map.items():
            e = re.sub(r'\b' + old + r'\b', new, e)
        
        # Handle indicator references - do this first to avoid conflicts
        for ind in dsl.indicators:
            # Replace both quoted and unquoted references
            e = re.sub(r'\b' + ind.id + r'\b', f"self.ind['{ind.id}']", e)
            used_indicators.add(ind.id)
        
        # Handle common indicator patterns - do this after individual indicators
        indicator_patterns = {
            r'bb_upper': "self.ind['bb_upper']",
            r'bb_lower': "self.ind['bb_lower']", 
            r'bb_middle': "self.ind['bb_middle']",
            r'bb_mid': "self.ind['bb_middle']",
            r'bb_top': "self.ind['bb_upper']",
            r'bb_bot': "self.ind['bb_lower']",
            r'vol_sma': "self.ind['vol_sma']",
            r'volume_sma': "self.ind['vol_sma']",
            r'atr': "self.ind['atr']",
            r'rsi': "self.ind['rsi']",
            r'macd': "self.ind['macd_line']",
            r'macd_signal': "self.ind['signal_line']",
            r'macd_hist': "self.ind['histogram']"
        }
        
        for pattern, replacement in indicator_patterns.items():
            e = re.sub(r'\b' + pattern + r'\b', replacement, e)
        
        # Clean up any malformed indicator references
        e = re.sub(r"self\.ind\['self\.ind\['([^']+)'\]'\]", r"self.ind['\1']", e)
        
        # Final cleanup - fix any remaining malformed patterns
        e = re.sub(r"self\.ind\['([^']+)'\]_([^']+)", r"self.ind['\1_\2']", e)
        e = re.sub(r"self\.data\.([^[]+)\[(\d+)\]_([^']+)", r"self.data.\1[\2]", e)
        
        return e
    
    # Convert signals
    entry_long = conv(dsl.signals.entry_long or "")
    entry_short = conv(dsl.signals.entry_short or "")
    exit_long = conv(dsl.signals.exit_long or "")
    exit_short = conv(dsl.signals.exit_short or "")
    
    # Build indicator initialization
    indicator_code = ""
    indicator_set = set()
    bb_created = False  # Track if BB indicators were already created
    
    for ind in dsl.indicators:
        if ind.id in indicator_set:
            continue
        indicator_set.add(ind.id)
        
        # Skip BB indicators if already created
        if ind.fn in ["BBANDS", "BB", "BOLLINGER"] and bb_created:
            continue
        
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
        elif ind.fn in ["BBANDS", "BB", "BOLLINGER"]:
            period = ind.params.get("period", 20)
            std = ind.params.get("std", 2)
            deviation = ind.params.get("deviation", 2)
            std = std if std else deviation
            indicator_code += f"        bb = {BTP_IND_MAP['BBANDS']}(self.data.close, period={period}, devfactor={std})\n"
            indicator_code += f"        self.ind['bb_upper'] = bb.lines.top\n"
            indicator_code += f"        self.ind['bb_middle'] = bb.lines.mid\n"
            indicator_code += f"        self.ind['bb_lower'] = bb.lines.bot\n"
            indicator_code += f"        self.ind['bb'] = bb.lines.mid\n"
            bb_created = True  # Mark that BB indicators were created
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
    
    # Add essential indicators that are commonly referenced
    if 'vol_sma' not in indicator_set:
        indicator_code += "        self.ind['vol_sma'] = bt.indicators.SMA(self.data.volume, period=10)\n"
    if 'bb_upper' not in indicator_set:
        indicator_code += "        bb = bt.indicators.BBands(self.data.close, period=20, devfactor=2)\n"
        indicator_code += "        self.ind['bb_upper'] = bb.lines.top\n"
        indicator_code += "        self.ind['bb_middle'] = bb.lines.mid\n"
        indicator_code += "        self.ind['bb_lower'] = bb.lines.bot\n"
        indicator_code += "        self.ind['bb'] = bb.lines.mid\n"
    if 'atr' not in indicator_set:
        indicator_code += "        self.ind['atr'] = bt.indicators.ATR(self.data, period=14)\n"
    
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
        try:
            return a[0] > b[0] and a[-1] <= b[-1]
        except:
            return False
    
    def _cross_under(self, a, b):
        """Check if a crosses under b (a < b and a_prev >= b_prev)"""
        try:
            return a[0] < b[0] and a[-1] >= b[-1]
        except:
            return False
    
    def _volume_high(self, threshold=1.5):
        """Check if current volume is above average"""
        try:
            avg_volume = sum([self.data.volume[-i] for i in range(1, 11)]) / 10
            return self.data.volume[0] > avg_volume * threshold
        except:
            return False
    
    def _calculate_position_size(self, stop_loss_pips, risk_percent=1.0):
        """Calculate position size based on risk"""
        try:
            risk_amount = self.broker.getcash() * (risk_percent / 100)
            position_size = risk_amount / stop_loss_pips
            return max(1, int(position_size))
        except:
            return 1000  # Default position size
    
    def next(self):
        # Exit conditions
        if {exit_long} and self.position.size > 0:
            self.close()
            return
            
        if {exit_short} and self.position.size < 0:
            self.close()
            return
        
        # Entry logic
        if self.position.size == 0 and self.order is None:
            # Long entry
            if {entry_long}:
                cash = self.broker.getcash()
                if cash > 0:
                    size = int(cash * 0.95 / self.data.close[0])
                    if size > 0:
                        self.order = self.buy(size=size)
                        print(f"BUY order placed: {{size}} shares at {{self.data.close[0]}}")
            
            # Short entry
            elif {entry_short}:
                cash = self.broker.getcash()
                if cash > 0:
                    size = int(cash * 0.95 / self.data.close[0])
                    if size > 0:
                        self.order = self.sell(size=size)
                        print(f"SELL order placed: {{size}} shares at {{self.data.close[0]}}")
    
    def notify_order(self, order):
        if order.status in [order.Completed]:
            if order.isbuy():
                print(f"BUY executed: {{order.size}} shares at {{order.executed.price}}")
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
            
            if self.trades:
                last_trade = self.trades[-1]
                last_trade['close_timestamp'] = trade.dtclose
                last_trade['pnl'] = trade.pnl
                last_trade['commission'] = trade.commission
'''
    
    return code 