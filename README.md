# ARK ETF Drawdown Analysis

Analyze drawdowns and stock contributions for ARK ETFs

## Features
- Calculate top 10 drawdowns for 2025
- Analyze stock contributions to each drawdown
- Visualize price movements with drawdown periods

## Methodology

### Drawdown Calculation
1. **Identify Peaks and Troughs**: Find local maxima (peaks) and subsequent minima (troughs) in ETF price
2. **Calculate Drawdown Depth**: `Drawdown = (Trough_Price - Peak_Price) / Peak_Price × 100%`
3. **Non-overlapping Periods**: After finding the largest drawdown, split timeline and recursively find next largest in remaining periods
4. **Ranking**: Sort drawdowns by depth (most negative first)

### Stock Contribution Analysis
1. **Market Value Change**: For each stock, calculate `Stock_MV_change = Stock_MV_trough - Stock_MV_peak`
2. **ETF Change**: Calculate `ETF_MV_change = ETF_MV_trough - ETF_MV_peak`
3. **Contribution Percentage**: `Contribution = Stock_MV_change / ETF_MV_change × 100%`
4. **Interpretation**: Shows what percentage of ETF's total decline is attributable to each stock
5. **Negative Contributors**: Identify stocks with positive contributions (helped ETF fall) still in current holdings

### Portfolio Metrics
- **Portfolio Return**: `(Last_Price - First_Price) / First_Price × 100%`
- **RoMaD**: `Portfolio_Return / |Maximum_Drawdown|` (Risk-adjusted return metric)

## Usage
```bash
cd code
python fetch_prices.py          # Fetch price data
python calculate_drawdown.py    # Calculate drawdowns
python calculate_contributors.py # Analyze stock contributions
python visualize_drawdowns.py   # Generate charts
```

## Input
- `{ETF}_Transformed_Data.xlsx` - ARK holdings data

## Output
- `{ETF}_drawdown_2025.xlsx` - Drawdown analysis
- `{ETF}_contributors.xlsx` - Stock contributions
- `{ETF}_drawdown_visualization_2025.png` - Visualization charts

## Requirements
```bash
pip install pandas numpy matplotlib openpyxl yfinance
```