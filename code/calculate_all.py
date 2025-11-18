"""
Unified drawdown calculation for all data types:
- Indices (^RUA, etc.)
- Peer Groups (by GICS)
- Individual ARK stocks
"""

import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.metrics.pairwise import cosine_similarity
import os

# Global cache
_cache = {}

# GICS name mapping for ARK truncated names
GICS_NAME_MAPPING = {
    'Health Care Equipment & Servic': 'Health Care Equipment & Services',
    'Technology Hardware & Equipmen': 'Technology Hardware & Equipment',
    'Semiconductors & Semiconductor': 'Semiconductors & Semiconductor Equipment',
    'Consumer Discretionary Distrib': 'Consumer Discretionary Distribution & Retail',
    'Pharmaceuticals, Biotechnology': 'Pharmaceuticals, Biotechnology & Life Sciences',
    'Real Estate Management & Devel': 'Real Estate Management & Development',
    'Commercial & Professional Serv': 'Commercial & Professional Services',
    'Consumer Staples Distribution': 'Consumer Staples Distribution & Retail'
}


# ============================================================================
# GLOBAL DATE CONFIGURATION
# ============================================================================

# Global analysis period - set by main.py
START_DATE = pd.to_datetime('2024-04-01')
END_DATE = pd.to_datetime('2025-11-10')


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def filter_valid_gics(df, gics_col='GICS'):
    """Filter out invalid GICS values from dataframe"""
    if len(df) == 0 or gics_col not in df.columns:
        return df

    if df[gics_col].dtype != 'object':
        return df

    return df[
        ~df[gics_col].str.contains('#N/A', na=False, case=False) &
        ~df[gics_col].str.contains('Field Not Applicable', na=False, case=False) &
        (df[gics_col] != '--') &
        (df[gics_col].str.strip() != '')
    ].copy()


# ============================================================================
# CORE DRAWDOWN FUNCTIONS
# ============================================================================

def find_max_drawdown_in_period(df, value_col='Value'):
    """Find the maximum drawdown in a given period"""
    if df.empty or len(df) < 2:
        return None

    df = df.copy()
    df['Running_Peak'] = df[value_col].cummax()
    df['Drawdown'] = (df[value_col] - df['Running_Peak']) / df['Running_Peak'] * 100

    min_dd = df['Drawdown'].min()
    if pd.isna(min_dd) or min_dd >= 0:
        return None

    min_idx = df['Drawdown'].idxmin()
    if pd.isna(min_idx):
        return None

    df_before = df.loc[:min_idx]
    peak_val = df_before[value_col].max()
    peak_idx = df_before[value_col].idxmax()

    if pd.isna(peak_idx):
        return None

    return {
        'peak_date': peak_idx,
        'trough_date': min_idx,
        'peak_price': peak_val,
        'trough_price': df.loc[min_idx, value_col],
        'depth_pct': min_dd
    }


def find_top_n_drawdowns(df, n=10, value_col='Value'):
    """Recursively find top N drawdowns in non-overlapping periods"""
    drawdowns = []
    remaining_periods = [(df.index[0], df.index[-1])]

    for rank in range(1, n + 1):
        best_dd = None
        best_dd_value = 0
        best_period_idx = -1
        best_split = None

        for i, (start, end) in enumerate(remaining_periods):
            period_df = df.loc[start:end]
            dd = find_max_drawdown_in_period(period_df, value_col)

            if dd and dd['depth_pct'] < best_dd_value:
                best_dd = dd
                best_dd_value = dd['depth_pct']
                best_period_idx = i
                best_split = (start, end)

        if best_dd is None:
            break

        best_dd['rank'] = rank
        best_dd['Name'] = f'Drawdown_{rank}'
        best_dd['peak_date'] = best_dd['peak_date'].strftime('%Y-%m-%d')
        best_dd['trough_date'] = best_dd['trough_date'].strftime('%Y-%m-%d')
        best_dd['days_to_trough'] = (pd.to_datetime(best_dd['trough_date']) - pd.to_datetime(best_dd['peak_date'])).days
        drawdowns.append(best_dd)

        start, end = best_split
        peak_date = pd.to_datetime(best_dd['peak_date'])
        trough_date = pd.to_datetime(best_dd['trough_date'])

        remaining_periods.pop(best_period_idx)

        if start < peak_date and (peak_date - start).days > 1:
            day_before_peak = peak_date - pd.Timedelta(days=1)
            if day_before_peak >= start:
                remaining_periods.append((start, day_before_peak))

        if trough_date < end and (end - trough_date).days > 1:
            day_after_trough = trough_date + pd.Timedelta(days=1)
            if day_after_trough <= end:
                remaining_periods.append((day_after_trough, end))

    return pd.DataFrame(drawdowns)


