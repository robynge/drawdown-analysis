"""
Main entry point for all drawdown analysis

Execution Order:
1. Fetch Market Data
2. ARK ETF Drawdown Analysis
3. Index Drawdown Analysis (Russell 3000)
4. Peer Group Drawdown Analysis
5. Individual Stock Drawdown Analysis
6. Stock vs Peer Group (Market Value)
7. Stock vs Peer Group (Weighted Price)
"""

import argparse
import pandas as pd

import fetch_prices
import calculate_all
import visualize_all


# ============================================================================
# DATE CONFIGURATION
# ============================================================================
# Set analysis start and end dates here

START_DATE = '2024-04-01'
END_DATE = '2025-11-10'


def configure_analysis_dates():
    """Configure global analysis date range"""
    start = pd.to_datetime(START_DATE)
    end = pd.to_datetime(END_DATE)

    print(f"\n{START_DATE} to {END_DATE}")

    # Set global dates
    calculate_all.START_DATE = start
    calculate_all.END_DATE = end

    return start, end


# ============================================================================
# MAIN PROCESSING FUNCTIONS
# ============================================================================

def step_1_fetch_market_data():
    """Step 1: Fetch Market Data"""
    print("\n[1/7] Fetching prices...")
    try:
        if hasattr(fetch_prices, 'main'):
            fetch_prices.main()
    except Exception as e:
        print(f"Error: {e}")


def step_2_process_ark_etf_drawdowns():
    """Step 2: Process ARK ETF Drawdown Analysis"""
    print("\n[2/7] ARK ETF drawdowns...")
    try:
        calculate_all.calculate_ark_etf_drawdowns()
        visualize_all.visualize_ark_etf_drawdowns()
    except Exception as e:
        print(f"Error: {e}")


def step_3_process_index_drawdowns():
    """Step 3: Process Index Drawdown Analysis"""
    print("\n[3/7] Index drawdowns...")
    try:
        calculate_all.calculate_index_drawdowns()
        visualize_all.visualize_index_drawdowns()
    except Exception as e:
        print(f"Error: {e}")


def step_4_process_peer_group_drawdowns():
    """Step 4: Process Peer Group Drawdown Analysis"""
    print("\n[4/7] Peer group drawdowns...")
    try:
        calculate_all.calculate_peer_group_drawdowns()
        visualize_all.visualize_peer_group_drawdowns()
    except Exception as e:
        print(f"Error: {e}")


def step_5_process_individual_stock_drawdowns():
    """Step 5: Process Individual Stock Drawdown Analysis"""
    print("\n[5/7] Stock drawdowns...")
    try:
        calculate_all.calculate_ark_stock_drawdowns()
        visualize_all.visualize_ark_stocks()
    except Exception as e:
        print(f"Error: {e}")


def step_6_visualize_stock_vs_peer():
    """Step 6: Visualize Stock vs Peer Group Comparison (MV & Weighted)"""
    print("\n[6/7] Stock vs peer (MV)...")
    try:
        visualize_all.visualize_stock_vs_peer_mv()
    except Exception as e:
        print(f"Error: {e}")


def step_7_visualize_stock_vs_peer_weighted():
    """Step 7: Visualize Stock vs Peer Group Weighted Price Comparison"""
    print("\n[7/7] Stock vs peer (weighted)...")
    try:
        visualize_all.visualize_stock_vs_peer_weighted()
    except Exception as e:
        print(f"Error: {e}")


# ============================================================================
# RUN MODES
# ============================================================================

def run_full_pipeline():
    """Full Pipeline: Execute all 7 steps"""
    configure_analysis_dates()

    step_1_fetch_market_data()
    step_2_process_ark_etf_drawdowns()
    step_3_process_index_drawdowns()
    step_4_process_peer_group_drawdowns()
    step_5_process_individual_stock_drawdowns()
    step_6_visualize_stock_vs_peer()
    step_7_visualize_stock_vs_peer_weighted()

    print("\nDone. Check ../output/")


def run_calculate_only():
    """Calculate Only Mode: No charts"""
    configure_analysis_dates()

    print("\n[2/5] ARK ETF...")
    calculate_all.calculate_ark_etf_drawdowns()

    print("\n[3/5] Index...")
    calculate_all.calculate_index_drawdowns()

    print("\n[4/5] Peer groups...")
    calculate_all.calculate_peer_group_drawdowns()

    print("\n[5/5] Stocks...")
    calculate_all.calculate_ark_stock_drawdowns()

    print("\nDone.")


def run_visualize_only():
    """Visualize Only Mode: Generate charts from existing data"""
    configure_analysis_dates()

    print("\n[2/7] ARK ETF charts...")
    visualize_all.visualize_ark_etf_drawdowns()

    print("\n[3/7] Index charts...")
    visualize_all.visualize_index_drawdowns()

    print("\n[4/7] Peer group charts...")
    visualize_all.visualize_peer_group_drawdowns()

    print("\n[5/7] Stock charts...")
    visualize_all.visualize_ark_stocks()

    print("\n[6/7] Stock vs peer (MV)...")
    visualize_all.visualize_stock_vs_peer_mv()

    print("\n[7/7] Stock vs peer (weighted)...")
    visualize_all.visualize_stock_vs_peer_weighted()

    print("\nDone.")


# ============================================================================
# COMMAND LINE ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='ARK ETF Drawdown Analysis Pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                    # Run full pipeline
  python main.py --calculate-only   # Only calculate, no charts
  python main.py --visualize-only   # Only generate charts from existing data
        """
    )

    parser.add_argument('--calculate-only', action='store_true',
                        help='Only calculate drawdowns (no visualization)')
    parser.add_argument('--visualize-only', action='store_true',
                        help='Only generate visualizations (requires existing data)')

    args = parser.parse_args()

    # Execute corresponding mode
    if args.calculate_only:
        run_calculate_only()
    elif args.visualize_only:
        run_visualize_only()
    else:
        run_full_pipeline()
