# Stock Market App

A terminal-based stock market viewer and trading interface that integrates with Alpaca's paper trading API. View real-time stock charts, monitor your portfolio, and execute trades directly from a clean terminal UI.

## Technology Stack

**Core Technologies:**
- **Python 3.7+** - Primary programming language
- **Curses** - Terminal UI framework for creating interactive, responsive interfaces
- **Pandas** - Data manipulation and analysis for stock market data
- **yFinance** - Yahoo Finance API wrapper for real-time and historical market data
- **Alpaca Trade API** - RESTful trading API for order execution and portfolio management

**Libraries & Tools:**
- **asciichartpy** - ASCII chart generation for terminal-based data visualization
- **python-dotenv** - Secure environment variable management for API credentials
- **Git** - Version control

## Features

- **Real-Time Stock Charts**: View ASCII charts for any stock symbol with 7 time periods (5d, 1mo, 3mo, 6mo, 1y, 2y, 5y) using arrow keys
- **Live Portfolio Tracking**: Monitor your portfolio equity, cash balance, and buying power with automatic refresh
- **Holdings Display**: See all your positions with current prices and unrealized P&L (color-coded green/red)
- **Paper Trading**: Execute market orders (buy/sell) through Alpaca's paper trading API
- **Auto-Refresh**: Stock prices and portfolio data update automatically every 5 seconds
- **Interactive UI**: Switch between different stocks with 's' key, navigate time periods with LEFT/RIGHT arrows, and place trades all from the keyboard
- **Fixed Layout**: Consistent window positioning for a stable 103x30 terminal display
- **Error Handling**: Robust exception handling for network issues, invalid symbols, and API errors

## Technical Implementation

### Architecture
- **Modular Design**: Separated concerns across multiple modules:
  - `terminal_ui.py` - Main UI logic and event loop using curses
  - `data.py` - Market data fetching and processing
  - `plotting.py` - Chart generation and data visualization
  - `orders.py` - Trade execution and order management
  - `account.py` - Portfolio and position tracking
  - `config.py` - API configuration and authentication
  - `util.py` - Utility functions

### Key Technical Features
- **Non-blocking UI**: Responsive keyboard input without blocking price updates every 5 seconds
- **Fixed Layout Design**: Optimized curses layout for consistent display across terminals
- **Color-Coded Indicators**: Uses curses color pairs for visual feedback (gains=green, losses=red)
- **RESTful API Integration**: Seamless integration with Alpaca's trading platform via REST API
- **Linear Chart Interpolation**: Even data sampling for short-period charts with smooth price interpolation
- **Real-Time Position Synchronization**: Immediate portfolio updates after trade execution

### Data Flow
1. User input → Event handler → API request
2. yFinance API → Historical data → Pandas DataFrame → Chart generation
3. Alpaca API → Order execution → Position update → UI refresh
4. Background thread → Price polling → Live updates → Stats panel refresh

## How to Run

1. **Set up your environment**:
   - Create a `.env` file in the project root with your Alpaca API credentials:
     ```
     api_key=your_api_key_here
     api_secret=your_api_secret_here
     base_url=https://paper-api.alpaca.markets
     ```

2. **Install dependencies**:
   ```bash
   pip install yfinance pandas asciichartpy alpaca-trade-api python-dotenv
   ```

3. **Run the application**:
   - Windows: Double-click `start.bat` or run `python terminal_ui.py`
   - Mac/Linux: Run `python terminal_ui.py`

## Usage

Once the application is running:

- **`s`** - Change stock symbol (e.g., "AAPL" or "TSLA")
- **`LEFT/RIGHT arrows`** - Navigate between time periods (5d, 1mo, 3mo, 6mo, 1y, 2y, 5y)
- **`t`** - Place a trade (format: "buy AAPL 1" or "sell MSFT 0.5")
- **`q`** - Quit the application

The main screen displays:
- Stock chart with historical price data
- Current price, change percentage, high/low, and volume
- Your portfolio summary (equity, cash, buying power)
- Your holdings with real-time P&L

## Requirements

- Python 3.7+
- Active Alpaca paper trading account (free at alpaca.markets)
- Terminal with curses support (native on Mac/Linux, Windows Terminal recommended on Windows)
