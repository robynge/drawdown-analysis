import yfinance as yf
import os
from pathlib import Path

# Set up paths relative to script location
script_dir = Path(__file__).parent
project_root = script_dir.parent
output_dir = project_root / "output"

# Create output directory if not exists
os.makedirs(output_dir, exist_ok=True)

# Russell 3000 index and ARK ETF symbols
indices = ['^RUA']  # Russell 3000 Index
ark_etfs = ['ARKK', 'ARKQ', 'ARKW', 'ARKG', 'ARKF', 'ARKX']  # ARK ETFs

# Date range for analysis
start_date = '2024-04-01'
end_date = '2025-11-10'

# Fetch and save price data for indices
for index in indices:
    ticker = yf.Ticker(index)
    df = ticker.history(start=start_date, end=end_date, interval="1d")
    if not df.empty:
        df.index = df.index.strftime('%Y-%m-%d')
        df = df[['Close']]
        df['Close'] = df['Close'].round(2)
        df.to_csv(f"{output_dir}/{index}_prices.csv", float_format='%.2f')

# Fetch and save price data for ARK ETFs
for etf in ark_etfs:
    ticker = yf.Ticker(etf)
    df = ticker.history(start=start_date, end=end_date, interval="1d")
    if not df.empty:
        df.index = df.index.strftime('%Y-%m-%d')
        df = df[['Close']]
        df['Close'] = df['Close'].round(2)
        df.to_csv(f"{output_dir}/{etf}_prices.csv", float_format='%.2f')