# 📈 Comprehensive Stock Backtester

A professional-grade backtesting platform for evaluating multiple technical trading strategies against historical stock data. Built with Python and Streamlit, this application allows traders and analysts to compare strategy performance metrics and visualize trade signals.

**[➡️ View the Live Demo Here](https://comprehensive-stock-backtester.streamlit.app/)**

---

## ✨ Features

- **Multi-Strategy Analysis**: Test 25+ technical trading strategies simultaneously on any stock.
- **Performance Metrics**: Compare Net Profit, Sharpe Ratio, Max Drawdown, and total trades.
- **Interactive Visualizations**:
  - Comparative equity curves for top-performing strategies.
  - Buy/sell signals overlaid directly on the price chart for clear analysis.
  - Detailed trade logs for in-depth strategy validation.
- **User-Friendly Interface**: Simple configuration with immediate visual feedback.
- **Event-Driven Architecture**: Built on a professional-grade, event-driven backtesting engine.
- **Data Integration**: Seamlessly retrieves historical market data from Yahoo Finance.

---

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- pip (Python package manager)

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/Saraid10/stock-backtester.git
    cd stock-backtester
    ```

2.  **Create and activate a virtual environment (recommended):**
    ```bash
    # For macOS/Linux
    python3 -m venv venv
    source venv/bin/activate

    # For Windows
    python -m venv venv
    venv\Scripts\activate
    ```

3.  **Install the required packages:**
    ```bash
    pip install -r requirements.txt
    ```

### Running the Application Locally

Launch the application with the following command:
```bash
streamlit run app.py
```

The application will open in your default web browser, typically at `http://localhost:8501`.

---

## 📊 How to Use the Backtester

1.  **Configure Your Backtest** in the sidebar:
    -   Enter a stock ticker symbol (e.g., `AAPL`, `MSFT`, `GOOGL`).
    -   Select the desired start and end dates for the backtest period.
    -   Set your initial capital amount.
2.  **Run the Analysis**: Click the **"Run All Strategies"** button.
3.  **Analyze the Results**:
    -   **Performance Ranking**: Review the main table to see which strategies performed best based on key metrics.
    -   **Equity Curves**: Compare the portfolio growth of the top 5 strategies in the "Comparative Equity Curves" chart.
    -   **Detailed Analysis**: Expand the details for any of the top performers to see:
        -   **Trade Signals Chart**: A price chart showing exactly where the strategy generated buy (▲) and sell (▼) signals.
        -   **Equity Curve Chart**: An individual performance graph for that specific strategy.
        -   **Trade Log**: A complete table of all trades executed by the strategy.

---

## 🔧 Backtesting Engine Architecture

This application implements a professional event-driven backtesting framework to ensure that there is no lookahead bias and that the simulation is as realistic as possible.

-   **Data Handler**: Manages historical price data retrieval and provides market data bars to the system.
-   **Strategy**: Generates trading signals based on technical indicators and market conditions.
-   **Portfolio**: Tracks positions, cash, and total equity. It handles risk management and order sizing.
-   **Execution Handler**: Simulates order execution and the associated costs (slippage and commission can be added).
-   **Event Queue**: A central message bus that coordinates the flow of `MARKET`, `SIGNAL`, `ORDER`, and `FILL` events between components.

---

## 📋 Implemented Strategies

The backtester includes the following 25 pre-built technical trading strategies:

| Strategy | Parameters | Description |
|:---|:---|:---|
| **Buy and Hold** | - | A simple benchmark strategy of buying and holding the asset. |
| **SMA Crossover** | `50/200` | Golden cross/death cross strategy using Simple Moving Averages. |
| **DEMA Crossover** | `50/200` | Crossover strategy using faster Double Exponential Moving Averages. |
| **TEMA Crossover** | `50/200` | Crossover strategy using even more responsive Triple Exponential Moving Averages. |
| **RSI** | `14/30/70` | Relative Strength Index momentum strategy with overbought/oversold levels. |
| **Bollinger Bands** | `20/2` | A mean-reversion strategy based on price volatility bands. |
| **MACD** | `12/26/9` | Moving Average Convergence Divergence trend-following momentum strategy. |
| **Parabolic SAR**| `0.02/0.2`| A trend-following (stop and reverse) indicator. |
| **Stochastic Osc**| `14/20/80`| A momentum indicator comparing a closing price to a range of its prices. |
| **OBV Crossover** | `20` | On-Balance Volume strategy to measure buying and selling pressure. |
| **Ichimoku Cloud**| `9/26` | A comprehensive indicator that defines support/resistance and momentum. |
| **ATR Channel** | `20/14/2` | A volatility channel breakout strategy using Average True Range. |
| **Rate of Change**| `12/20` | A momentum oscillator measuring the percentage change in price. |
| **Awesome Osc** | `5/34` | A momentum indicator reflecting the explosiveness of the market. |
| **Keltner Channel**| `20/10/2`| A volatility-based envelope strategy. |
| **VWAP Crossover**| `20` | A strategy based on the Volume-Weighted Average Price. |
| **Donchian Channel**|`20`| A breakout strategy using highest high and lowest low over a period. |
| **CCI** |`20/-100/100`| Commodity Channel Index strategy to identify cyclical trends. |
| **MA Ribbon** |`5/10/20`| A trend-following strategy using multiple moving averages. |
| **Chaikin Money Flow**| `20` | A volume-based oscillator to measure market buying/selling pressure. |
| **Williams %R** |`14/-80/-20`| A momentum indicator that is the inverse of the Stochastic Oscillator. |
| **Aroon Indicator**| `25` | A trend indicator used to identify trend direction and strength. |
| **Money Flow Index**|`14/20/80`| A volume-weighted RSI that measures buying and selling pressure. |
| **TRIX** | `15/9` | A triple-smoothed exponential moving average oscillator. |
| **Vortex Indicator**| `14` | A trend-following indicator to spot the start of a new trend. |

---

## 📁 Project Structure

```
stock-backtester/
│
├── app.py                      # Main Streamlit application UI and logic
│
├── backtest/                   # Core backtesting engine components
│   └── (All engine files...)
│
├── strategies/                 # All trading strategy implementations
│   └── (All strategy files...)
│
├── .gitignore                  # Specifies files for Git to ignore
├── requirements.txt            # List of Python package dependencies
├── LICENSE                     # Project's MIT License
└── README.md                   # This documentation file
```

---

## 📝 License

This project is licensed under the MIT License. Copyright (c) 2025 Saraid10. See the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Please feel free to check the issues page if you want to contribute.

## 🔗 Acknowledgments

-   Built with **[Streamlit](https://streamlit.io/)**.
-   Market data provided by **[Yahoo Finance](https://finance.yahoo.com/)**.
-   Inspired by the work of Michael Halls-Moore on event-driven backtesting.

---

<p align="center">Developed by <a href="https://github.com/Saraid10">Saraid10</a></p>
