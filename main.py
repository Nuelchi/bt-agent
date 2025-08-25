import json
import asyncio
from typing import Optional
from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging
from datetime import datetime, timedelta
from langchain.schema import HumanMessage

from translator import StrategyTranslator
from compiler_btp import compile_btp
from backtest_runner import run_backtestingpy, run_backtrader
from data_fetcher import DataFetcher

def analyze_performance(metrics: dict) -> dict:
    """Analyze strategy performance and identify areas for improvement"""
    analysis = {
        "overall_score": 0,
        "strengths": [],
        "weaknesses": [],
        "risk_level": "medium",
        "recommendations": []
    }
    
    # Calculate overall score based on key metrics
    sharpe = metrics.get("sharpe", 0)
    drawdown = metrics.get("drawdown", {}).get("max", {}).get("drawdown", 0)
    returns = metrics.get("returns", {}).get("rtot100", 0)
    total_trades = metrics.get("trades", {}).get("total", {}).get("total", 0)
    
    # Score calculation (0-100)
    score = 0
    
    # Sharpe ratio scoring (0-25 points)
    if sharpe > 1.0:
        score += 25
        analysis["strengths"].append("Excellent risk-adjusted returns (Sharpe > 1.0)")
    elif sharpe > 0.5:
        score += 20
        analysis["strengths"].append("Good risk-adjusted returns (Sharpe > 0.5)")
    elif sharpe > 0:
        score += 10
        analysis["strengths"].append("Positive risk-adjusted returns")
    else:
        analysis["weaknesses"].append(f"Poor risk-adjusted returns (Sharpe: {sharpe:.2f})")
    
    # Drawdown scoring (0-25 points)
    if drawdown < 10:
        score += 25
        analysis["strengths"].append("Excellent risk management (Max DD < 10%)")
    elif drawdown < 20:
        score += 20
        analysis["strengths"].append("Good risk management (Max DD < 20%)")
    elif drawdown < 30:
        score += 15
        analysis["strengths"].append("Acceptable risk management (Max DD < 30%)")
    else:
        score += 5
        analysis["weaknesses"].append(f"High risk strategy (Max DD: {drawdown:.1f}%)")
    
    # Returns scoring (0-25 points)
    if returns > 20:
        score += 25
        analysis["strengths"].append("Excellent returns (>20%)")
    elif returns > 10:
        score += 20
        analysis["strengths"].append("Good returns (>10%)")
    elif returns > 5:
        score += 15
        analysis["strengths"].append("Moderate returns (>5%)")
    elif returns > 0:
        score += 10
        analysis["strengths"].append("Positive returns")
    else:
        analysis["weaknesses"].append(f"Negative returns ({returns:.1f}%)")
    
    # Trading activity scoring (0-25 points)
    if total_trades > 20:
        score += 25
        analysis["strengths"].append("High trading activity")
    elif total_trades > 10:
        score += 20
        analysis["strengths"].append("Good trading activity")
    elif total_trades > 5:
        score += 15
        analysis["strengths"].append("Moderate trading activity")
    else:
        score += 10
        analysis["weaknesses"].append("Low trading activity")
    
    analysis["overall_score"] = score
    
    # Determine risk level
    if drawdown > 40 or sharpe < -1:
        analysis["risk_level"] = "high"
    elif drawdown > 20 or sharpe < 0:
        analysis["risk_level"] = "medium"
    else:
        analysis["risk_level"] = "low"
    
    # Generate recommendations based on weaknesses
    if sharpe < 0:
        analysis["recommendations"].append("Improve risk-adjusted returns by adding stop-losses or position sizing")
    if drawdown > 30:
        analysis["recommendations"].append("Reduce maximum drawdown by implementing better risk management")
    if returns < 5:
        analysis["recommendations"].append("Enhance entry/exit signals for better profitability")
    if total_trades < 5:
        analysis["recommendations"].append("Increase trading frequency by relaxing entry conditions")
    
    return analysis

