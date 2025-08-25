# Trading Agent Backtester

A sophisticated AI-powered trading strategy backtesting system that translates natural language, Pine Script, or MQL strategies into executable code and runs comprehensive backtests using backtesting.py.

## 🚀 Features

- **AI-Powered Strategy Translation**: Uses GPT-4 to convert natural language descriptions into executable trading strategies
- **Multi-Language Support**: Accepts Pine Script, MQL4/5, and natural language inputs
- **Automatic Code Generation**: Compiles strategies into backtesting.py compatible code
- **Real-Time Metrics**: Comprehensive performance analytics including Sharpe ratio, drawdown, win rate, and more
- **Auto-Repair System**: LLM automatically fixes code errors and retries failed backtests
- **Data Integration**: Fetches historical data from Yahoo Finance with intelligent caching
- **Modern Web Interface**: Beautiful, responsive frontend for strategy input and results visualization

## 🏗️ Architecture

The system follows the architecture shown in your images:

1. **Input Normalizer**: Detects and processes different input formats
2. **LLM Translator**: Converts strategies to validated DSL (Domain Specific Language)
3. **Compiler**: Generates executable Python code for backtesting.py
4. **Sandboxed Executor**: Runs backtests safely with resource limits
5. **Auto-Fix Loop**: Uses LLM to repair failed strategies automatically
6. **Analyzers & Metrics**: Comprehensive performance analysis
7. **Streaming Frontend**: Real-time results display

## 📋 Requirements

- Python 3.8+
- OpenAI API key
- Internet connection for data fetching

## 🛠️ Installation

1. **Clone the repository**:
   ```bash
   git clone <your-repo-url>
   cd bt-agent
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   ```bash
   cp env_example.txt .env
   # Edit .env and add your OpenAI API key
   export OPENAI_API_KEY=your_actual_api_key_here
   ```

## 🚀 Usage

### Starting the Server

```bash
python main.py
```

The server will start on `http://localhost:8000`

### Using the Web Interface

1. **Open your browser** and navigate to `http://localhost:8000`
2. **Select your trading instrument** (Forex, Stocks, or Crypto)
3. **Choose timeframe** (15M, 1H, 4H, 1D)
4. **Set date range** for backtesting
5. **Describe your strategy** in natural language
6. **Click "Run Backtest"** to execute

### Strategy Examples

#### Natural Language
```
Create a strategy that buys when the 20-period EMA crosses above the 50-period EMA, 
with a 2% risk per trade and ATR-based stop loss. Exit when the fast EMA crosses below the slow EMA.
```

#### Pine Script Style
```
//@version=5
strategy("EMA Cross", overlay=true)
fast_ema = ta.ema(close, 20)
slow_ema = ta.ema(close, 50)
long_condition = ta.crossover(fast_ema, slow_ema)
short_condition = ta.crossunder(fast_ema, slow_ema)
```

#### MQL Style
```
OnTick() {
    double ema_fast = iMA(Symbol(), PERIOD_CURRENT, 20, 0, MODE_EMA, PRICE_CLOSE);
    double ema_slow = iMA(Symbol(), PERIOD_CURRENT, 50, 0, MODE_EMA, PRICE_CLOSE);
    // Strategy logic here
}
```

## 📊 Metrics & Analysis

The system provides comprehensive performance metrics:

- **Portfolio Value**: Starting and ending portfolio values
- **Total Return**: Strategy performance percentage
- **Max Drawdown**: Maximum loss from peak to trough
- **Sharpe Ratio**: Risk-adjusted return measure
- **Win Rate**: Percentage of profitable trades
- **Trade Analysis**: Detailed breakdown of all trades
- **Strategy vs Buy & Hold**: Performance comparison

## 🔧 Configuration

### Environment Variables

- `OPENAI_API_KEY`: Your OpenAI API key (required)
- `HOST`: Server host (default: 0.0.0.0)
- `PORT`: Server port (default: 8000)

### Customizing Indicators

Edit `compiler_btp.py` to add new technical indicators or modify existing ones.

### Data Sources

Currently supports Yahoo Finance. Extend `data_fetcher.py` to add more data providers.

## 🏗️ Project Structure

```
bt-agent/
├── main.py                 # FastAPI application
├── dsl.py                  # Pydantic schema definitions
├── translator.py           # LLM strategy translator
├── compiler_btp.py         # DSL to backtesting.py compiler
├── backtest_runner.py      # Sandboxed backtest executor
├── autofix.py             # Auto-repair system
├── data_fetcher.py        # Data fetching and caching
├── requirements.txt        # Python dependencies
├── frontend/
│   └── index.html         # Web interface
└── data_cache/            # Cached market data
```

## 🔒 Security Features

- **Sandboxed Execution**: Backtests run in isolated processes
- **Resource Limits**: CPU and memory usage restrictions
- **Code Validation**: All generated code validated before execution
- **No Network Access**: Backtest processes cannot access external resources

## 🚧 Limitations & Future Work

### Current Limitations
- Single symbol backtesting (portfolio backtesting planned)
- Limited to backtesting.py framework (Backtrader support planned)
- Basic risk management (advanced position sizing planned)

### Planned Features
- Multi-asset portfolio backtesting
- Backtrader framework support
- Advanced risk management and position sizing
- Strategy optimization and parameter tuning
- Real-time paper trading
- More data sources (MT5, Interactive Brokers, etc.)

## 🐛 Troubleshooting

### Common Issues

1. **OpenAI API Key Error**: Ensure your API key is set correctly
2. **Data Fetching Issues**: Check internet connection and symbol format
3. **Memory Errors**: Reduce backtest date range or timeframe
4. **Strategy Translation Failures**: Try rephrasing your strategy description

### Debug Mode

Enable detailed logging by setting environment variable:
```bash
export LOG_LEVEL=DEBUG
```

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📞 Support

For issues and questions:
1. Check the troubleshooting section
2. Review the logs in the web interface
3. Open an issue on GitHub

---

**Built with ❤️ using FastAPI, LangChain, and backtesting.py** 