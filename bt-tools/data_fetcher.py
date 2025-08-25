import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataFetcher:
    def __init__(self, cache_dir="data_cache"):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
    
    def fetch_data(self, symbol, start_date=None, end_date=None, timeframe="1d"):
        """
        Fetch historical market data with proper date handling and symbol validation
        """
        try:
            # Normalize symbol for yfinance
            normalized_symbol = self._normalize_symbol_for_yfinance(symbol)
            
            # Set default dates if not provided
            if end_date is None:
                end_date = datetime.now()
            if start_date is None:
                start_date = end_date - timedelta(days=365)  # Default to 1 year
            
            # Ensure dates are in the past
            if start_date > datetime.now():
                start_date = datetime.now() - timedelta(days=365)
            if end_date > datetime.now():
                end_date = datetime.now()
            
            # Convert to string format yfinance expects
            start_str = start_date.strftime('%Y-%m-%d')
            end_str = end_date.strftime('%Y-%m-%d')
            
            logger.info(f"Fetching data for {normalized_symbol} from {start_str} to {end_str}")
            
            # Try to get data from cache first
            cache_file = os.path.join(self.cache_dir, f"{normalized_symbol}_{start_str}_{end_str}.csv")
            if os.path.exists(cache_file):
                logger.info(f"Loading data from cache: {cache_file}")
                data = pd.read_csv(cache_file, index_col=0, parse_dates=True)
                if not data.empty:
                    return self._format_data_for_backtesting(data)
            
            # Fetch from yfinance
            data = self._fetch_yfinance(normalized_symbol, start_str, end_str, timeframe)
            
            if data is not None and not data.empty:
                # Cache the data
                data.to_csv(cache_file)
                logger.info(f"Data cached to {cache_file}")
                return self._format_data_for_backtesting(data)
            else:
                raise ValueError(f"No data returned for {normalized_symbol}")
                
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {str(e)}")
            raise
    
    def _normalize_symbol_for_yfinance(self, symbol: str) -> str:
        """Map common FX/crypto formats to Yahoo tickers - based on pyth-m5 approach"""
        if not symbol:
            return symbol
        s = symbol.strip()
        if not s:
            return s
        
        # Preserve Yahoo-native forms
        if s.startswith('^') or s.endswith('=X'):
            return s
        
        upper = s.upper().replace(' ', '')
        
        # If already hyphenated crypto like BTC-USD, keep
        if '-' in upper and len(upper.split('-')) == 2:
            return upper
        
        # Remove separators to analyze base/quote
        merged = upper.replace('/', '').replace('_', '').replace('-', '')
        
        # Known crypto bases to disambiguate from FX
        crypto_bases = {
            "BTC","ETH","SOL","XRP","ADA","DOGE","LTC","BCH","BNB","AVAX","DOT",
            "SHIB","MATIC","LINK","TRX","XLM","XMR","ETC","UNI","ATOM","FIL","NEAR"
        }
        
        if len(merged) == 6 and merged.isalpha():
            base, quote = merged[:3], merged[3:]
            if base in crypto_bases or quote in {"USDT", "BTC", "ETH"}:
                # Crypto pair -> BASE-QUOTE
                return f"{base}-{quote}"
            # Default treat as FX -> BASEQUOTE=X
            return f"{base}{quote}=X"
        
        # If looks like crypto with 3-4 letter quote
        for sep in ('/', '_'):
            if sep in upper:
                parts = [p for p in upper.split(sep) if p]
                if len(parts) == 2 and 2 <= len(parts[1]) <= 5:
                    return f"{parts[0]}-{parts[1]}"
        
        # Fallback: return normalized upper-case ticker (stocks, indices without caret already)
        return upper
    
    def _fetch_yfinance(self, symbol, start_date, end_date, timeframe):
        """
        Fetch data from yfinance with proper error handling
        """
        try:
            # Map our timeframes to yfinance format
            yf_timeframe = self._map_timeframe(timeframe)
            
            ticker = yf.Ticker(symbol)
            
            # Get historical data
            data = ticker.history(start=start_date, end=end_date, interval=yf_timeframe)
            
            if data.empty:
                logger.warning(f"No data found for {symbol} from {start_date} to {end_date}")
                return None
            
            # yfinance returns uppercase column names, so check for those
            required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            missing_columns = [col for col in required_columns if col not in data.columns]
            
            if missing_columns:
                logger.warning(f"Missing columns for {symbol}: {missing_columns}")
                return None
            
            # Handle timezone-aware datetime index
            if data.index.tz is not None:
                # Convert to UTC first, then make naive
                data.index = data.index.tz_convert('UTC').tz_localize(None)
            else:
                # If no timezone, assume UTC and make naive
                data.index = pd.to_datetime(data.index, utc=True).tz_localize(None)
            
            # Clean the data
            data = data.dropna()
            
            if len(data) < 10:  # Need at least 10 data points for backtesting
                logger.warning(f"Insufficient data for {symbol}: only {len(data)} points")
                return None
            
            logger.info(f"Successfully fetched {len(data)} data points for {symbol}")
            return data
            
        except Exception as e:
            logger.error(f"yfinance error for {symbol}: {str(e)}")
            return None
    
    def _map_timeframe(self, timeframe):
        """Map our timeframes to yfinance format"""
        mapping = {
            "1m": "1m", "5m": "5m", "15m": "15m", "30m": "30m",
            "1h": "1h", "4h": "4h", "1d": "1d"
        }
        return mapping.get(timeframe, "1d")
    
    def _format_data_for_backtesting(self, df):
        """Format data for backtrader - backtrader expects lowercase columns"""
        try:
            # Ensure proper datetime index
            if not isinstance(df.index, pd.DatetimeIndex):
                df.index = pd.to_datetime(df.index)
            
            # Convert to naive UTC if timezone-aware
            if df.index.tz is not None:
                df = df.tz_convert("UTC").tz_localize(None)
            else:
                # If no timezone info, assume UTC and convert to naive
                df.index = pd.to_datetime(df.index, utc=True).tz_localize(None)
            
            # Rename columns to lowercase (backtrader expects this)
            df = df.rename(columns={
                "Open": "open",
                "High": "high", 
                "Low": "low",
                "Close": "close",
                "Volume": "volume"
            })
            
            # Ensure we have the required columns
            required_cols = ["open", "high", "low", "close", "volume"]
            df = df[[col for col in required_cols if col in df.columns]].copy()
            
            # Add volume if missing
            if "volume" not in df.columns:
                df["volume"] = 1000000  # Default volume
            
            # Clean data
            df.dropna(inplace=True)
            
            if len(df) < 10:
                raise ValueError(f"Insufficient data: only {len(df)} points")
            
            return df
            
        except Exception as e:
            logger.error(f"Error formatting data: {str(e)}")
            raise
    
    def get_available_symbols(self):
        """
        Return a list of commonly available symbols for testing
        """
        return [
            'AAPL', 'MSFT', 'GOOGL', 'TSLA', 'AMZN',  # US Stocks
            'EURUSD=X', 'GBPUSD=X', 'USDJPY=X',        # Forex
            'BTC-USD', 'ETH-USD'                        # Crypto
        ]
    
    def validate_symbol(self, symbol):
        """
        Check if a symbol is likely to have data available
        """
        try:
            normalized = self._normalize_symbol_for_yfinance(symbol)
            ticker = yf.Ticker(normalized)
            info = ticker.info
            return 'regularMarketPrice' in info and info['regularMarketPrice'] is not None
        except:
            return False 