async def generate_optimization_suggestions(
    strategy: str,
    symbol: str,
    timeframe: str,
    current_performance: dict,
    optimization_goal: str,
    user_feedback: str = None,
    original_language: str = None
) -> dict:
    """Generate AI-powered optimization suggestions"""
    
    # Create optimization prompt based on goal and performance
    if optimization_goal == "improve_returns":
        goal_description = "improve overall returns and profitability"
    elif optimization_goal == "reduce_drawdown":
        goal_description = "reduce maximum drawdown and improve risk management"
    elif optimization_goal == "increase_sharpe":
        goal_description = "improve risk-adjusted returns (Sharpe ratio)"
    else:
        goal_description = "improve overall strategy performance"
    
    # Build the optimization prompt
    language_context = ""
    if original_language:
        if original_language.lower() == "pine":
            language_context = f"\nNote: The original strategy is in Pine Script. Provide suggestions that can be implemented in Pine Script syntax."
        elif original_language.lower() == "mql":
            language_context = f"\nNote: The original strategy is in MQL (MetaTrader). Provide suggestions that can be implemented in MQL syntax."
        elif original_language.lower() == "python":
            language_context = f"\nNote: The original strategy is in Python. Provide suggestions that can be implemented in Python syntax."
        elif original_language.lower() == "natural":
            language_context = f"\nNote: The original strategy is in natural language. Provide suggestions in clear, actionable language."
    
    prompt = f"""
    Analyze this trading strategy for {symbol} on {timeframe} timeframe and suggest specific improvements to {goal_description}.
    
    Current Strategy: {strategy}
    
    Performance Analysis:
    - Overall Score: {current_performance['overall_score']}/100
    - Risk Level: {current_performance['risk_level']}
    - Strengths: {', '.join(current_performance['strengths'])}
    - Weaknesses: {', '.join(current_performance['weaknesses'])}
    - Recommendations: {', '.join(current_performance['recommendations'])}
    
    User Feedback: {user_feedback or 'None provided'}
    {language_context}
    
    Please provide specific, actionable suggestions in this format:
    1. Entry Signal Improvements: [specific changes to entry conditions]
    2. Exit Signal Improvements: [specific changes to exit conditions]
    3. Risk Management: [specific risk controls to add]
    4. Position Sizing: [specific position sizing rules]
    5. Additional Indicators: [specific technical indicators to consider]
    6. Timeframe Adjustments: [specific timeframe optimizations]
    
    Focus on practical, implementable changes that address the identified weaknesses.
    """
    
    try:
        # Use the translator's LLM to generate suggestions
        response = translator.llm.invoke([HumanMessage(content=prompt)])
        suggestions = response.content.strip()
        
        # Parse suggestions into structured format
        structured_suggestions = {
            "entry_improvements": [],
            "exit_improvements": [],
            "risk_management": [],
            "position_sizing": [],
            "additional_indicators": [],
            "timeframe_adjustments": [],
            "overall_recommendations": suggestions
        }
        
        # Simple parsing of the response
        lines = suggestions.split('\n')
        current_section = "overall_recommendations"
        
        for line in lines:
            line = line.strip()
            if "entry" in line.lower() and "signal" in line.lower():
                current_section = "entry_improvements"
            elif "exit" in line.lower() and "signal" in line.lower():
                current_section = "exit_improvements"
            elif "risk" in line.lower() and "management" in line.lower():
                current_section = "risk_management"
            elif "position" in line.lower() and "sizing" in line.lower():
                current_section = "position_sizing"
            elif "indicator" in line.lower():
                current_section = "additional_indicators"
            elif "timeframe" in line.lower():
                current_section = "timeframe_adjustments"
            elif line and not line.startswith(('1.', '2.', '3.', '4.', '5.', '6.')):
                if current_section != "overall_recommendations":
                    structured_suggestions[current_section].append(line)
        
        return structured_suggestions
        
    except Exception as e:
        logger.error(f"Error generating optimization suggestions: {e}")
        return {
            "entry_improvements": ["Add stop-loss orders", "Implement trailing stops"],
            "exit_improvements": ["Add take-profit levels", "Use multiple exit conditions"],
            "risk_management": ["Limit position size to 2% of capital", "Add maximum drawdown protection"],
            "position_sizing": ["Use Kelly Criterion", "Implement volatility-based sizing"],
            "additional_indicators": ["Add RSI for overbought/oversold", "Include volume analysis"],
            "timeframe_adjustments": ["Consider shorter timeframe for entries", "Use longer timeframe for trend"],
            "overall_recommendations": "Focus on risk management and entry/exit signal quality"
        }

