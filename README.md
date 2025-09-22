# ARK ETF Drawdown Analysis

Analyze drawdowns and stock contributions for ARK ETFs

## Features
- Calculate top 10 drawdowns for 2025
- Analyze stock contributions to each drawdown
- Visualize price movements with drawdown periods

## Methodology

### Drawdown Calculation
ETF
day1 etf return = (day1 ETF price - day0 ETF price)/day0 ETF price
day1 ETF MV = sum of every stock's (day1 stock position * day1 stock price)
day1 ETF inflows/outflows = sum of every stock's stock inflows/outflows
day1 ETF dollar pnl = day0 ETF MV * day1 etf return
day1 ETF adj pnl = day1 ETF dollar pnl - day1 ETF inflows/outflows


Holdings
day1 stock return = (day1 stock price - day0 stock price)/day0 stock price
day1 stock MV = day1 stock price * day1 stock position


Ongoing holding(Day0 > 0 & Day1 > 0)
day1 stock dollar pnl = day1 stock MV - day0 stock MV
day1 stock inflows/outflows = (day1 stock position - day0 stock position) * (day1 stock price + day0 stock price)/2
day1 stock adj pnl = day1 stock dollar pnl - day1 stock inflows/outflows

Entry position(Day0 = 0, Day1 > 0)
day0 stock dollar pnl = 0
day1 stock dollar pnl = day1 stock MV - day0 stock MV
day1 stock inflows = day1 stock position * day1 stock price
day1 stock adj pnl = day1 stock dollar pnl - day1 stock inflows/outflows

Exit position(Day0 > 0, Day1 = 0)
day1 stock MV = 0
day1 stock outflows = -day0 stock position * day0 stock price
day1 stock dollar pnl = day1 stock outflows
day1 stock adj pnl = 0

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