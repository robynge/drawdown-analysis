import pandas as pd
import numpy as np
from pathlib import Path

def load_holdings_data(etf_name):
    base_dir = Path(__file__).parent.parent
    file_path = base_dir / 'input' / f'{etf_name}_Transformed_Data.xlsx'

    df = pd.read_excel(file_path)
    df = df[['Date', 'Ticker', 'Position', 'Market Value']]

    # Filter out USD (cash position)
    df = df[df['Ticker'] != 'USD']

    df['Date'] = pd.to_datetime(df['Date'])
    df['calculated_stock_price'] = df['Market Value'] / df['Position']

    return df

def calculate_daily_metrics(df):
    df = df.sort_values(['Date', 'Ticker'])

    # Get unique dates in order
    dates = sorted(df['Date'].unique())

    # ETF level calculations
    etf_df = df.groupby('Date')['Market Value'].sum().to_frame('ETF MV')
    etf_df['ETF Price'] = etf_df['ETF MV'] / etf_df['ETF MV'].iloc[0] * 100  # Normalized price
    etf_df['ETF return'] = etf_df['ETF Price'].pct_change()
    etf_df['ETF dollar pnl'] = etf_df['ETF MV'].shift(1) * etf_df['ETF return']

    # Create previous date mapping based on actual dates in data
    date_map = {dates[i]: dates[i-1] for i in range(1, len(dates))}
    df['prev_date'] = df['Date'].map(date_map)

    # Get previous values based on actual previous date
    prev_data = df.set_index(['Date', 'Ticker'])[['Position', 'calculated_stock_price', 'Market Value']]
    prev_data = prev_data.rename(columns={
        'Position': 'prev_position',
        'calculated_stock_price': 'prev_price',
        'Market Value': 'prev_mv'
    })

    df = df.merge(
        prev_data,
        left_on=['prev_date', 'Ticker'],
        right_index=True,
        how='left'
    )

    # Check for enter/exit
    df['is_entry'] = df['prev_position'].isna() | (df['prev_position'] == 0)
    df['is_exit'] = (df['Position'] == 0) & (df['prev_position'].notna())
    df['is_continuous'] = ~df['is_entry'] & ~df['is_exit']

    # Calculate stock return only for continuous positions
    df['stock return'] = df.apply(lambda row:
        (row['calculated_stock_price'] - row['prev_price']) / row['prev_price']
        if row['is_continuous'] and not pd.isna(row['prev_price']) and row['prev_price'] != 0 else np.nan,
        axis=1
    )

    df['stock MV'] = df['calculated_stock_price'] * df['Position']

    # Calculate stock dollar pnl as current MV - previous MV
    df['stock dollar pnl'] = df.apply(lambda row:
        row['stock MV'] - row['prev_mv'] if row['is_continuous'] and not pd.isna(row['prev_mv']) else 0,
        axis=1
    )

    # Calculate inflows/outflows based on position status
    df['stock inflows/outflows'] = df.apply(lambda row:
        row['Position'] * row['calculated_stock_price'] if row['is_entry'] else
        -row['prev_position'] * row['prev_price'] if row['is_exit'] else
        (row['Position'] - row['prev_position']) * (row['calculated_stock_price'] + row['prev_price']) / 2,
        axis=1
    )

    df['stock adj pnl'] = df['stock dollar pnl'] - df['stock inflows/outflows']

    # Aggregate stock inflows/outflows to ETF level
    etf_inflows = df.groupby('Date')['stock inflows/outflows'].sum()
    etf_df['ETF inflows/outflows'] = etf_inflows
    etf_df['ETF adj pnl'] = etf_df['ETF dollar pnl'] - etf_df['ETF inflows/outflows']

    return df, etf_df

def save_results(etf_name, df, etf_df):
    output_dir = Path(__file__).parent.parent / 'output'
    output_file = output_dir / f'{etf_name}_daily_metrics.xlsx'

    # Include all calculated columns for stock metrics
    stock_output = df[['Date', 'Ticker', 'Position', 'calculated_stock_price',
                       'prev_date', 'prev_position', 'prev_price', 'prev_mv',
                       'stock return', 'stock MV',
                       'is_entry', 'is_exit', 'is_continuous',
                       'stock dollar pnl', 'stock inflows/outflows', 'stock adj pnl']].copy()

    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        stock_output.to_excel(writer, sheet_name='Stock_Metrics', index=False)
        etf_df.to_excel(writer, sheet_name='ETF_Metrics')

if __name__ == '__main__':
    etfs = ['ARKK', 'ARKQ', 'ARKW', 'ARKG', 'ARKF', 'ARKX']

    for etf in etfs:
        print(f"Processing {etf}...")
        holdings_df = load_holdings_data(etf)
        stock_df, etf_metrics = calculate_daily_metrics(holdings_df)
        save_results(etf, stock_df, etf_metrics)
        print(f"Saved {etf}_daily_metrics.xlsx")