async def generate_improved_strategy(
    original_strategy: str,
    suggestions: dict,
    symbol: str,
    original_language: str = None
) -> str:
    """Generate an improved version of the strategy based on optimization suggestions"""
    
    # Build improvement prompt
    language_instruction = ""
    if original_language:
        if original_language.lower() == "pine":
            language_instruction = f"\nIMPORTANT: Return the improved strategy in Pine Script code format, not natural language. Use proper Pine Script syntax, variables, and structure."
        elif original_language.lower() == "mql":
            language_instruction = f"\nIMPORTANT: Return the improved strategy in MQL (MetaTrader) code format, not natural language. Use proper MQL syntax, functions, and structure."
        elif original_language.lower() == "python":
            language_instruction = f"\nIMPORTANT: Return the improved strategy in Python code format, not natural language. Use proper Python syntax, functions, and structure."
        elif original_language.lower() == "natural":
            language_instruction = f"\nReturn the improved strategy in natural language that can be translated to DSL."
    
    prompt = f"""
    Based on the following optimization suggestions, improve this trading strategy for {symbol}:
    
    Original Strategy: {original_strategy}
    
    Optimization Suggestions:
    - Entry Improvements: {', '.join(suggestions.get('entry_improvements', []))}
    - Exit Improvements: {', '.join(suggestions.get('exit_improvements', []))}
    - Risk Management: {', '.join(suggestions.get('risk_management', []))}
    - Position Sizing: {', '.join(suggestions.get('position_sizing', []))}
    - Additional Indicators: {', '.join(suggestions.get('additional_indicators', []))}
    - Timeframe Adjustments: {', '.join(suggestions.get('timeframe_adjustments', []))}
    
    {language_instruction}
    
    Focus on making it more robust, profitable, and risk-managed.
    """
    
    try:
        # Use the translator's LLM to generate improved strategy
        response = translator.llm.invoke([HumanMessage(content=prompt)])
        improved_strategy = response.content.strip()
        
        # Clean up the response
        if improved_strategy.startswith("Improved Strategy:"):
            improved_strategy = improved_strategy[18:].strip()
        if improved_strategy.startswith("Strategy:"):
            improved_strategy = improved_strategy[9:].strip()
            
        return improved_strategy
        
    except Exception as e:
        logger.error(f"Error generating improved strategy: {e}")
        return f"Enhanced {original_strategy} with improved risk management and signal quality"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize components with OpenRouter API key
OPENROUTER_API_KEY = "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"

translator = StrategyTranslator(api_key=OPENROUTER_API_KEY)
data_fetcher = DataFetcher()

class BacktestRequest(BaseModel):
    strategy: str
    symbol: str
    timeframe: str = "1d"
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    initial_capital: Optional[float] = 100000.0

class OptimizationRequest(BaseModel):
    strategy: str
    symbol: str
    timeframe: str
    start_date: str
    end_date: str
    initial_capital: float
    current_metrics: dict
    optimization_goal: str = "improve_returns"  # improve_returns, reduce_drawdown, increase_sharpe
    user_feedback: Optional[str] = None
    original_language: Optional[str] = None  # pine, mql, python, natural, etc.

app = FastAPI(title="AI Trading Agent", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "AI Trading Agent API", "status": "running"}

@app.get("/symbols")
async def get_symbols():
    """Get list of available symbols for testing"""
    return {"symbols": data_fetcher.get_available_symbols()}

