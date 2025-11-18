import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

def get_drawdown_contributions(etf_name, drawdown_idx):
    """Calculate contributions for a specific drawdown period"""
    base_dir = Path(__file__).parent.parent

    # Read drawdown dates
    drawdown_file = base_dir / 'output' / f'{etf_name}_drawdown_2024-2025.xlsx'
    all_drawdowns = pd.read_excel(drawdown_file, sheet_name='Drawdowns')

    # Skip Current_Drawdown row
    drawdowns = all_drawdowns[all_drawdowns['rank'] != 'Current'].reset_index(drop=True)

    if drawdown_idx >= len(drawdowns):
        return None, None, None

    dd = drawdowns.iloc[drawdown_idx]
    peak_date = pd.to_datetime(dd['peak_date'])
    trough_date = pd.to_datetime(dd['trough_date'])

    # Read stock adj pnl data
    metrics_file = base_dir / 'output' / f'{etf_name}_daily_metrics.xlsx'
    df = pd.read_excel(metrics_file, sheet_name='Stock_Metrics',
                      usecols=['Date', 'Ticker', 'stock adj pnl'])
    df['Date'] = pd.to_datetime(df['Date'])

    # Filter for drawdown period
    mask = (df['Date'] >= peak_date) & (df['Date'] <= trough_date)
    period_data = df[mask]

    # Sum by ticker
    contributions = period_data.groupby('Ticker')['stock adj pnl'].sum()
    # Keep all stocks, including those with zero contribution
    contributions = contributions.sort_values()


    return contributions, peak_date, trough_date

def create_bar_chart(contributions, title, save_path, max_stocks=None):
    """Create a simple bar chart for contributions"""
    if len(contributions) == 0:
        return

    # No limiting - show all stocks
    # If there are too many stocks, make the figure wider
    if len(contributions) > 50:
        fig_width = 20
    elif len(contributions) > 30:
        fig_width = 16
    else:
        fig_width = 14

    fig, ax = plt.subplots(figsize=(fig_width, 7))

    # Create bar chart
    x = np.arange(len(contributions))
    colors = ['red' if v < 0 else 'green' for v in contributions.values]

    bars = ax.bar(x, contributions.values, color=colors, alpha=0.7, edgecolor='black', linewidth=0.5)

    # Set labels
    ax.set_xticks(x)
    ax.set_xticklabels(contributions.index, rotation=45, ha='right', fontsize=8)

    # Format
    ax.axhline(y=0, color='black', linewidth=0.8)
    ax.set_ylabel('Sum of stock adj pnl')
    ax.set_title(title)
    ax.grid(True, alpha=0.3, axis='y')

    # Format y-axis
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:,.0f}'))

    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()


def main():
    etfs = ['ARKK', 'ARKQ', 'ARKW', 'ARKG', 'ARKF', 'ARKX']
    base_dir = Path(__file__).parent.parent

    for etf_name in etfs:
        output_dir = base_dir / 'output' / 'contribution_charts' / etf_name
        output_dir.mkdir(parents=True, exist_ok=True)


        all_contributions = pd.Series(dtype=float)

        # Process each of 10 drawdowns
        for idx in range(10):
            contributions, peak_date, trough_date = get_drawdown_contributions(etf_name, idx)

            if contributions is not None:

                # Create individual drawdown chart
                title = f'{etf_name} Drawdown {idx+1} ({peak_date.strftime("%Y-%m-%d")} to {trough_date.strftime("%Y-%m-%d")})'
                save_path = output_dir / f'{etf_name}_drawdown_{idx+1}.png'
                create_bar_chart(contributions, title, save_path)

                # Add to total contributions
                all_contributions = all_contributions.add(contributions, fill_value=0)

        # Create total chart (sum of all 10 drawdowns)
        if len(all_contributions) > 0:
            all_contributions = all_contributions[all_contributions != 0].sort_values()
            title = f'{etf_name} - Total Contributions (Sum of All 10 Drawdowns)'
            save_path = output_dir / f'{etf_name}_total.png'
            create_bar_chart(all_contributions, title, save_path)


if __name__ == '__main__':
    main()