def calculate_drawdown_metrics(df, value_col='Value'):
    """Calculate complete drawdown metrics including current and top 10"""
    top_drawdowns = find_top_n_drawdowns(df, n=10, value_col=value_col)

    if top_drawdowns.empty:
        return None

    peak_price = df[value_col].max()
    peak_date = df[value_col].idxmax()
    current_price = df[value_col].iloc[-1]
    current_date = df.index[-1]
    actual_current_dd = ((current_price - peak_price) / peak_price) * 100

    first_price = df[value_col].iloc[0]
    last_price = df[value_col].iloc[-1]
    overall_return = ((last_price - first_price) / first_price) * 100

    period_returns = []
    for _, row in top_drawdowns.iterrows():
        period_return = ((row['trough_price'] - row['peak_price']) / row['peak_price']) * 100
        period_returns.append(round(period_return, 2))

    top_drawdowns['Period_Return_%'] = period_returns
    top_drawdowns['RoMaD'] = ''
    if len(top_drawdowns) > 0:
        max_drawdown = top_drawdowns.iloc[0]['depth_pct']
        if max_drawdown < 0:
            romad = overall_return / abs(max_drawdown)
            top_drawdowns.loc[top_drawdowns.index[0], 'RoMaD'] = round(romad, 2)

    top_drawdowns['peak_price'] = top_drawdowns['peak_price'].round(2)
    top_drawdowns['trough_price'] = top_drawdowns['trough_price'].round(2)
    top_drawdowns['depth_pct'] = top_drawdowns['depth_pct'].round(2)

    current_period_return = ((current_price - peak_price) / peak_price) * 100

    current_dd_row = pd.DataFrame([{
        'Name': 'Current_Drawdown',
        'rank': 'Current',
        'peak_date': peak_date.strftime('%Y-%m-%d'),
        'trough_date': current_date.strftime('%Y-%m-%d'),
        'peak_price': round(peak_price, 2),
        'trough_price': round(current_price, 2),
        'depth_pct': round(actual_current_dd, 2),
        'days_to_trough': (current_date - peak_date).days,
        'Period_Return_%': round(current_period_return, 2),
        'RoMaD': ''
    }])

    cols = ['Name', 'rank', 'peak_date', 'trough_date', 'peak_price', 'trough_price',
            'depth_pct', 'days_to_trough', 'Period_Return_%', 'RoMaD']
    top_drawdowns = top_drawdowns[cols]

    all_drawdowns = pd.concat([current_dd_row, top_drawdowns], ignore_index=True)
    return all_drawdowns


# ============================================================================
# DATA LOADING FUNCTIONS
# ============================================================================

