import json
import re
from typing import Optional
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from dsl import DSL

class StrategyTranslator:
    def __init__(self, api_key: str = None):
        # Use OpenRouter API key if provided, otherwise fall back to environment variable
        if api_key:
            self.api_key = api_key
        else:
            import os
            self.api_key = os.getenv("OPENAI_API_KEY")
        
        if not self.api_key:
            raise ValueError("API key is required")
        
        # Configure for OpenRouter
        self.llm = ChatOpenAI(
            model="anthropic/claude-3.5-sonnet",  # Use OpenRouter's Claude endpoint
            openai_api_key=self.api_key,
            openai_api_base="https://openrouter.ai/api/v1",  # OpenRouter API endpoint
            temperature=0.1
        )
        
    def detect_language(self, text: str) -> str:
        """Detect if input is Pine Script, MQL, or natural language"""
        text_lower = text.lower()
        
        if "//@version" in text_lower or "strategy(" in text_lower:
            return "pine"
        elif any(keyword in text_lower for keyword in ["ontick", "ima", "ordersend", "expert"]):
            return "mql"
        else:
            return "natural"
    
    def translate_to_dsl(self, strategy_text: str, preferred_framework: str = "backtrader") -> DSL:
        """Translate strategy text to DSL using LLM"""
        
        language = self.detect_language(strategy_text)
        
        system_prompt = f"""You are a trading strategy translator. Convert the given strategy into a strict JSON DSL format.

Rules:
- Only output valid JSON that matches this exact schema:
{{
  "name": "strategy name",
  "symbols": ["symbol1", "symbol2"],
  "timeframe": "1h",
  "indicators": [
    {{"id": "indicator_name", "fn": "EMA", "params": {{"period": 20}}}}
  ],
  "signals": {{
    "entry_long": "cross(ema_fast, ema_slow)",
    "exit_long": "cross_down(ema_fast, ema_slow)",
    "entry_short": "cross_down(ema_fast, ema_slow)",
    "exit_short": "cross(ema_fast, ema_slow)"
  }},
  "risk": {{
    "risk_per_trade_pct": 1.0,
    "stop": "atr * 2",
    "take_profit": "2R"
  }},
  "constraints": {{}},
  "framework": "{preferred_framework}"
}}

- Use only these indicator functions: SMA, EMA, WMA, RSI, MACD, ATR, BBANDS, STOCH, ADX, VWAP
- Signal expressions can use: cross(a,b), cross_down(a,b), and, or, not, True, False
- Risk: "2R" means 2x risk, "pips:30" for fixed pips, "atr*X" for ATR multiplier
- Timeframes: 1m, 5m, 15m, 1h, 4h, 1d
- Framework: {preferred_framework} (Note: This generates backtrader code, not backtesting.py)

Input language detected: {language}

Output only the JSON, no explanations."""

        user_prompt = f"Translate this trading strategy:\n\n{strategy_text}"
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        try:
            response = self.llm.invoke(messages)
            json_str = response.content.strip()
            
            # Clean up any markdown formatting
            if json_str.startswith("```json"):
                json_str = json_str[7:]
            if json_str.endswith("```"):
                json_str = json_str[:-3]
            
            json_str = json_str.strip()
            
            # Parse and validate
            data = json.loads(json_str)
            dsl = DSL(**data)
            return dsl
            
        except Exception as e:
            raise Exception(f"Translation failed: {str(e)}")
    
    def repair_dsl(self, error_message: str, traceback: str, code: str) -> str:
        """Repair failed code using LLM"""
        
        repair_prompt = f"""You are fixing a {code.split('class ')[1].split('(')[0]} strategy class.

ERROR: {error_message}
TRACEBACK: {traceback}
CODE: {code}

Rules:
- Keep class name as is
- Do not remove analyzers usage assumptions (they are added outside)
- Use only public APIs
- Fix the specific error mentioned

Output only the corrected Python code, no explanations."""

        messages = [
            SystemMessage(content=repair_prompt),
            HumanMessage(content="Please fix this code.")
        ]
        
        try:
            response = self.llm.invoke(messages)
            return response.content.strip()
        except Exception as e:
            raise Exception(f"Repair failed: {str(e)}") 