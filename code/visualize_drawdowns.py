import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path
import numpy as np
from datetime import datetime

def visualize_etf_drawdowns(etf_name):
    """Visualize ETF price with top 10 drawdown periods highlighted"""
    
    # Set up paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    output_dir = project_root / 'output'
    
    # Read price data
    price_file = output_dir / f'{etf_name}_prices.csv'
    if not price_file.exists():
        print(f"Price file not found: {price_file}")
        return
    
    df_prices = pd.read_csv(price_file)
    df_prices['Date'] = pd.to_datetime(df_prices['Date'])
    df_prices.set_index('Date', inplace=True)
    
    # Filter for 2025 data
    df_2025 = df_prices[df_prices.index.year == 2025].copy()
    if df_2025.empty:
        print(f"No 2025 data for {etf_name}")
        return
    
    # Read drawdown data
    drawdown_file = output_dir / f'{etf_name}_drawdown_2025.xlsx'
    if not drawdown_file.exists():
        print(f"Drawdown file not found: {drawdown_file}")
        return
    
    top_drawdowns = pd.read_excel(drawdown_file, sheet_name='Top_10_Drawdowns')
    
    # Create figure
    fig, ax = plt.subplots(figsize=(16, 8))
    
    # Plot the price line
    ax.plot(df_2025.index, df_2025['Close'], color='black', linewidth=1.5, zorder=3)
    
    # Color map for drawdowns (gradient from red for worst to green for least)
    colors = plt.cm.RdYlGn(np.linspace(0.2, 0.8, 10))
    
    # Add colored backgrounds for each drawdown period
    for idx, row in top_drawdowns.iterrows():
        if idx >= 10:  # Only show top 10
            break
            
        peak_date = pd.to_datetime(row['peak_date'])
        trough_date = pd.to_datetime(row['trough_date'])
        
        # Add vertical span for drawdown period
        ax.axvspan(peak_date, trough_date, 
                   alpha=0.3, 
                   color=colors[idx],
                   label=f"Drawdown {row['rank']}: {row['depth_pct']:.1f}%",
                   zorder=1)
    
    # Format the plot
    ax.set_title(f'{etf_name} Price & Top 10 Drawdowns - 2025', fontsize=16, fontweight='bold')
    ax.set_xlabel('Date', fontsize=12)
    ax.set_ylabel('Price ($)', fontsize=12)
    ax.grid(True, alpha=0.3)
    
    # Rotate x-axis labels
    plt.xticks(rotation=45)
    
    # Add simple legend
    ax.legend(loc='upper left', ncol=2, fontsize=9, framealpha=0.9)
    
    # Adjust layout
    plt.tight_layout()
    
    # Save the figure
    output_file = output_dir / f'{etf_name}_drawdown_visualization_2025.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Saved visualization to {output_file}")
    
    # Close the plot to free memory
    plt.close()

def main():
    """Process all ETFs"""
    etfs = ['ARKK', 'ARKQ', 'ARKW', 'ARKG', 'ARKF', 'ARKX']
    
    for etf in etfs:
        print(f"\nVisualizing {etf}...")
        try:
            visualize_etf_drawdowns(etf)
        except Exception as e:
            print(f"Error processing {etf}: {e}")

if __name__ == "__main__":
    main()