def load_r3000_holdings():
    """Load R3000 holdings data with caching"""
    if 'r3000_holdings' in _cache:
        return _cache['r3000_holdings']

    base_dir = Path(__file__).parent.parent
    file_path = base_dir / 'input' / 'IWV_Transformed_Data.xlsx'

    # Read both 2024 and 2025 sheets
    all_data = []
    for sheet in ['2024', '2025']:
        df_sheet = pd.read_excel(file_path, sheet_name=sheet)
        all_data.append(df_sheet)

    # Combine both sheets
    df_holdings = pd.concat(all_data, ignore_index=True)

    # Convert Date to datetime
    df_holdings['Date'] = pd.to_datetime(df_holdings['Date'])

    # Calculate Market_Value = Position * Price
    df_holdings['Market_Value'] = df_holdings['Position'] * df_holdings['Price']

    # Remove rows where Price or Position is NaN (can't calculate Market_Value)
    df_holdings = df_holdings.dropna(subset=['Price', 'Position']).copy()

    # Ensure correct data types
    df_holdings['Position'] = df_holdings['Position'].astype(float)
    df_holdings['Price'] = df_holdings['Price'].astype(float)
    df_holdings['Market_Value'] = df_holdings['Market_Value'].astype(float)

    _cache['r3000_holdings'] = df_holdings
    return df_holdings


def load_industry_info(source='r3000'):
    """Load industry classification from 'value' sheet, using 'GICS Ind Grp Name' column

    Maps tickers by their symbol only (e.g., 'AAPL' from 'AAPL US Equity')
    to handle different exchange codes (US/UW/UN/etc)
    """
    cache_key = f'{source}_industry'
    if cache_key in _cache:
        return _cache[cache_key]

    base_dir = Path(__file__).parent.parent

    if source == 'r3000':
        file_path = base_dir / 'input' / 'R3000 industry info.xlsx'
    else:  # ark
        file_path = base_dir / 'input' / 'ARK ETFs industry info.xlsx'

    # Read 'value' sheet for both files
    df = pd.read_excel(file_path, sheet_name='value')

    # Find the GICS Industry Group column (may have \n in column name or different variations)
    gics_col = None
    for col in df.columns:
        if 'GICS Ind Grp Name' in col or 'GICS Industry Group' in col:
            gics_col = col
            break

    if gics_col is None:
        raise ValueError(f"Cannot find 'GICS Ind Grp Name' or 'GICS Industry Group' column in {file_path}. Found columns: {list(df.columns)}")

    # Extract Bloomberg Name and GICS Industry Group
    df_clean = df[['Bloomberg Name', gics_col]].copy()
    df_clean.columns = ['Bloomberg_Name', 'GICS']

    # Remove rows where GICS is NaN
    df_valid = df_clean[df_clean['GICS'].notna()].copy()

    # Fix truncated GICS names in ARK data to match R3000 full names
    if source == 'ark':
        df_valid['GICS'] = df_valid['GICS'].replace(GICS_NAME_MAPPING)

    # For R3000: Create symbol-based mapping (match by ticker symbol only, not full Bloomberg Name)
    # This handles cases where holdings use "AAPL US Equity" but industry info has "AAPL UW Equity"
    if source == 'r3000':
        # Extract symbol from Bloomberg Name (first part before space)
        df_valid['Symbol'] = df_valid['Bloomberg_Name'].str.split().str[0]

        # Create mapping for both symbol and full Bloomberg Name
        industry_dict = {}
        for _, row in df_valid.iterrows():
            symbol = row['Symbol']
            gics = row['GICS']
            # Map both "AAPL" and "AAPL US/UW/UN Equity" formats
            industry_dict[symbol] = gics
            industry_dict[row['Bloomberg_Name']] = gics

    else:
        # For ARK: Use full Bloomberg Name (they already match)
        industry_dict = dict(zip(df_valid['Bloomberg_Name'], df_valid['GICS']))

    # Report missing GICS info
    missing_count = len(df_clean) - len(df_valid)
    if missing_count > 0:
        print(f"  WARNING: {missing_count} stocks have missing GICS Industry Group in {source.upper()} file")
        print(f"  Missing stocks: {df_clean[df_clean['GICS'].isna()]['Bloomberg_Name'].tolist()[:5]}")

    _cache[cache_key] = industry_dict
    return industry_dict


