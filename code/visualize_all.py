"""
Unified visualization for all drawdown types:
- Index drawdowns
- Peer group drawdowns
- Individual stock vs peer group comparisons
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from matplotlib.ticker import FuncFormatter

from calculate_all import (calculate_peer_group_prices, calculate_peer_group_prices_mv,
                           calculate_peer_group_prices_weighted, load_ark_holdings,
                           load_industry_info, START_DATE, END_DATE,
                           filter_valid_gics)


def format_value(x, pos):
    """Format large numbers as M/B/T"""
    if abs(x) >= 1e12:
        return f'${x/1e12:.1f}T'
    elif abs(x) >= 1e9:
        return f'${x/1e9:.1f}B'
    elif abs(x) >= 1e6:
        return f'${x/1e6:.1f}M'
    else:
        return f'${x:.0f}'


def visualize_ark_etf_drawdowns():
    """Visualize ARK ETF drawdowns"""

    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    output_dir = project_root / 'output'

    etfs = ['ARKK', 'ARKQ', 'ARKW', 'ARKG', 'ARKF', 'ARKX']
    start_date = START_DATE
    end_date = END_DATE

    for etf in etfs:

        drawdown_file = output_dir / f'{etf}_drawdown_2024-2025.xlsx'
        if not drawdown_file.exists():
            continue

        # Load ETF price data
        price_file = output_dir / f'{etf}_prices.csv'
        if not price_file.exists():
            continue

        df_prices = pd.read_csv(price_file)
        df_prices['Date'] = pd.to_datetime(df_prices['Date'])
        df_prices.set_index('Date', inplace=True)

        # Filter to analysis period
        df_period = df_prices[(df_prices.index >= start_date) & (df_prices.index <= end_date)].copy()

        if df_period.empty:
            continue

        # Load drawdowns
        all_drawdowns = pd.read_excel(drawdown_file, sheet_name='Drawdowns')
        top_drawdowns = all_drawdowns[all_drawdowns['rank'] != 'Current']

        fig, ax = plt.subplots(figsize=(16, 8))
        ax.plot(df_period.index, df_period['Close'], color='black', linewidth=1.5, zorder=3)

        colors = plt.cm.RdYlGn(np.linspace(0.2, 0.8, min(10, len(top_drawdowns))))

        for plot_idx, (idx, row) in enumerate(top_drawdowns.iterrows()):
            if plot_idx >= 10:
                break
            peak_date = pd.to_datetime(row['peak_date'])
            trough_date = pd.to_datetime(row['trough_date'])
            ax.axvspan(peak_date, trough_date, alpha=0.3, color=colors[plot_idx],
                       label=f"Drawdown {row['rank']}: {row['depth_pct']:.1f}%", zorder=1)

        ax.set_title(f'{etf} Price & Top 10 Drawdowns (Apr 2024 - Oct 2025)',
                     fontsize=16, fontweight='bold')
        ax.set_xlabel('Date', fontsize=12)
        ax.set_ylabel('ETF Price ($)', fontsize=12)
        ax.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        ax.legend(loc='upper left', ncol=2, fontsize=9, framealpha=0.9)
        plt.tight_layout()

        output_file = output_dir / f'{etf}_drawdown_visualization_2024-2025.png'
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()


def visualize_index_drawdowns():
    """Visualize index drawdowns"""

    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    output_dir = project_root / 'output'

    indices = ['^RUA']
    start_date = START_DATE
    end_date = END_DATE

    for index_name in indices:

        price_file = output_dir / f'{index_name}_prices.csv'
        if not price_file.exists():
            continue

        df_prices = pd.read_csv(price_file)
        df_prices['Date'] = pd.to_datetime(df_prices['Date'])
        df_prices.set_index('Date', inplace=True)

        df_period = df_prices[(df_prices.index >= start_date) & (df_prices.index <= end_date)].copy()
        if df_period.empty:
            continue

        drawdown_file = output_dir / f'{index_name}_drawdown_2024-2025.xlsx'
        if not drawdown_file.exists():
            continue

        all_drawdowns = pd.read_excel(drawdown_file, sheet_name='Drawdowns')
        top_drawdowns = all_drawdowns[all_drawdowns['rank'] != 'Current']

        fig, ax = plt.subplots(figsize=(16, 8))
        ax.plot(df_period.index, df_period['Close'], color='black', linewidth=1.5, zorder=3)

        colors = plt.cm.RdYlGn(np.linspace(0.2, 0.8, min(10, len(top_drawdowns))))

        for plot_idx, (idx, row) in enumerate(top_drawdowns.iterrows()):
            if plot_idx >= 10:
                break
            peak_date = pd.to_datetime(row['peak_date'])
            trough_date = pd.to_datetime(row['trough_date'])
            ax.axvspan(peak_date, trough_date, alpha=0.3, color=colors[plot_idx],
                       label=f"Drawdown {row['rank']}: {row['depth_pct']:.1f}%", zorder=1)

        ax.set_title(f'{index_name} Price & Top 10 Drawdowns (Apr 2024 - Oct 2025)',
                     fontsize=16, fontweight='bold')
        ax.set_xlabel('Date', fontsize=12)
        ax.set_ylabel('Price ($)', fontsize=12)
        ax.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        ax.legend(loc='upper left', ncol=2, fontsize=9, framealpha=0.9)
        plt.tight_layout()

        output_file = output_dir / f'{index_name}_drawdown_visualization_2024-2025.png'
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()


def visualize_peer_group_drawdowns_mv():
    """Visualize peer group drawdowns (Market Value)"""

    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    output_dir = project_root / 'output' / 'peer_group_charts_mv'
    output_dir.mkdir(parents=True, exist_ok=True)

    peer_prices = calculate_peer_group_prices_mv()

    start_date = START_DATE
    end_date = END_DATE

    # Filter out invalid GICS
    peer_prices = filter_valid_gics(peer_prices, 'GICS')

    gics_groups = sorted(peer_prices['GICS'].unique())

    print(f"  Generating {len(gics_groups)} peer group MV charts...")

    for gics in gics_groups:

        group_data = peer_prices[peer_prices['GICS'] == gics].copy()
        group_data = group_data[(group_data['Date'] >= start_date) & (group_data['Date'] <= end_date)]

        if group_data.empty:
            continue

        group_data = group_data.sort_values('Date').set_index('Date')

        drawdown_file = project_root / 'output' / 'R3000_peer_groups_drawdown_2024-2025.xlsx'
        if not drawdown_file.exists():
            continue

        sheet_name = gics[:31].replace('/', '_').replace('\\', '_').replace(':', '_')
        try:
            top_drawdowns = pd.read_excel(drawdown_file, sheet_name=sheet_name)
            top_drawdowns = top_drawdowns[top_drawdowns['rank'] != 'Current']
        except:
            continue

        fig, ax = plt.subplots(figsize=(16, 8))
        ax.plot(group_data.index, group_data['Value'], color='black', linewidth=1.5, zorder=3)

        colors = plt.cm.RdYlGn(np.linspace(0.2, 0.8, min(10, len(top_drawdowns))))

        for plot_idx, (idx, row) in enumerate(top_drawdowns.iterrows()):
            if plot_idx >= 10:
                break
            peak_date = pd.to_datetime(row['peak_date'])
            trough_date = pd.to_datetime(row['trough_date'])
            ax.axvspan(peak_date, trough_date, alpha=0.3, color=colors[plot_idx],
                       label=f"Drawdown {row['rank']}: {row['depth_pct']:.1f}%", zorder=1)

        ax.set_title(f'{gics} - Market Value & Top 10 Drawdowns (Apr 2024 - Oct 2025)',
                     fontsize=16, fontweight='bold')
        ax.set_xlabel('Date', fontsize=12)
        ax.set_ylabel('Total Market Value', fontsize=12)
        ax.yaxis.set_major_formatter(FuncFormatter(format_value))
        ax.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        ax.legend(loc='upper left', ncol=2, fontsize=9, framealpha=0.9)
        plt.tight_layout()

        safe_filename = gics.replace('/', '_').replace('\\', '_').replace(':', '_')
        output_file = output_dir / f'{safe_filename}_mv_drawdown_2024-2025.png'
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()


def visualize_peer_group_drawdowns_weighted():
    """Visualize peer group drawdowns (Weighted Price)"""

    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    output_dir = project_root / 'output' / 'peer_group_charts_weighted'
    output_dir.mkdir(parents=True, exist_ok=True)

    peer_prices = calculate_peer_group_prices_weighted()

    start_date = START_DATE
    end_date = END_DATE

    # Filter out invalid GICS
    peer_prices = filter_valid_gics(peer_prices, 'GICS')

    gics_groups = sorted(peer_prices['GICS'].unique())

    print(f"  Generating {len(gics_groups)} peer group weighted charts...")

    for gics in gics_groups:

        group_data = peer_prices[peer_prices['GICS'] == gics].copy()
        group_data = group_data[(group_data['Date'] >= start_date) & (group_data['Date'] <= end_date)]

        if group_data.empty:
            continue

        group_data = group_data.sort_values('Date').set_index('Date')

        drawdown_file = project_root / 'output' / 'R3000_peer_groups_drawdown_2024-2025.xlsx'
        if not drawdown_file.exists():
            continue

        sheet_name = gics[:31].replace('/', '_').replace('\\', '_').replace(':', '_')
        try:
            top_drawdowns = pd.read_excel(drawdown_file, sheet_name=sheet_name)
            top_drawdowns = top_drawdowns[top_drawdowns['rank'] != 'Current']
        except:
            continue

        fig, ax = plt.subplots(figsize=(16, 8))
        ax.plot(group_data.index, group_data['Value'], color='darkgreen', linewidth=1.5, zorder=3)

        colors = plt.cm.RdYlGn(np.linspace(0.2, 0.8, min(10, len(top_drawdowns))))

        for plot_idx, (idx, row) in enumerate(top_drawdowns.iterrows()):
            if plot_idx >= 10:
                break
            peak_date = pd.to_datetime(row['peak_date'])
            trough_date = pd.to_datetime(row['trough_date'])
            ax.axvspan(peak_date, trough_date, alpha=0.3, color=colors[plot_idx],
                       label=f"Drawdown {row['rank']}: {row['depth_pct']:.1f}%", zorder=1)

        ax.set_title(f'{gics} - Weighted Price & Top 10 Drawdowns (Apr 2024 - Oct 2025)',
                     fontsize=16, fontweight='bold')
        ax.set_xlabel('Date', fontsize=12)
        ax.set_ylabel('Weighted Price Index', fontsize=12)
        ax.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        ax.legend(loc='upper left', ncol=2, fontsize=9, framealpha=0.9)
        plt.tight_layout()

        safe_filename = gics.replace('/', '_').replace('\\', '_').replace(':', '_')
        output_file = output_dir / f'{safe_filename}_weighted_drawdown_2024-2025.png'
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()


def visualize_peer_group_drawdowns():
    """Wrapper to call both peer group visualization functions"""
    visualize_peer_group_drawdowns_mv()
    visualize_peer_group_drawdowns_weighted()


def visualize_ark_stocks_mv():
    """Visualize ARK stocks vs peer groups (Market Value)"""
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    output_dir = project_root / 'output' / 'stock_drawdowns'
    chart_dir = project_root / 'output' / 'stock_charts_mv'
    chart_dir.mkdir(parents=True, exist_ok=True)

    ark_industry = load_industry_info('ark')
    peer_prices = calculate_peer_group_prices_mv()
    peer_prices = filter_valid_gics(peer_prices, 'GICS')

    etfs = ['ARKK', 'ARKQ', 'ARKW', 'ARKG', 'ARKF', 'ARKX']
    stock_etf_map = {}

    for etf in etfs:
        holdings = load_ark_holdings(etf)
        for ticker in holdings['Ticker'].unique():
            ticker_clean = ticker.split()[0] if isinstance(ticker, str) else ticker
            if ticker_clean not in stock_etf_map:
                stock_etf_map[ticker_clean] = []
            stock_etf_map[ticker_clean].append((etf, ticker))

    start_date = START_DATE
    end_date = END_DATE

    for ticker_clean, etf_list in stock_etf_map.items():
        drawdown_file = output_dir / f'{ticker_clean}_drawdown_2024-2025.xlsx'
        if not drawdown_file.exists():
            continue


        for etf, ticker_full in etf_list:
            try:
                # Check if sheet exists first
                xl_file = pd.ExcelFile(drawdown_file)
                if etf not in xl_file.sheet_names:
                    continue  # Skip this ETF if no sheet exists (insufficient data)

                stock_drawdowns = pd.read_excel(drawdown_file, sheet_name=etf)
                stock_dd_filtered = stock_drawdowns[stock_drawdowns['rank'] != 'Current']

                holdings = load_ark_holdings(etf)
                stock_data = holdings[holdings['Ticker'] == ticker_full].copy()

                if len(stock_data) < 30:
                    continue

                bloomberg_name = stock_data['Bloomberg Name'].iloc[0]
                gics = ark_industry.get(bloomberg_name)
                if gics is None:
                    continue

                # Filter stock_data to analysis period for visualization
                stock_data = stock_data[(stock_data['Date'] >= start_date) & (stock_data['Date'] <= end_date)].copy()

                if len(stock_data) < 30:
                    continue

                # Try exact match first, then try prefix match (for truncated GICS names)
                if gics in peer_prices['GICS'].values:
                    gics_key = gics
                else:
                    # Find matching GICS by prefix (handle Excel 30-char truncation)
                    matching = peer_prices[peer_prices['GICS'].str.startswith(gics[:25])]['GICS'].unique()
                    gics_key = matching[0] if len(matching) > 0 else gics

                peer_data = peer_prices[peer_prices['GICS'] == gics_key].copy()
                peer_data = peer_data[(peer_data['Date'] >= start_date) & (peer_data['Date'] <= end_date)]

                if peer_data.empty:
                    print(f"  WARNING: No peer group data for {ticker_clean} (GICS: {gics})")
                    continue

                peer_data = peer_data.sort_values('Date').set_index('Date')

                peer_drawdown_file = project_root / 'output' / 'R3000_peer_groups_drawdown_2024-2025.xlsx'
                if not peer_drawdown_file.exists():
                    continue

                # Try to find matching sheet name (handle GICS name variations)
                # Use the matched gics_key to find Excel sheet names
                sheet_name = gics_key.replace('/', '_').replace('\\', '_').replace(':', '_')

                # Try exact match first, then try with trimmed spaces
                try:
                    peer_drawdowns = pd.read_excel(peer_drawdown_file, sheet_name=sheet_name)
                except ValueError:
                    # Sheet not found with exact name, try to find best match
                    xl_file = pd.ExcelFile(peer_drawdown_file)
                    available_sheets = xl_file.sheet_names

                    # Try matching by prefix (first 25 characters to handle truncation differences)
                    prefix = sheet_name[:25]
                    matching_sheet = None
                    for avail_sheet in available_sheets:
                        if avail_sheet.startswith(prefix):
                            matching_sheet = avail_sheet
                            break

                    if matching_sheet is None:
                        continue

                    peer_drawdowns = pd.read_excel(peer_drawdown_file, sheet_name=matching_sheet)

                peer_dd_filtered = peer_drawdowns[peer_drawdowns['rank'] != 'Current']

                # Check if we have valid data to plot
                if peer_data.empty:
                    print(f"  WARNING: Empty peer data for {ticker_clean} (GICS: {gics})")
                    continue

                # Create dual plot
                fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 12), sharex=True)

                colors = plt.cm.RdYlGn(np.linspace(0.2, 0.8, 10))

                # Top: Stock
                stock_data_sorted = stock_data.sort_values('Date')
                stock_data_sorted['date_diff'] = stock_data_sorted['Date'].diff().dt.days

                segments = []
                current_segment = []

                for idx, row in stock_data_sorted.iterrows():
                    if len(current_segment) == 0:
                        current_segment.append(row)
                    elif row['date_diff'] <= 5 or pd.isna(row['date_diff']):
                        current_segment.append(row)
                    else:
                        if current_segment:
                            segments.append(pd.DataFrame(current_segment))
                        current_segment = [row]

                if current_segment:
                    segments.append(pd.DataFrame(current_segment))

                for segment_df in segments:
                    ax1.plot(segment_df['Date'], segment_df['Price'], color='black', linewidth=1.5, zorder=3)

                for plot_idx, (idx, row) in enumerate(stock_dd_filtered.iterrows()):
                    if plot_idx >= 10:
                        break
                    peak_date = pd.to_datetime(row['peak_date'])
                    trough_date = pd.to_datetime(row['trough_date'])
                    ax1.axvspan(peak_date, trough_date, alpha=0.3, color=colors[plot_idx],
                                label=f"DD {row['rank']}: {row['depth_pct']:.1f}%", zorder=1)

                ax1.set_title(f'{bloomberg_name} in {etf} - Price & Top 10 Drawdowns (Apr 2024 - Oct 2025)',
                              fontsize=14, fontweight='bold')
                ax1.set_ylabel('Stock Price ($)', fontsize=12)
                ax1.grid(True, alpha=0.3)
                ax1.legend(loc='upper left', ncol=2, fontsize=8, framealpha=0.9)
                ax1.set_xlim(start_date, end_date)

                # Bottom: Peer Group MV
                ax2.plot(peer_data.index, peer_data['Value'], color='darkblue', linewidth=1.5, zorder=3)

                for plot_idx, (idx, row) in enumerate(peer_dd_filtered.iterrows()):
                    if plot_idx >= 10:
                        break
                    peak_date = pd.to_datetime(row['peak_date'])
                    trough_date = pd.to_datetime(row['trough_date'])
                    ax2.axvspan(peak_date, trough_date, alpha=0.3, color=colors[plot_idx],
                                label=f"DD {row['rank']}: {row['depth_pct']:.1f}%", zorder=1)

                ax2.set_title(f'Peer Group: {gics} (Market Value)', fontsize=14, fontweight='bold')
                ax2.set_xlabel('Date', fontsize=12)
                ax2.set_ylabel('Peer Group Market Value', fontsize=12)
                ax2.yaxis.set_major_formatter(FuncFormatter(format_value))
                ax2.grid(True, alpha=0.3)
                ax2.legend(loc='upper left', ncol=2, fontsize=8, framealpha=0.9)
                ax2.set_xlim(start_date, end_date)

                plt.xticks(rotation=45)
                plt.tight_layout()

                output_file = chart_dir / f'{ticker_clean}_{etf}_mv_drawdown_2024-2025.png'
                plt.savefig(output_file, dpi=300, bbox_inches='tight')
                plt.close()


            except Exception as e:
                continue


def visualize_ark_stocks_weighted():
    """Visualize ARK stocks vs peer groups (Weighted Price)"""
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    output_dir = project_root / 'output' / 'stock_drawdowns'
    chart_dir = project_root / 'output' / 'stock_charts_weighted'
    chart_dir.mkdir(parents=True, exist_ok=True)

    ark_industry = load_industry_info('ark')
    peer_prices = calculate_peer_group_prices_weighted()
    peer_prices = filter_valid_gics(peer_prices, 'GICS')

    etfs = ['ARKK', 'ARKQ', 'ARKW', 'ARKG', 'ARKF', 'ARKX']
    stock_etf_map = {}

    for etf in etfs:
        holdings = load_ark_holdings(etf)
        for ticker in holdings['Ticker'].unique():
            ticker_clean = ticker.split()[0] if isinstance(ticker, str) else ticker
            if ticker_clean not in stock_etf_map:
                stock_etf_map[ticker_clean] = []
            stock_etf_map[ticker_clean].append((etf, ticker))

    start_date = START_DATE
    end_date = END_DATE

    for ticker_clean, etf_list in stock_etf_map.items():
        drawdown_file = output_dir / f'{ticker_clean}_drawdown_2024-2025.xlsx'
        if not drawdown_file.exists():
            continue


        for etf, ticker_full in etf_list:
            try:
                # Check if sheet exists first
                xl_file = pd.ExcelFile(drawdown_file)
                if etf not in xl_file.sheet_names:
                    continue  # Skip this ETF if no sheet exists (insufficient data)

                stock_drawdowns = pd.read_excel(drawdown_file, sheet_name=etf)
                stock_dd_filtered = stock_drawdowns[stock_drawdowns['rank'] != 'Current']

                holdings = load_ark_holdings(etf)
                stock_data = holdings[holdings['Ticker'] == ticker_full].copy()

                if len(stock_data) < 30:
                    continue

                bloomberg_name = stock_data['Bloomberg Name'].iloc[0]
                gics = ark_industry.get(bloomberg_name)
                if gics is None:
                    continue

                # Filter stock_data to analysis period for visualization
                stock_data = stock_data[(stock_data['Date'] >= start_date) & (stock_data['Date'] <= end_date)].copy()

                if len(stock_data) < 30:
                    continue

                # Try exact match first, then try prefix match (for truncated GICS names)
                if gics in peer_prices['GICS'].values:
                    gics_key = gics
                else:
                    # Find matching GICS by prefix (handle Excel 30-char truncation)
                    matching = peer_prices[peer_prices['GICS'].str.startswith(gics[:25])]['GICS'].unique()
                    gics_key = matching[0] if len(matching) > 0 else gics

                peer_data = peer_prices[peer_prices['GICS'] == gics_key].copy()
                peer_data = peer_data[(peer_data['Date'] >= start_date) & (peer_data['Date'] <= end_date)]

                if peer_data.empty:
                    print(f"  WARNING: No peer group data for {ticker_clean} (GICS: {gics})")
                    continue

                peer_data = peer_data.sort_values('Date').set_index('Date')

                peer_drawdown_file = project_root / 'output' / 'R3000_peer_groups_drawdown_2024-2025.xlsx'
                if not peer_drawdown_file.exists():
                    continue

                # Try to find matching sheet name (handle GICS name variations)
                # Use the matched gics_key to find Excel sheet names
                sheet_name = gics_key.replace('/', '_').replace('\\', '_').replace(':', '_')

                # Try exact match first, then try with trimmed spaces
                try:
                    peer_drawdowns = pd.read_excel(peer_drawdown_file, sheet_name=sheet_name)
                except ValueError:
                    # Sheet not found with exact name, try to find best match
                    xl_file = pd.ExcelFile(peer_drawdown_file)
                    available_sheets = xl_file.sheet_names

                    # Try matching by prefix (first 25 characters to handle truncation differences)
                    prefix = sheet_name[:25]
                    matching_sheet = None
                    for avail_sheet in available_sheets:
                        if avail_sheet.startswith(prefix):
                            matching_sheet = avail_sheet
                            break

                    if matching_sheet is None:
                        continue

                    peer_drawdowns = pd.read_excel(peer_drawdown_file, sheet_name=matching_sheet)

                peer_dd_filtered = peer_drawdowns[peer_drawdowns['rank'] != 'Current']

                # Check if we have valid data to plot
                if peer_data.empty:
                    print(f"  WARNING: Empty peer data for {ticker_clean} (GICS: {gics})")
                    continue

                # Create dual plot
                fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 12), sharex=True)

                colors = plt.cm.RdYlGn(np.linspace(0.2, 0.8, 10))

                # Top: Stock
                stock_data_sorted = stock_data.sort_values('Date')
                stock_data_sorted['date_diff'] = stock_data_sorted['Date'].diff().dt.days

                segments = []
                current_segment = []

                for idx, row in stock_data_sorted.iterrows():
                    if len(current_segment) == 0:
                        current_segment.append(row)
                    elif row['date_diff'] <= 5 or pd.isna(row['date_diff']):
                        current_segment.append(row)
                    else:
                        if current_segment:
                            segments.append(pd.DataFrame(current_segment))
                        current_segment = [row]

                if current_segment:
                    segments.append(pd.DataFrame(current_segment))

                for segment_df in segments:
                    ax1.plot(segment_df['Date'], segment_df['Price'], color='black', linewidth=1.5, zorder=3)

                for plot_idx, (idx, row) in enumerate(stock_dd_filtered.iterrows()):
                    if plot_idx >= 10:
                        break
                    peak_date = pd.to_datetime(row['peak_date'])
                    trough_date = pd.to_datetime(row['trough_date'])
                    ax1.axvspan(peak_date, trough_date, alpha=0.3, color=colors[plot_idx],
                                label=f"DD {row['rank']}: {row['depth_pct']:.1f}%", zorder=1)

                ax1.set_title(f'{bloomberg_name} in {etf} - Price & Top 10 Drawdowns (Apr 2024 - Oct 2025)',
                              fontsize=14, fontweight='bold')
                ax1.set_ylabel('Stock Price ($)', fontsize=12)
                ax1.grid(True, alpha=0.3)
                ax1.legend(loc='upper left', ncol=2, fontsize=8, framealpha=0.9)
                ax1.set_xlim(start_date, end_date)

                # Bottom: Peer Group Weighted Price
                ax2.plot(peer_data.index, peer_data['Value'], color='darkgreen', linewidth=1.5, zorder=3)

                for plot_idx, (idx, row) in enumerate(peer_dd_filtered.iterrows()):
                    if plot_idx >= 10:
                        break
                    peak_date = pd.to_datetime(row['peak_date'])
                    trough_date = pd.to_datetime(row['trough_date'])
                    ax2.axvspan(peak_date, trough_date, alpha=0.3, color=colors[plot_idx],
                                label=f"DD {row['rank']}: {row['depth_pct']:.1f}%", zorder=1)

                ax2.set_title(f'Peer Group: {gics} (Weighted Price)', fontsize=14, fontweight='bold')
                ax2.set_xlabel('Date', fontsize=12)
                ax2.set_ylabel('Peer Group Weighted Price Index', fontsize=12)
                ax2.grid(True, alpha=0.3)
                ax2.legend(loc='upper left', ncol=2, fontsize=8, framealpha=0.9)
                ax2.set_xlim(start_date, end_date)

                plt.xticks(rotation=45)
                plt.tight_layout()

                output_file = chart_dir / f'{ticker_clean}_{etf}_weighted_drawdown_2024-2025.png'
                plt.savefig(output_file, dpi=300, bbox_inches='tight')
                plt.close()


            except Exception as e:
                continue


def visualize_ark_stocks():
    """Wrapper to call both stock visualization functions"""
    visualize_ark_stocks_mv()
    visualize_ark_stocks_weighted()


def visualize_stock_vs_peer_mv():
    """Visualize stock price vs peer group market value comparison"""
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    chart_dir = project_root / 'output' / 'stock_vs_peer_mv'
    chart_dir.mkdir(parents=True, exist_ok=True)

    ark_industry = load_industry_info('ark')
    peer_prices = calculate_peer_group_prices_mv()
    peer_prices = filter_valid_gics(peer_prices, 'GICS')

    etfs = ['ARKK', 'ARKQ', 'ARKW', 'ARKG', 'ARKF', 'ARKX']
    stock_etf_map = {}

    for etf in etfs:
        holdings = load_ark_holdings(etf)
        for ticker in holdings['Ticker'].unique():
            ticker_clean = ticker.split()[0] if isinstance(ticker, str) else ticker
            if ticker_clean not in stock_etf_map:
                stock_etf_map[ticker_clean] = []
            stock_etf_map[ticker_clean].append((etf, ticker))

    start_date = START_DATE
    end_date = END_DATE

    total_stocks = len(stock_etf_map)
    processed = 0
    print(f"  Generating {total_stocks} stock vs peer MV charts...")

    for ticker_clean, etf_list in stock_etf_map.items():
        processed += 1
        if processed % 10 == 0 or processed == total_stocks:
            print(f"  Progress: {processed}/{total_stocks} stocks")

        for etf, ticker_full in etf_list:
            try:
                holdings = load_ark_holdings(etf)
                stock_data = holdings[holdings['Ticker'] == ticker_full].copy()

                if len(stock_data) < 30:
                    continue

                bloomberg_name = stock_data['Bloomberg Name'].iloc[0]
                gics = ark_industry.get(bloomberg_name)
                if gics is None:
                    continue

                # Filter stock_data to analysis period
                stock_data = stock_data[(stock_data['Date'] >= start_date) & (stock_data['Date'] <= end_date)].copy()

                if len(stock_data) < 30:
                    continue

                # Get peer group data
                if gics in peer_prices['GICS'].values:
                    gics_key = gics
                else:
                    matching = peer_prices[peer_prices['GICS'].str.startswith(gics[:25])]['GICS'].unique()
                    gics_key = matching[0] if len(matching) > 0 else gics

                peer_data = peer_prices[peer_prices['GICS'] == gics_key].copy()
                peer_data = peer_data[(peer_data['Date'] >= start_date) & (peer_data['Date'] <= end_date)]

                if peer_data.empty:
                    continue

                peer_data = peer_data.sort_values('Date').set_index('Date')

                # Normalize both to start at 100
                stock_data_sorted = stock_data.sort_values('Date').set_index('Date')
                stock_normalized = (stock_data_sorted['Price'] / stock_data_sorted['Price'].iloc[0]) * 100
                peer_normalized = (peer_data['Value'] / peer_data['Value'].iloc[0]) * 100

                # Create comparison plot
                fig, ax = plt.subplots(figsize=(16, 8))

                # Plot stock
                ax.plot(stock_normalized.index, stock_normalized.values,
                       color='blue', linewidth=2, label=f'{ticker_clean} (Stock)', zorder=3)

                # Plot peer group
                ax.plot(peer_normalized.index, peer_normalized.values,
                       color='orange', linewidth=2, label=f'{gics_key} (Peer Group)', alpha=0.7, zorder=2)

                ax.set_title(f'{bloomberg_name} vs Peer Group MV (Normalized to 100)',
                            fontsize=16, fontweight='bold')
                ax.set_xlabel('Date', fontsize=12)
                ax.set_ylabel('Normalized Value (Base=100)', fontsize=12)
                ax.grid(True, alpha=0.3)
                ax.legend(loc='best', fontsize=10, framealpha=0.9)
                ax.set_xlim(start_date, end_date)

                # Add horizontal line at 100
                ax.axhline(y=100, color='black', linestyle='--', linewidth=0.8, alpha=0.5)

                plt.xticks(rotation=45)
                plt.tight_layout()

                output_file = chart_dir / f'{ticker_clean}_{etf}_vs_peer_mv.png'
                plt.savefig(output_file, dpi=300, bbox_inches='tight')
                plt.close()

            except Exception as e:
                continue


def visualize_stock_vs_peer_weighted():
    """Visualize stock price vs peer group weighted price comparison"""
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    chart_dir = project_root / 'output' / 'stock_vs_peer_weighted'
    chart_dir.mkdir(parents=True, exist_ok=True)

    ark_industry = load_industry_info('ark')
    peer_prices = calculate_peer_group_prices_weighted()
    peer_prices = filter_valid_gics(peer_prices, 'GICS')

    etfs = ['ARKK', 'ARKQ', 'ARKW', 'ARKG', 'ARKF', 'ARKX']
    stock_etf_map = {}

    for etf in etfs:
        holdings = load_ark_holdings(etf)
        for ticker in holdings['Ticker'].unique():
            ticker_clean = ticker.split()[0] if isinstance(ticker, str) else ticker
            if ticker_clean not in stock_etf_map:
                stock_etf_map[ticker_clean] = []
            stock_etf_map[ticker_clean].append((etf, ticker))

    start_date = START_DATE
    end_date = END_DATE

    total_stocks = len(stock_etf_map)
    processed = 0
    print(f"  Generating {total_stocks} stock vs peer weighted charts...")

    for ticker_clean, etf_list in stock_etf_map.items():
        processed += 1
        if processed % 10 == 0 or processed == total_stocks:
            print(f"  Progress: {processed}/{total_stocks} stocks")

        for etf, ticker_full in etf_list:
            try:
                holdings = load_ark_holdings(etf)
                stock_data = holdings[holdings['Ticker'] == ticker_full].copy()

                if len(stock_data) < 30:
                    continue

                bloomberg_name = stock_data['Bloomberg Name'].iloc[0]
                gics = ark_industry.get(bloomberg_name)
                if gics is None:
                    continue

                # Filter stock_data to analysis period
                stock_data = stock_data[(stock_data['Date'] >= start_date) & (stock_data['Date'] <= end_date)].copy()

                if len(stock_data) < 30:
                    continue

                # Get peer group data
                if gics in peer_prices['GICS'].values:
                    gics_key = gics
                else:
                    matching = peer_prices[peer_prices['GICS'].str.startswith(gics[:25])]['GICS'].unique()
                    gics_key = matching[0] if len(matching) > 0 else gics

                peer_data = peer_prices[peer_prices['GICS'] == gics_key].copy()
                peer_data = peer_data[(peer_data['Date'] >= start_date) & (peer_data['Date'] <= end_date)]

                if peer_data.empty:
                    continue

                peer_data = peer_data.sort_values('Date').set_index('Date')

                # Normalize both to start at 100
                stock_data_sorted = stock_data.sort_values('Date').set_index('Date')
                stock_normalized = (stock_data_sorted['Price'] / stock_data_sorted['Price'].iloc[0]) * 100
                peer_normalized = (peer_data['Value'] / peer_data['Value'].iloc[0]) * 100

                # Create comparison plot
                fig, ax = plt.subplots(figsize=(16, 8))

                # Plot stock
                ax.plot(stock_normalized.index, stock_normalized.values,
                       color='blue', linewidth=2, label=f'{ticker_clean} (Stock)', zorder=3)

                # Plot peer group
                ax.plot(peer_normalized.index, peer_normalized.values,
                       color='orange', linewidth=2, label=f'{gics_key} (Peer Group)', alpha=0.7, zorder=2)

                ax.set_title(f'{bloomberg_name} vs Peer Group Weighted Price (Normalized to 100)',
                            fontsize=16, fontweight='bold')
                ax.set_xlabel('Date', fontsize=12)
                ax.set_ylabel('Normalized Price (Base=100)', fontsize=12)
                ax.grid(True, alpha=0.3)
                ax.legend(loc='best', fontsize=10, framealpha=0.9)
                ax.set_xlim(start_date, end_date)

                # Add horizontal line at 100
                ax.axhline(y=100, color='black', linestyle='--', linewidth=0.8, alpha=0.5)

                plt.xticks(rotation=45)
                plt.tight_layout()

                output_file = chart_dir / f'{ticker_clean}_{etf}_vs_peer_weighted.png'
                plt.savefig(output_file, dpi=300, bbox_inches='tight')
                plt.close()

            except Exception as e:
                continue


if __name__ == '__main__':
    visualize_ark_etf_drawdowns()
    visualize_index_drawdowns()
    visualize_peer_group_drawdowns()
    visualize_ark_stocks()
    visualize_stock_vs_peer_mv()
    visualize_stock_vs_peer_weighted()
