import pandas as pd
import numpy as np
import os
from pathlib import Path

def find_max_drawdown_in_period(df):
    """Find the maximum drawdown in a given period"""
    if df.empty or len(df) < 2:
        return None
    
    # Calculate running peak and drawdown
    df = df.copy()
    df['Running_Peak'] = df['Close'].cummax()
    df['Drawdown'] = (df['Close'] - df['Running_Peak']) / df['Running_Peak'] * 100
    
    # Find the minimum (worst) drawdown
    min_dd = df['Drawdown'].min()
    if min_dd >= 0:  # No drawdown in this period
        return None
    
    min_idx = df['Drawdown'].idxmin()
    
    # Find the peak before this trough
    df_before = df.loc[:min_idx]
    peak_val = df_before['Close'].max()
    peak_idx = df_before['Close'].idxmax()
    
    return {
        'peak_date': peak_idx,
        'trough_date': min_idx,
        'peak_price': peak_val,
        'trough_price': df.loc[min_idx, 'Close'],
        'depth_pct': min_dd
    }

def find_top_n_drawdowns(df, n=10):
    """Recursively find top N drawdowns in non-overlapping periods"""
    drawdowns = []
    remaining_periods = [(df.index[0], df.index[-1])]
    
    for rank in range(1, n + 1):
        best_dd = None
        best_dd_value = 0
        best_period_idx = -1
        best_split = None
        
        # Find the worst drawdown across all remaining periods
        for i, (start, end) in enumerate(remaining_periods):
            period_df = df.loc[start:end]
            dd = find_max_drawdown_in_period(period_df)
            
            if dd and dd['depth_pct'] < best_dd_value:
                best_dd = dd
                best_dd_value = dd['depth_pct']
                best_period_idx = i
                best_split = (start, end)
        
        if best_dd is None:
            break
        
        # Add the drawdown to results
        best_dd['rank'] = rank
        best_dd['Name'] = f'Drawdown_{rank}'
        best_dd['peak_date'] = best_dd['peak_date'].strftime('%Y-%m-%d')
        best_dd['trough_date'] = best_dd['trough_date'].strftime('%Y-%m-%d')
        best_dd['days_to_trough'] = (pd.to_datetime(best_dd['trough_date']) - pd.to_datetime(best_dd['peak_date'])).days
        drawdowns.append(best_dd)
        
        # Split the period into two parts (before peak and after trough)
        start, end = best_split
        peak_date = pd.to_datetime(best_dd['peak_date'])
        trough_date = pd.to_datetime(best_dd['trough_date'])
        
        # Remove the used period and add the remaining segments
        remaining_periods.pop(best_period_idx)
        
        # Add period before the drawdown (if exists)
        if start < peak_date and (peak_date - start).days > 1:
            # Need at least one day before peak
            day_before_peak = peak_date - pd.Timedelta(days=1)
            if day_before_peak >= start:
                remaining_periods.append((start, day_before_peak))
        
        # Add period after the drawdown (if exists)
        if trough_date < end and (end - trough_date).days > 1:
            # Start from day after trough
            day_after_trough = trough_date + pd.Timedelta(days=1)
            if day_after_trough <= end:
                remaining_periods.append((day_after_trough, end))
    
    return pd.DataFrame(drawdowns)

# Set up paths relative to script location
script_dir = Path(__file__).parent
project_root = script_dir.parent
output_dir = project_root / 'output'

# ARK ETF list - all 6 ETFs with transformed data
ark_etfs = ['ARKK', 'ARKQ', 'ARKW', 'ARKG', 'ARKF', 'ARKX']