def load_ark_holdings(etf_name):
    """Load ARK ETF holdings with caching"""
    cache_key = f'ark_holdings_{etf_name}'
    if cache_key in _cache:
        return _cache[cache_key]

    base_dir = Path(__file__).parent.parent
    file_path = base_dir / 'input' / f'{etf_name}_Transformed_Data.xlsx'

    df = pd.read_excel(file_path)
    df = df[['Date', 'Ticker', 'Bloomberg Name', 'Position', 'Market Value']]
    df = df[df['Ticker'] != 'USD']
    df['Date'] = pd.to_datetime(df['Date'])
    df['Price'] = df['Market Value'] / df['Position']

    _cache[cache_key] = df
    return df


# ============================================================================
# PEER GROUP FUNCTIONS
# ============================================================================

def calculate_peer_group_prices_mv():
    """Calculate peer group total market values (sum of market values by GICS)"""
    if 'peer_group_prices_mv' in _cache:
        return _cache['peer_group_prices_mv']

    holdings = load_r3000_holdings()
    industry_dict = load_industry_info('r3000')

    # First try exact match on full ticker
    holdings['GICS'] = holdings['Ticker'].map(industry_dict)

    # For unmatched tickers, try matching by symbol only
    unmatched_mask = holdings['GICS'].isna()
    if unmatched_mask.sum() > 0:
        holdings.loc[unmatched_mask, 'Symbol'] = holdings.loc[unmatched_mask, 'Ticker'].str.split().str[0]
        holdings.loc[unmatched_mask, 'GICS'] = holdings.loc[unmatched_mask, 'Symbol'].map(industry_dict)

    # Report missing industry info for R3000 stocks (only once)
    if 'peer_group_prices_weighted' not in _cache:
        missing_gics = holdings[holdings['GICS'].isna()]
        if len(missing_gics) > 0:
            missing_tickers = missing_gics['Ticker'].unique()
            print(f"\n  WARNING: {len(missing_tickers)} R3000 stocks have NO industry info:")
            print("  Missing tickers:")
            for ticker in sorted(missing_tickers)[:20]:
                print(f"    - {ticker}")
            if len(missing_tickers) > 20:
                print(f"    ... and {len(missing_tickers) - 20} more")
            print(f"  Total holdings records affected: {len(missing_gics):,}")
            print()

    # Filter holdings with valid GICS info
    holdings_with_gics = holdings[holdings['GICS'].notna()].copy()
    holdings_with_gics = filter_valid_gics(holdings_with_gics, 'GICS')

    # Sum market values by Date and GICS
    peer_prices = holdings_with_gics.groupby(['Date', 'GICS'])['Market_Value'].sum().reset_index()
    peer_prices.columns = ['Date', 'GICS', 'Value']

    _cache['peer_group_prices_mv'] = peer_prices
    return peer_prices


