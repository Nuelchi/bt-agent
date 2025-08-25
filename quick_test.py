#!/usr/bin/env python3
"""
Quick test of the OpenRouter integration
"""

from translator import StrategyTranslator
from compiler_btp import compile_btp

def test_strategy_translation():
    """Test translating a natural language strategy to DSL"""
    
    # Initialize translator with OpenRouter API key
    api_key = "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"
    translator = StrategyTranslator(api_key=api_key)
    
    # Test strategy description
    strategy_text = """
    Create a simple moving average crossover strategy that:
    - Buys when the 20-period SMA crosses above the 50-period SMA
    - Sells when the 20-period SMA crosses below the 50-period SMA
    - Uses 1% risk per trade
    - Has an ATR-based stop loss
    - Trades EUR/USD on 1-hour timeframe
    """
    
    print("🧪 Testing OpenRouter strategy translation...")
    print(f"Strategy: {strategy_text.strip()}")
    print("-" * 50)
    
    try:
        # Translate to DSL
        dsl = translator.translate_to_dsl(strategy_text, preferred_framework="backtestingpy")
        
        print("✅ Strategy translated successfully!")
        print(f"   Name: {dsl.name}")
        print(f"   Symbols: {dsl.symbols}")
        print(f"   Timeframe: {dsl.timeframe}")
        print(f"   Framework: {dsl.framework}")
        print(f"   Indicators: {len(dsl.indicators)}")
        print(f"   Entry Long: {dsl.signals.entry_long}")
        print(f"   Exit Long: {dsl.signals.exit_long}")
        print(f"   Risk: {dsl.risk.risk_per_trade_pct}%")
        
        # Test compilation
        print("\n🧪 Testing code compilation...")
        code = compile_btp(dsl)
        print("✅ Code compiled successfully!")
        print(f"   Code length: {len(code)} characters")
        
        # Show first few lines
        lines = code.split('\n')[:10]
        print("   First 10 lines:")
        for i, line in enumerate(lines, 1):
            print(f"   {i:2d}: {line}")
        
        print("\n🎉 OpenRouter integration test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_strategy_translation() 