# Process each ETF
for etf in ark_etfs:
    filename = f"{output_dir}/{etf}_prices.csv"
    
    if os.path.exists(filename):
        print(f"\nProcessing {etf}...")
        
        # Read price data
        df = pd.read_csv(filename)
        df['Date'] = pd.to_datetime(df['Date'])
        df.set_index('Date', inplace=True)
        
        # Filter for 2025 data only
        df_2025 = df[df.index.year == 2025]
        
        if df_2025.empty:
            print(f"  No 2025 data available")
            continue
        
        # Find top 10 drawdowns
        top_drawdowns = find_top_n_drawdowns(df_2025, n=10)
        
        if not top_drawdowns.empty:
            # Calculate current drawdown from 2025 peak
            peak_2025 = df_2025['Close'].max()
            peak_date_2025 = df_2025['Close'].idxmax()
            current_price = df_2025['Close'].iloc[-1]
            current_date = df_2025.index[-1]
            actual_current_dd = ((current_price - peak_2025) / peak_2025) * 100
            
            # Calculate 2025 portfolio return
            first_price_2025 = df_2025['Close'].iloc[0]
            last_price_2025 = df_2025['Close'].iloc[-1]
            portfolio_return_2025 = ((last_price_2025 - first_price_2025) / first_price_2025) * 100
            
            # Add portfolio return column to all rows
            top_drawdowns['Portfolio_Return_%'] = round(portfolio_return_2025, 2)
            
            # Calculate RoMaD for the top drawdown only
            top_drawdowns['RoMaD'] = ''
            if len(top_drawdowns) > 0:
                max_drawdown = top_drawdowns.iloc[0]['depth_pct']
                if max_drawdown < 0:  # Ensure we have a negative drawdown
                    romad = portfolio_return_2025 / abs(max_drawdown)
                    top_drawdowns.loc[top_drawdowns.index[0], 'RoMaD'] = round(romad, 2)
            
            # Round all numeric columns to 2 decimal places
            top_drawdowns['peak_price'] = top_drawdowns['peak_price'].round(2)
            top_drawdowns['trough_price'] = top_drawdowns['trough_price'].round(2)
            top_drawdowns['depth_pct'] = top_drawdowns['depth_pct'].round(2)
            
            # Reorder columns to put Name first
            cols = ['Name', 'rank', 'peak_date', 'trough_date', 'peak_price', 'trough_price', 
                    'depth_pct', 'days_to_trough', 'Portfolio_Return_%', 'RoMaD']
            top_drawdowns = top_drawdowns[cols]
            
            # Create current drawdown dataframe
            current_dd_df = pd.DataFrame([{
                'ETF': etf,
                'Peak_Date': peak_date_2025.strftime('%Y-%m-%d'),
                'Peak_Price': peak_2025,
                'Current_Date': current_date.strftime('%Y-%m-%d'),
                'Current_Price': current_price,
                'Current_Drawdown_%': actual_current_dd
            }])
            
            # Save to Excel with multiple sheets
            with pd.ExcelWriter(f"{output_dir}/{etf}_drawdown_2025.xlsx", engine='openpyxl') as writer:
                top_drawdowns.to_excel(writer, sheet_name='Top_10_Drawdowns', index=False)
                current_dd_df.to_excel(writer, sheet_name='Current_Drawdown', index=False)
            
            print(f"  2025 Peak Price = ${peak_2025:.2f}")
            print(f"  Current Price = ${current_price:.2f}")
            print(f"  Current Drawdown = {actual_current_dd:.2f}%")
            print(f"  2025 Portfolio Return = {portfolio_return_2025:.2f}%")
            if len(top_drawdowns) > 0 and top_drawdowns.iloc[0]['depth_pct'] < 0:
                print(f"  RoMaD = {portfolio_return_2025 / abs(top_drawdowns.iloc[0]['depth_pct']):.2f}")
            print(f"\n  Top Drawdowns:")
            for _, row in top_drawdowns.head(5).iterrows():
                print(f"    #{int(row['rank'])}: {row['depth_pct']:.2f}% (Peak: {row['peak_date']}, Trough: {row['trough_date']})")
            print(f"  Saved to {etf}_drawdown_2025.xlsx")
    else:
        print(f"File {filename} not found")

print(f"\nAll results saved to {output_dir}/")