def calculate_peer_group_prices_weighted():
    """Calculate peer group weighted prices

    For each stock:
    1. Calculate weight = stock's Market_Value / total R3000 Market_Value on that day
    2. Calculate weighted_price = weight × stock's Price
    3. Sum weighted_prices by GICS group
    """
    if 'peer_group_prices_weighted' in _cache:
        return _cache['peer_group_prices_weighted']

    holdings = load_r3000_holdings()
    industry_dict = load_industry_info('r3000')

    # First try exact match on full ticker
    holdings['GICS'] = holdings['Ticker'].map(industry_dict)

    # For unmatched tickers, try matching by symbol only
    unmatched_mask = holdings['GICS'].isna()
    if unmatched_mask.sum() > 0:
        holdings.loc[unmatched_mask, 'Symbol'] = holdings.loc[unmatched_mask, 'Ticker'].str.split().str[0]
        holdings.loc[unmatched_mask, 'GICS'] = holdings.loc[unmatched_mask, 'Symbol'].map(industry_dict)

    # Filter holdings with valid GICS info
    holdings_with_gics = holdings[holdings['GICS'].notna()].copy()
    holdings_with_gics = filter_valid_gics(holdings_with_gics, 'GICS')

    # Calculate total R3000 market value for each date
    daily_total_mv = holdings_with_gics.groupby('Date')['Market_Value'].sum().reset_index()
    daily_total_mv.columns = ['Date', 'Total_MV']

    # Merge to get daily total MV for each stock
    holdings_with_gics = holdings_with_gics.merge(daily_total_mv, on='Date', how='left')

    # Calculate weight = stock's MV / total R3000 MV
    holdings_with_gics['Weight'] = holdings_with_gics['Market_Value'] / holdings_with_gics['Total_MV']

    # Calculate weighted price = weight × stock price
    holdings_with_gics['Weighted_Price'] = holdings_with_gics['Weight'] * holdings_with_gics['Price']

    # Sum weighted prices by Date and GICS
    peer_prices = holdings_with_gics.groupby(['Date', 'GICS'])['Weighted_Price'].sum().reset_index()
    peer_prices.columns = ['Date', 'GICS', 'Value']

    _cache['peer_group_prices_weighted'] = peer_prices
    return peer_prices


def calculate_peer_group_prices():
    """Backward compatibility: defaults to MV version"""
    return calculate_peer_group_prices_mv()


def build_peer_group_lookup(peer_prices):
    """Build efficient lookup structure for peer group prices"""
    if 'peer_lookup' in _cache:
        return _cache['peer_lookup']

    lookup = {}
    for gics in peer_prices['GICS'].unique():
        gics_data = peer_prices[peer_prices['GICS'] == gics].copy()
        lookup[gics] = dict(zip(gics_data['Date'], gics_data['Value']))

    _cache['peer_lookup'] = lookup
    return lookup


# ============================================================================
# CALCULATION FUNCTIONS
# ============================================================================

def _calculate_price_based_drawdowns(tickers):
    """Generic function to calculate drawdowns from price CSV files

    Args:
        tickers: List of ticker symbols to process
    """
    base_dir = Path(__file__).parent.parent
    output_dir = base_dir / 'output'
    start_date = START_DATE
    end_date = END_DATE

    for ticker in tickers:
        price_file = output_dir / f'{ticker}_prices.csv'
        if not price_file.exists():
            continue

        df_prices = pd.read_csv(price_file)
        df_prices['Date'] = pd.to_datetime(df_prices['Date'])
        df_prices.set_index('Date', inplace=True)
        df_prices.columns = ['Value']

        # Filter to analysis period
        df_period = df_prices[(df_prices.index >= start_date) & (df_prices.index <= end_date)].copy()

        if len(df_period) < 2:
            continue

        # Calculate drawdowns
        all_drawdowns = calculate_drawdown_metrics(df_period)

        if all_drawdowns is not None:
            output_file = output_dir / f'{ticker}_drawdown_2024-2025.xlsx'
            with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                all_drawdowns.to_excel(writer, sheet_name='Drawdowns', index=False)


def calculate_ark_etf_drawdowns():
    """Calculate drawdowns for ARK ETFs based on ETF price"""
    etfs = ['ARKK', 'ARKQ', 'ARKW', 'ARKG', 'ARKF', 'ARKX']
    _calculate_price_based_drawdowns(etfs)


def calculate_index_drawdowns():
    """Calculate drawdowns for indices (^RUA, etc.)"""
    indices = ['^RUA']
    _calculate_price_based_drawdowns(indices)