@app.post("/backtest")
async def backtest_strategy(request: BacktestRequest):
    """
    Run a backtest with the given strategy
    """
    try:
        logger.info(f"Starting backtest for {request.symbol}")
        
        # Set default dates if not provided
        if request.end_date is None:
            end_date = datetime.now() - timedelta(days=1)  # Use yesterday as default
        else:
            # Handle both YYYY-MM-DD and YYYY-MM-DDTHH:MM:SSZ formats
            try:
                end_date = datetime.strptime(request.end_date, '%Y-%m-%d')
            except ValueError:
                try:
                    end_date = datetime.strptime(request.end_date, '%Y-%m-%dT%H:%M:%SZ')
                except ValueError:
                    end_date = datetime.strptime(request.end_date, '%Y-%m-%dT%H:%M:%S')
            
        if request.start_date is None:
            start_date = end_date - timedelta(days=365)  # Default to 1 year
        else:
            # Handle both YYYY-MM-DD and YYYY-MM-DDTHH:MM:SSZ formats
            try:
                start_date = datetime.strptime(request.start_date, '%Y-%m-%d')
            except ValueError:
                try:
                    start_date = datetime.strptime(request.start_date, '%Y-%m-%dT%H:%M:%SZ')
                except ValueError:
                    start_date = datetime.strptime(request.start_date, '%Y-%m-%dT%H:%M:%S')
        
        # Validate dates
        if start_date >= end_date:
            raise HTTPException(status_code=400, detail="Start date must be before end date")
        
        if end_date > datetime.now():
            raise HTTPException(status_code=400, detail="End date cannot be in the future")
        
        # Fetch market data
        logger.info(f"Fetching data for {request.symbol}")
        data = data_fetcher.fetch_data(
            symbol=request.symbol,
            start_date=start_date,
            end_date=end_date,
            timeframe=request.timeframe
        )
        
        if data is None or data.empty:
            raise HTTPException(status_code=400, detail=f"No data available for {request.symbol}")
        
        logger.info(f"Data fetched: {len(data)} data points")
        
        # Translate strategy to DSL
        logger.info("Translating strategy to DSL")
        dsl = translator.translate_to_dsl(request.strategy)
        
        # Compile DSL to backtesting.py code
        logger.info("Compiling DSL to backtesting.py code")
        code = compile_btp(dsl)
        
        # Run backtest with backtrader (more robust than backtesting.py)
        logger.info(f"Running backtest with backtrader, initial capital: {request.initial_capital}")
        try:
            # Create a temporary CSV file for the data
            temp_csv = f"temp_{request.symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            data.to_csv(temp_csv)
            
            # Run the backtest using backtrader
            result = run_backtrader(temp_csv, code, request.timeframe, request.initial_capital)
            
            # Clean up temp file
            import os
            if os.path.exists(temp_csv):
                os.remove(temp_csv)
                
            if result["ok"]:
                return {
                    "success": True,
                    "metrics": result.get("metrics", {}),
                    "trades": result.get("trades", []),
                    "data_points": len(data),
                    "symbol": request.symbol,
                    "timeframe": request.timeframe,
                    "start_date": start_date.strftime('%Y-%m-%d'),
                    "end_date": end_date.strftime('%Y-%m-%d')
                }
            else:
                raise HTTPException(status_code=500, detail=f"Backtest failed: {result['error']}")
                
        except Exception as e:
            logger.error(f"Backtest execution error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Backtest execution failed: {str(e)}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in backtest: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/optimize")
async def optimize_strategy(request: OptimizationRequest):
    """
    Analyze current strategy performance and suggest optimizations
    """
    try:
        logger.info(f"Starting strategy optimization for {request.symbol}")
        
        # Analyze current performance
        current_performance = analyze_performance(request.current_metrics)
        
        # Generate optimization suggestions
        optimization_suggestions = await generate_optimization_suggestions(
            strategy=request.strategy,
            symbol=request.symbol,
            timeframe=request.timeframe,
            current_performance=current_performance,
            optimization_goal=request.optimization_goal,
            user_feedback=request.user_feedback,
            original_language=request.original_language
        )
        
        # Generate improved strategy code
        improved_strategy = await generate_improved_strategy(
            original_strategy=request.strategy,
            suggestions=optimization_suggestions,
            symbol=request.symbol,
            original_language=request.original_language
        )
        
        return {
            "success": True,
            "analysis": current_performance,
            "suggestions": optimization_suggestions,
            "improved_strategy": improved_strategy,
            "optimization_goal": request.optimization_goal
        }
        
    except Exception as e:
        logger.error(f"Strategy optimization error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Optimization failed: {str(e)}")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await websocket.accept()
    
    try:
        # Send initial connection message
        await websocket.send_text(json.dumps({
            "type": "connection",
            "message": "Connected to AI Trading Agent",
            "timestamp": datetime.now().isoformat()
        }))
        
        # Keep connection alive and send periodic updates
        while True:
            await asyncio.sleep(5)
            await websocket.send_text(json.dumps({
                "type": "heartbeat",
                "timestamp": datetime.now().isoformat(),
                "status": "active"
            }))
            
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
    finally:
        await websocket.close()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001) 