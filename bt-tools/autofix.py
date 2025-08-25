from typing import Dict, Any, Callable
from translator import StrategyTranslator
from backtest_runner import run_backtestingpy, run_backtrader

def try_run_with_autofix(dsl, compile_fn, csv_path: str, llm: StrategyTranslator, max_attempts: int = 3) -> Dict[str, Any]:
    """Try to run strategy with automatic LLM repair on failure"""
    
    attempts = []
    
    # First attempt
    code = compile_fn(dsl)
    
    for attempt_num in range(max_attempts):
        # Choose runner based on framework
        if dsl.framework == "backtrader":
            result = run_backtrader(csv_path, code, dsl.timeframe)
        else:
            result = run_backtestingpy(csv_path, code, dsl.timeframe)
        
        if result["ok"]:
            return {
                "success": True,
                "code": code,
                "metrics": result.get("metrics", {}),
                "trades": result.get("trades", []),
                "equity_curve": result.get("equity_curve"),
                "final_value": result.get("final_value"),
                "attempts": attempts
            }
        
        # Record failed attempt
        attempts.append({
            "attempt": attempt_num + 1,
            "error": result["error"],
            "traceback": result["traceback"],
            "code": code
        })
        
        if attempt_num < max_attempts - 1:
            # Try to repair with LLM
            try:
                prompt = f"""You are fixing a {dsl.framework} strategy class named GeneratedStrategy.

ERROR: {result['error']}
TRACEBACK: {result['traceback']}
CODE: {code}

Rules:
- Keep class name GeneratedStrategy
- Do not remove analyzers usage assumptions (they are added outside)
- Use only {dsl.framework} public APIs
- Fix the specific error mentioned

Output only the corrected Python code, no explanations."""
                
                code = llm.repair_dsl(result["error"], result["traceback"], code)
                
            except Exception as repair_error:
                # If repair fails, add to attempts and continue
                attempts.append({
                    "attempt": f"{attempt_num + 1}_repair_failed",
                    "error": f"Repair failed: {str(repair_error)}",
                    "traceback": "",
                    "code": code
                })
                break
    
    # All attempts failed
    return {
        "success": False,
        "attempts": attempts,
        "error": f"Failed after {max_attempts} attempts"
    } 