def calculate_peer_group_drawdowns():
    """Calculate drawdowns for each peer group"""

    peer_prices = calculate_peer_group_prices()
    peer_prices = filter_valid_gics(peer_prices, 'GICS')

    start_date = START_DATE
    end_date = END_DATE
    peer_prices_period = peer_prices[(peer_prices['Date'] >= start_date) & (peer_prices['Date'] <= end_date)]

    base_dir = Path(__file__).parent.parent
    output_file = base_dir / 'output' / 'R3000_peer_groups_drawdown_2024-2025.xlsx'

    all_results = {}
    gics_groups = sorted(peer_prices_period['GICS'].unique())

    for gics in gics_groups:
        group_data = peer_prices_period[peer_prices_period['GICS'] == gics].copy()
        group_data = group_data.sort_values('Date').set_index('Date')

        if len(group_data) < 2:
            continue

        all_drawdowns = calculate_drawdown_metrics(group_data)
        if all_drawdowns is not None:
            all_results[gics] = all_drawdowns

    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        for gics, df in all_results.items():
            sheet_name = gics[:31].replace('/', '_').replace('\\', '_').replace(':', '_')
            df.to_excel(writer, sheet_name=sheet_name, index=False)



def calculate_cosine_similarity(stock_returns, peer_returns):
    """Calculate cosine similarity between returns"""
    common_dates = stock_returns.index.intersection(peer_returns.index)
    if len(common_dates) < 2:
        return None

    stock_vals = stock_returns.loc[common_dates].values.reshape(1, -1)
    peer_vals = peer_returns.loc[common_dates].values.reshape(1, -1)

    if np.any(np.isnan(stock_vals)) or np.any(np.isnan(peer_vals)):
        return None
    if np.std(stock_vals) == 0 or np.std(peer_vals) == 0:
        return None

    similarity = cosine_similarity(stock_vals, peer_vals)[0][0]
    return round(similarity, 4)


def _add_peer_group_metrics(top_drawdowns, gics, stock_returns, peer_prices, peer_lookup):
    """Add peer group comparison metrics to drawdown dataframe

    Args:
        top_drawdowns: DataFrame with stock drawdown data
        gics: GICS industry group name
        stock_returns: Stock return series
        peer_prices: Peer group price dataframe
        peer_lookup: Peer group lookup dictionary

    Returns:
        DataFrame with added peer group columns
    """
    # Try exact match first, then try prefix match (for truncated GICS names)
    if gics in peer_prices['GICS'].values:
        gics_key = gics
    else:
        # Find matching GICS by prefix (handle Excel 30-char truncation)
        matching = peer_prices[peer_prices['GICS'].str.startswith(gics[:25])]['GICS'].unique()
        gics_key = matching[0] if len(matching) > 0 else gics

    peer_data = peer_prices[peer_prices['GICS'] == gics_key].copy()
    peer_data = peer_data.sort_values('Date').set_index('Date')
    peer_returns = peer_data['Value'].pct_change(fill_method=None)

    peer_names = []
    peer_peaks = []
    peer_troughs = []
    peer_dds = []
    cos_sims = []

    for _, row in top_drawdowns.iterrows():
        peak_date_dd = pd.to_datetime(row['peak_date'])
        trough_date_dd = pd.to_datetime(row['trough_date'])

        peer_names.append(gics)

        # Use the same gics_key for peer_lookup
        peer_peak = peer_lookup[gics_key].get(peak_date_dd) if gics_key in peer_lookup else None
        peer_trough = peer_lookup[gics_key].get(trough_date_dd) if gics_key in peer_lookup else None

        if peer_peak and peer_trough:
            peer_peaks.append(round(peer_peak, 2))
            peer_troughs.append(round(peer_trough, 2))
            peer_dd = ((peer_trough - peer_peak) / peer_peak) * 100
            peer_dds.append(round(peer_dd, 2))
        else:
            peer_peaks.append(None)
            peer_troughs.append(None)
            peer_dds.append(None)

        period_stock_returns = stock_returns[peak_date_dd:trough_date_dd]
        period_peer_returns = peer_returns[peak_date_dd:trough_date_dd]
        cos_sim = calculate_cosine_similarity(period_stock_returns, period_peer_returns)
        cos_sims.append(cos_sim)

    top_drawdowns['PeerGroup_Name'] = peer_names
    top_drawdowns['PeerGroup_Peak_Value'] = peer_peaks
    top_drawdowns['PeerGroup_Trough_Value'] = peer_troughs
    top_drawdowns['PeerGroup_DD_%'] = peer_dds
    top_drawdowns['Cosine_Similarity'] = cos_sims

    return top_drawdowns


