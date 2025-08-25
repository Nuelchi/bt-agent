#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_fetcher import DataFetcher
from datetime import datetime, timedelta

def test_data_fetch():
    fetcher = DataFetcher()
    
    # Test with the same dates that the API would use
    end_date = datetime.now() - timedelta(days=1)
    start_date = end_date - timedelta(days=365)
    
    print(f"Testing data fetch for AAPL")
    print(f"Start date: {start_date}")
    print(f"End date: {end_date}")
    
    try:
        data = fetcher.fetch_data(
            symbol="AAPL",
            start_date=start_date,
            end_date=end_date,
            timeframe="1d"
        )
        
        if data is not None and not data.empty:
            print(f"Success! Got {len(data)} data points")
            print(f"Data shape: {data.shape}")
            print(f"Data columns: {list(data.columns)}")
            print(f"Data index type: {type(data.index)}")
            print(f"First few rows:")
            print(data.head())
        else:
            print("No data returned")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_data_fetch() 