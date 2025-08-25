import React, { useState, useEffect } from "react";
import axios from "axios";
import "./App.css";

function App() {
  const [market, setMarket] = useState("stocks");
  const [symbol, setSymbol] = useState("AAPL");
  const [timeframe, setTimeframe] = useState("1d");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [initialCapital, setInitialCapital] = useState(100000);
  const [strategyText, setStrategyText] = useState("Buy and hold strategy for AAPL");
  const [isLoading, setIsLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  const [availableSymbols, setAvailableSymbols] = useState([]);
  const [showOptimization, setShowOptimization] = useState(false);
  const [optimizationGoal, setOptimizationGoal] = useState("improve_returns");
  const [userFeedback, setUserFeedback] = useState("");
  const [optimizationResults, setOptimizationResults] = useState(null);
  const [isOptimizing, setIsOptimizing] = useState(false);

  // Function to detect strategy language
  const detectStrategyLanguage = (strategy) => {
    const lowerStrategy = strategy.toLowerCase();
    
    // Pine Script detection
    if (lowerStrategy.includes('pine') || 
        lowerStrategy.includes('strategy') || 
        lowerStrategy.includes('@version') ||
        lowerStrategy.includes('//@strategy') ||
        lowerStrategy.includes('strategy(') ||
        lowerStrategy.includes('plot(') ||
        lowerStrategy.includes('ta.')) {
      return 'pine';
    }
    
    // MQL detection
    if (lowerStrategy.includes('mql') || 
        lowerStrategy.includes('expert') || 
        lowerStrategy.includes('oninit') ||
        lowerStrategy.includes('ontick') ||
        lowerStrategy.includes('order') ||
        lowerStrategy.includes('position') ||
        lowerStrategy.includes('symbol') ||
        lowerStrategy.includes('_point')) {
      return 'mql';
    }
    
    // Python detection
    if (lowerStrategy.includes('def ') || 
        lowerStrategy.includes('import ') || 
        lowerStrategy.includes('class ') ||
        lowerStrategy.includes('self.') ||
        lowerStrategy.includes('if __name__') ||
        lowerStrategy.includes('pandas') ||
        lowerStrategy.includes('numpy')) {
      return 'python';
    }
    
    // Default to natural language
    return 'natural';
  };

  useEffect(() => {
    // Set default dates
    const end = new Date();
    const start = new Date();
    start.setFullYear(start.getFullYear() - 1);
    
    setEndDate(end.toISOString().split('T')[0]);
    setStartDate(start.toISOString().split('T')[0]);
    
    // Fetch available symbols
    fetchSymbols();
  }, []);

  // Update strategy text when symbol changes
  useEffect(() => {
    if (symbol && strategyText) {
      const updatedStrategy = strategyText.replace(/for\s+\w+/, `for ${symbol}`);
      setStrategyText(updatedStrategy);
    }
  }, [symbol]);

  const fetchSymbols = async () => {
    try {
      const response = await axios.get('/symbols');
      setAvailableSymbols(response.data.symbols);
    } catch (err) {
      console.error('Failed to fetch symbols:', err);
    }
  };

  const getSymbolsForMarket = () => {
    switch (market) {
      case 'stocks':
        return availableSymbols.filter(s => !s.includes('=') && !s.includes('-'));
      case 'forex':
        return availableSymbols.filter(s => s.includes('=X'));
      case 'crypto':
        return availableSymbols.filter(s => s.includes('-USD'));
      default:
        return availableSymbols;
    }
  };

  const runBacktest = async () => {
    setIsLoading(true);
    setError(null);
    setResults(null);

    try {
      // Send dates in simple YYYY-MM-DD format (backend will handle parsing)
      const startDateTime = startDate;
      const endDateTime = endDate;
      
      // Update strategy text to include current symbol
      const updatedStrategy = strategyText.replace(/for\s+\w+/, `for ${symbol}`);
      
      const response = await axios.post('/backtest', {
        strategy: updatedStrategy,
        symbol: symbol,
        timeframe: timeframe,
        start_date: startDateTime,
        end_date: endDateTime,
        initial_capital: initialCapital
      });

      setResults(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Backtest failed');
    } finally {
      setIsLoading(false);
    }
  };

  const optimizeStrategy = async () => {
    if (!results) return;
    
    setIsOptimizing(true);
    setError(null);
    setOptimizationResults(null);

    try {
      // Detect the language of the original strategy
      const detectedLanguage = detectStrategyLanguage(strategyText);
      
      const response = await axios.post('/optimize', {
        strategy: strategyText,
        symbol: symbol,
        timeframe: timeframe,
        start_date: startDate,
        end_date: endDate,
        initial_capital: initialCapital,
        current_metrics: results.metrics,
        optimization_goal: optimizationGoal,
        user_feedback: userFeedback,
        original_language: detectedLanguage
      });

      setOptimizationResults(response.data);
      setShowOptimization(false);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Optimization failed');
    } finally {
      setIsOptimizing(false);
    }
  };

  const formatMetric = (value, type = 'number') => {
    if (value === null || value === undefined) return 'N/A';
    
    switch (type) {
      case 'percentage':
        return `${(value * 100).toFixed(2)}%`;
      case 'currency':
        return `$${value.toFixed(2)}`;
      default:
        return typeof value === 'number' ? value.toFixed(4) : value;
    }
  };

  return (
    <div className="App">
      <header className="header">
        <h1>🚀 AI Trading Agent Backtester</h1>
        <p>Powered by LangChain & OpenRouter Claude</p>
      </header>

      <div className="main-container">
        <div className="controls-panel">
          <div className="control-group">
            <label>Market Type:</label>
            <select value={market} onChange={(e) => setMarket(e.target.value)}>
              <option value="stocks">Stocks</option>
              <option value="forex">Forex</option>
              <option value="crypto">Crypto</option>
            </select>
          </div>

          <div className="control-group">
            <label>Symbol:</label>
            <select value={symbol} onChange={(e) => setSymbol(e.target.value)}>
              {getSymbolsForMarket().map(s => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </div>

          <div className="control-group">
            <label>Timeframe:</label>
            <select value={timeframe} onChange={(e) => setTimeframe(e.target.value)}>
              <option value="1m">1 Minute</option>
              <option value="5m">5 Minutes</option>
              <option value="15m">15 Minutes</option>
              <option value="1h">1 Hour</option>
              <option value="4h">4 Hours</option>
              <option value="1d">1 Day</option>
            </select>
          </div>

          <div className="control-group">
            <label>Start Date:</label>
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
            />
          </div>

          <div className="control-group">
            <label>End Date:</label>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
            />
          </div>

          <div className="control-group">
            <label>Initial Capital ($):</label>
            <input
              type="number"
              value={initialCapital}
              onChange={(e) => setInitialCapital(Number(e.target.value))}
              min="1000"
              step="1000"
              placeholder="100000"
            />
          </div>
        </div>

        <div className="strategy-section">
          <h3>📊 Trading Strategy</h3>
          <textarea
            value={strategyText}
            onChange={(e) => setStrategyText(e.target.value)}
            placeholder="Describe your trading strategy in natural language..."
            rows={4}
          />
          <button 
            className="run-button"
            onClick={runBacktest}
            disabled={isLoading}
          >
            {isLoading ? 'Running Backtest...' : '🚀 Run Backtest'}
          </button>
        </div>

        {error && (
          <div className="error-message">
            <h3>❌ Error</h3>
            <p>{error}</p>
          </div>
        )}

        {results && (
          <div className="results-panel">
            <h3>📈 Backtest Results</h3>
            
            <div className="metrics-grid">
              <div className="metric-card">
                <h4>Returns</h4>
                <div className="metric-value">
                  {formatMetric(results.metrics?.returns?.rtot100, 'percentage')}
                </div>
              </div>
              
              <div className="metric-card">
                <h4>Sharpe Ratio</h4>
                <div className="metric-value">
                  {formatMetric(results.metrics?.sharpe)}
                </div>
              </div>
              
              <div className="metric-card">
                <h4>Max Drawdown</h4>
                <div className="metric-value">
                  {formatMetric(results.metrics?.drawdown?.max?.drawdown, 'percentage')}
                </div>
              </div>
              
              <div className="metric-card">
                <h4>Total Trades</h4>
                <div className="metric-value">
                  {results.metrics?.trades?.total?.total || 'N/A'}
                </div>
              </div>
              
              <div className="metric-card">
                <h4>SQN</h4>
                <div className="metric-value">
                  {formatMetric(results.metrics?.sqn?.sqn)}
                </div>
              </div>
              
              <div className="metric-card">
                <h4>Data Points</h4>
                <div className="metric-value">
                  {results.data_points}
                </div>
              </div>
            </div>

            <div className="trade-details">
              <h4>Trade Summary</h4>
              <p>Symbol: {results.symbol}</p>
              <p>Timeframe: {results.timeframe}</p>
              <p>Period: {results.start_date} to {results.end_date}</p>
            </div>

            <div className="portfolio-balance">
              <h4>💰 Portfolio Balance</h4>
              <div className="balance-grid">
                <div className="balance-card">
                  <h5>Starting Balance</h5>
                  <div className="balance-value start">
                    ${results.metrics?.summary?.pv_start?.toLocaleString() || initialCapital.toLocaleString()}
                  </div>
                </div>
                <div className="balance-card">
                  <h5>Final Balance</h5>
                  <div className="balance-value end">
                    ${results.metrics?.summary?.pv_end?.toLocaleString() || 'N/A'}
                  </div>
                </div>
                <div className="balance-card">
                  <h5>Total Return</h5>
                  <div className={`balance-value ${(results.metrics?.summary?.pv_end || 0) >= (results.metrics?.summary?.pv_start || initialCapital) ? 'positive' : 'negative'}`}>
                    ${((results.metrics?.summary?.pv_end || 0) - (results.metrics?.summary?.pv_start || initialCapital)).toLocaleString()}
                  </div>
                </div>
                <div className="balance-card">
                  <h5>Return %</h5>
                  <div className={`balance-value ${(results.metrics?.summary?.pv_end || 0) >= (results.metrics?.summary?.pv_start || initialCapital) ? 'positive' : 'negative'}`}>
                    {(((results.metrics?.summary?.pv_end || 0) - (results.metrics?.summary?.pv_start || initialCapital)) / (results.metrics?.summary?.pv_start || initialCapital) * 100).toFixed(2)}%
                  </div>
                </div>
              </div>
            </div>

            {results.trades && results.trades.length > 0 && (
              <div className="trades-section">
                <h4>📊 Trade History</h4>
                <div className="trades-table">
                  <table>
                    <thead>
                      <tr>
                        <th>Time</th>
                        <th>Type</th>
                        <th>Size</th>
                        <th>Price</th>
                        <th>PnL</th>
                      </tr>
                    </thead>
                    <tbody>
                      {results.trades.map((trade, index) => (
                        <tr key={index} className={trade.type === 'buy' ? 'buy-trade' : 'sell-trade'}>
                          <td>{new Date(trade.time).toLocaleDateString()}</td>
                          <td className={`trade-type ${trade.type}`}>
                            {trade.type === 'buy' ? '🟢 BUY' : '🔴 SELL'}
                          </td>
                          <td>{Math.abs(trade.size)}</td>
                          <td>${trade.price.toFixed(2)}</td>
                          <td className={trade.pnl >= 0 ? 'positive' : 'negative'}>
                            {trade.pnl !== 0 ? `$${trade.pnl.toFixed(2)}` : '-'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Optimization Section */}
        {results && (
          <div className="optimization-section">
            <h3>🔧 Strategy Optimization</h3>
            <p>Not happy with your results? Let AI optimize your strategy!</p>
            
            {!showOptimization ? (
              <button 
                className="optimize-button"
                onClick={() => setShowOptimization(true)}
              >
                🚀 Optimize Strategy
              </button>
            ) : (
              <div className="optimization-form">
                <div className="form-group">
                  <label>Optimization Goal:</label>
                  <select 
                    value={optimizationGoal} 
                    onChange={(e) => setOptimizationGoal(e.target.value)}
                  >
                    <option value="improve_returns">Improve Returns</option>
                    <option value="reduce_drawdown">Reduce Drawdown</option>
                    <option value="increase_sharpe">Increase Sharpe Ratio</option>
                  </select>
                </div>
                
                <div className="form-group">
                  <label>Additional Feedback (Optional):</label>
                  <textarea
                    value={userFeedback}
                    onChange={(e) => setUserFeedback(e.target.value)}
                    placeholder="Describe what you'd like to improve... (e.g., 'Too many false signals', 'Need better risk management')"
                    rows={3}
                  />
                </div>
                
                <div className="form-actions">
                  <button 
                    className="optimize-button"
                    onClick={optimizeStrategy}
                    disabled={isOptimizing}
                  >
                    {isOptimizing ? '🤖 AI Optimizing...' : '🚀 Generate Optimized Strategy'}
                  </button>
                  <button 
                    className="cancel-button"
                    onClick={() => setShowOptimization(false)}
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Optimization Results */}
        {optimizationResults && (
          <div className="optimization-results">
            <h3>🎯 Optimization Results</h3>
            
            <div className="performance-analysis">
              <h4>📊 Performance Analysis</h4>
              <div className="analysis-grid">
                <div className="analysis-card">
                  <h5>Overall Score</h5>
                  <div className="score-value">
                    {optimizationResults.analysis.overall_score}/100
                  </div>
                </div>
                <div className="analysis-card">
                  <h5>Risk Level</h5>
                  <div className={`risk-level ${optimizationResults.analysis.risk_level}`}>
                    {optimizationResults.analysis.risk_level.toUpperCase()}
                  </div>
                </div>
              </div>
              
              <div className="analysis-details">
                <div className="strengths">
                  <h5>✅ Strengths</h5>
                  <ul>
                    {optimizationResults.analysis.strengths.map((strength, index) => (
                      <li key={index}>{strength}</li>
                    ))}
                  </ul>
                </div>
                
                <div className="weaknesses">
                  <h5>❌ Weaknesses</h5>
                  <ul>
                    {optimizationResults.analysis.weaknesses.map((weakness, index) => (
                      <li key={index}>{weakness}</li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>

            <div className="optimization-suggestions">
              <h4>💡 AI Suggestions</h4>
              <div className="suggestions-grid">
                {Object.entries(optimizationResults.suggestions).map(([category, suggestions]) => {
                  if (category === 'overall_recommendations' || !Array.isArray(suggestions)) return null;
                  if (suggestions.length === 0) return null;
                  
                  return (
                    <div key={category} className="suggestion-category">
                      <h5>{category.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</h5>
                      <ul>
                        {suggestions.map((suggestion, index) => (
                          <li key={index}>{suggestion}</li>
                        ))}
                      </ul>
                    </div>
                  );
                })}
              </div>
            </div>

            <div className="improved-strategy">
              <h4>🚀 Improved Strategy</h4>
              <div className="language-indicator">
                <span className={`language-badge ${optimizationResults.original_language || 'natural'}`}>
                  {optimizationResults.original_language || 'natural'} format
                </span>
              </div>
              <div className="strategy-text">
                {optimizationResults.improved_strategy}
              </div>
              <button 
                className="use-strategy-button"
                onClick={() => {
                  setStrategyText(optimizationResults.improved_strategy);
                  setOptimizationResults(null);
                }}
              >
                ✨ Use This Strategy
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