def calculate_ark_stock_drawdowns():
    """Calculate drawdowns for individual ARK stocks"""
    ark_industry = load_industry_info('ark')
    peer_prices = calculate_peer_group_prices()
    peer_prices = filter_valid_gics(peer_prices, 'GICS')

    peer_lookup = build_peer_group_lookup(peer_prices)

    etfs = ['ARKK', 'ARKQ', 'ARKW', 'ARKG', 'ARKF', 'ARKX']
    stock_etf_map = {}

    for etf in etfs:
        holdings = load_ark_holdings(etf)
        for ticker in holdings['Ticker'].unique():
            ticker_clean = ticker.split()[0] if isinstance(ticker, str) else ticker
            if ticker_clean not in stock_etf_map:
                stock_etf_map[ticker_clean] = []
            stock_etf_map[ticker_clean].append((etf, ticker))

    base_dir = Path(__file__).parent.parent
    output_dir = base_dir / 'output' / 'stock_drawdowns'
    output_dir.mkdir(parents=True, exist_ok=True)

    start_date = START_DATE
    end_date = END_DATE

    total_stocks = len(stock_etf_map)
    print(f"  Processing {total_stocks} stocks...")
    processed = 0

    for ticker_clean, etf_list in stock_etf_map.items():
        processed += 1
        if processed % 10 == 0 or processed == total_stocks:
            print(f"  Progress: {processed}/{total_stocks} stocks")
        output_file = output_dir / f'{ticker_clean}_drawdown_2024-2025.xlsx'

        if output_file.exists():
            os.remove(output_file)

        results = {}

        for etf, ticker_full in etf_list:
            holdings = load_ark_holdings(etf)
            stock_data = holdings[holdings['Ticker'] == ticker_full].copy()

            if len(stock_data) < 30:
                continue

            bloomberg_name = stock_data['Bloomberg Name'].iloc[0]
            gics = ark_industry.get(bloomberg_name)
            if gics is None:
                continue

            stock_period = stock_data[(stock_data['Date'] >= start_date) & (stock_data['Date'] <= end_date)].copy()
            if len(stock_period) < 30:
                continue

            stock_period = stock_period.sort_values('Date').set_index('Date')
            stock_period = stock_period.rename(columns={'Price': 'Value'})

            top_drawdowns = calculate_drawdown_metrics(stock_period)
            if top_drawdowns is None:
                continue

            # Add peer group comparison
            stock_returns = stock_period['Value'].pct_change(fill_method=None)
            top_drawdowns = _add_peer_group_metrics(top_drawdowns, gics, stock_returns, peer_prices, peer_lookup)

            cols = ['Name', 'rank', 'peak_date', 'trough_date', 'peak_price', 'trough_price',
                    'depth_pct', 'days_to_trough', 'Period_Return_%', 'RoMaD',
                    'PeerGroup_Name', 'PeerGroup_Peak_Value', 'PeerGroup_Trough_Value',
                    'PeerGroup_DD_%', 'Cosine_Similarity']
            top_drawdowns = top_drawdowns[cols]

            results[etf] = top_drawdowns

        if results:
            with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                for etf, df in results.items():
                    df.to_excel(writer, sheet_name=etf, index=False)


if __name__ == '__main__':
    calculate_ark_etf_drawdowns()
    calculate_index_drawdowns()
    calculate_peer_group_drawdowns()
    calculate_ark_stock_drawdowns()
