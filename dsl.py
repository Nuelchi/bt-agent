from pydantic import BaseModel, validator
from typing import List, Dict, Any, Optional, Literal

class Indicator(BaseModel):
    id: str
    fn: Literal["SMA", "EMA", "WMA", "RSI", "MACD", "ATR", "BBANDS", "STOCH", "ADX", "VWAP"]
    params: Dict[str, Any] = {}

class Session(BaseModel):
    start: str
    end: str
    tz: str = "UTC"

class Signals(BaseModel):
    entry_long: Optional[str] = None
    exit_long: Optional[str] = None
    entry_short: Optional[str] = None
    exit_short: Optional[str] = None

class Risk(BaseModel):
    risk_per_trade_pct: float = 1.0
    stop: Optional[str] = None
    take_profit: Optional[str] = None

class DSL(BaseModel):
    name: str
    symbols: List[str]
    timeframe: str
    indicators: List[Indicator] = []
    signals: Signals
    risk: Risk = Risk()
    constraints: Dict[str, Any] = {}
    framework: Literal["backtrader", "backtestingpy"] = "backtestingpy"

    @validator("timeframe")
    def valid_tf(cls, v):
        # Allowed: "1m", "5m", "15m", "1h", "4h", "1d"
        assert any(v.endswith(s) for s in ["m", "h", "d"]), "Bad timeframe"
        return v 