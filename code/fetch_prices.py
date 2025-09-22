import yfinance as yf
import pandas as pd
import os
from pathlib import Path

# Set up paths relative to script location
script_dir = Path(__file__).parent
project_root = script_dir.parent
output_dir = project_root / "output"

# Create output directory if not exists
os.makedirs(output_dir, exist_ok=True)

# ARK ETF list - all 6 ETFs with transformed data
ark_etfs = ['ARKK', 'ARKQ', 'ARKW', 'ARKG', 'ARKF', 'ARKX']

# Fetch and save price data
for etf in ark_etfs:
    print(f"Fetching {etf}...")
    ticker = yf.Ticker(etf)
    df = ticker.history(period="max", interval="1d")
    
    if not df.empty:
        # Convert index to string format without timezone
        df.index = df.index.strftime('%Y-%m-%d')
        
        # Ensure all price columns are numeric with proper formatting
        price_cols = ['Open', 'High', 'Low', 'Close']
        for col in price_cols:
            df[col] = df[col].round(2)  # Round to 2 decimal places
        
        # Save with clean numeric format
        df.to_csv(f"{output_dir}/{etf}_prices.csv", float_format='%.2f')
        print(f"Saved {etf}_prices.csv")
        print(f"  Data from {df.index[0]} to {df.index[-1]}")
    else:
        print(f"No data for {etf}")