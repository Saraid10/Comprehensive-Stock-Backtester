import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import yfinance as yf
import datetime
from datetime import datetime, timedelta
import queue
import os
import logging
import traceback
from PIL import Image
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# Import local modules
from backtest.backtest import Backtest
from backtest.data import HistoricCSVDataHandler
from backtest.portfolio import Portfolio
from backtest.execution import SimulatedExecutionHandler
from strategies.buy_and_hold import BuyAndHoldStrategy
from strategies.moving_average_crossover import MovingAverageCrossover
from strategies.bollinger_bands import BollingerBandsStrategy
from strategies.rsi import RSIStrategy
from strategies.macd import MACDStrategy
from strategies.parabolic_sar import ParabolicSARStrategy
from strategies.ichimoku import IchimokuStrategy
from strategies.williams_r import WilliamsRStrategy
from strategies.stochastic import StochasticStrategy
from strategies.adx import ADXStrategy
from strategies.aroon import AroonStrategy
from strategies.cci import CCIStrategy
from strategies.fibonacci_retracement import FibonacciRetracementStrategy
from strategies.turtle_trading import TurtleTradingStrategy
from strategies.breakout import BreakoutStrategy
from strategies.mean_reversion import MeanReversionStrategy
from strategies.momentum import MomentumStrategy
from strategies.obv import OBVStrategy
from strategies.psar_macd import PSARMACDStrategy
from strategies.sma_rsi import SMA_RSIStrategy
from strategies.supertrend import SupertrendStrategy
from strategies.trix import TRIXStrategy
from strategies.triple_ma import TripleMovingAverageStrategy
from strategies.vwap import VWAPStrategy
from strategies.money_flow_index import MoneyFlowIndexStrategy
from strategies.vortex import VortexIndicatorStrategy

# Set up page configuration
st.set_page_config(
    page_title="Comprehensive Stock Backtester",
    page_icon="📈",
    layout="wide"
)

# Initialize session state variables
if 'strategies_results' not in st.session_state:
    st.session_state.strategies_results = {}
if 'selected_strategy' not in st.session_state:
    st.session_state.selected_strategy = None
if 'show_details' not in st.session_state:
    st.session_state.show_details = False

# App title and description
st.image("assets/logo.png", width=60)
st.title("Comprehensive Stock Backtester")
st.write("This tool runs multiple trading strategies against historical stock data to identify the top performers. Configure your backtest on the left and click 'Run All Strategies' to begin.")

# Sidebar configuration
st.sidebar.title("Backtest Configuration")

# Ticker input
ticker = st.sidebar.text_input("Stock Symbol", "AAPL", help="Enter the ticker symbol of the stock you want to backtest")

# Date range selection
today = datetime.today()
default_end_date = today - timedelta(days=1)
default_start_date = default_end_date - timedelta(days=365*2)  # 2 years of data by default

start_date = st.sidebar.date_input("Start Date", default_start_date, help="Select the start date for your backtest")
end_date = st.sidebar.date_input("End Date", default_end_date, help="Select the end date for your backtest")

# Initial capital input
initial_capital = st.sidebar.number_input("Initial Capital ($)", min_value=1000, value=100000, step=1000, help="Enter your starting investment amount")

# Position sizing settings
st.sidebar.header("Position Sizing")
position_size_pct = st.sidebar.slider("Position Size (% of Portfolio)", 1, 100, 5, 1, 
                                     help="What percentage of the portfolio to invest in each position")

# Display warning for aggressive position sizing
if position_size_pct > 20:
    st.sidebar.warning("⚠️ **High Risk Alert**: Position sizes above 20% reduce diversification and significantly increase risk. This approach is not recommended for most trading strategies.", icon="⚠️")
elif position_size_pct > 10:
    st.sidebar.info("ℹ️ Position sizes between 10-20% represent an aggressive approach with higher risk.", icon="ℹ️")

# Strategy selection - checkboxes for individual strategies
st.sidebar.header("Select Strategies")

# Create a dictionary of strategies with their parameters
strategies = {
    "Buy and Hold": {"class": BuyAndHoldStrategy, "params": {}, "selected": True},
    "SMA Crossover": {"class": MovingAverageCrossover, "params": {"short_window": st.sidebar.slider("SMA Short Window", 5, 50, 10, 1), "long_window": st.sidebar.slider("SMA Long Window", 20, 200, 50, 5)}, "selected": st.sidebar.checkbox("Run SMA Crossover")},
    "Bollinger Bands": {"class": BollingerBandsStrategy, "params": {"window": st.sidebar.slider("Bollinger Window", 10, 50, 20, 1), "num_std": st.sidebar.slider("Bollinger Std Dev", 1.0, 3.0, 2.0, 0.1)}, "selected": st.sidebar.checkbox("Run Bollinger Bands")},
    "RSI": {"class": RSIStrategy, "params": {"rsi_period": st.sidebar.slider("RSI Period", 5, 30, 14, 1), "overbought": st.sidebar.slider("RSI Overbought", 50, 90, 70, 5), "oversold": st.sidebar.slider("RSI Oversold", 10, 50, 30, 5)}, "selected": st.sidebar.checkbox("Run RSI")},
    "MACD": {"class": MACDStrategy, "params": {"fast_period": st.sidebar.slider("MACD Fast Period", 5, 20, 12, 1), "slow_period": st.sidebar.slider("MACD Slow Period", 15, 40, 26, 1), "signal_period": st.sidebar.slider("MACD Signal Period", 5, 15, 9, 1)}, "selected": st.sidebar.checkbox("Run MACD")},
    "Parabolic SAR": {"class": ParabolicSARStrategy, "params": {"af_start": st.sidebar.slider("PSAR AF Start", 0.01, 0.05, 0.02, 0.01), "af_inc": st.sidebar.slider("PSAR AF Increment", 0.01, 0.1, 0.02, 0.01), "af_max": st.sidebar.slider("PSAR AF Max", 0.1, 0.5, 0.2, 0.05)}, "selected": st.sidebar.checkbox("Run Parabolic SAR")},
    "Ichimoku Cloud": {"class": IchimokuStrategy, "params": {"tenkan_period": st.sidebar.slider("Ichimoku Tenkan Period", 5, 30, 9, 1), "kijun_period": st.sidebar.slider("Ichimoku Kijun Period", 15, 60, 26, 1), "senkou_b_period": st.sidebar.slider("Ichimoku Senkou B Period", 30, 120, 52, 2)}, "selected": st.sidebar.checkbox("Run Ichimoku Cloud")},
    "Williams %R": {"class": WilliamsRStrategy, "params": {"period": st.sidebar.slider("Williams %R Period", 5, 30, 14, 1), "overbought": st.sidebar.slider("Williams %R Overbought", -50, -5, -20, 5), "oversold": st.sidebar.slider("Williams %R Oversold", -95, -50, -80, 5)}, "selected": st.sidebar.checkbox("Run Williams %R")},
    "Stochastic Oscillator": {"class": StochasticStrategy, "params": {"k_period": st.sidebar.slider("Stochastic %K Period", 5, 30, 14, 1), "d_period": st.sidebar.slider("Stochastic %D Period", 3, 10, 3, 1), "overbought": st.sidebar.slider("Stochastic Overbought", 50, 90, 80, 5), "oversold": st.sidebar.slider("Stochastic Oversold", 10, 50, 20, 5)}, "selected": st.sidebar.checkbox("Run Stochastic Oscillator")},
    "ADX": {"class": ADXStrategy, "params": {"adx_period": st.sidebar.slider("ADX Period", 7, 30, 14, 1), "adx_threshold": st.sidebar.slider("ADX Threshold", 15, 40, 25, 1)}, "selected": st.sidebar.checkbox("Run ADX")},
    "Aroon Indicator": {"class": AroonStrategy, "params": {"period": st.sidebar.slider("Aroon Indicator Period", 10, 50, 25, 1)}, "selected": st.sidebar.checkbox("Run Aroon Indicator")},
    "CCI": {"class": CCIStrategy, "params": {"period": st.sidebar.slider("CCI Period", 10, 40, 20, 1), "overbought": st.sidebar.slider("CCI Overbought", 50, 200, 100, 10), "oversold": st.sidebar.slider("CCI Oversold", -200, -50, -100, 10)}, "selected": st.sidebar.checkbox("Run CCI")},
    "Fibonacci Retracement": {"class": FibonacciRetracementStrategy, "params": {"lookback": st.sidebar.slider("Fibonacci Lookback", 20, 200, 50, 5)}, "selected": st.sidebar.checkbox("Run Fibonacci Retracement")},
    "Turtle Trading": {"class": TurtleTradingStrategy, "params": {"entry_period": st.sidebar.slider("Turtle Entry Period", 10, 60, 20, 5), "exit_period": st.sidebar.slider("Turtle Exit Period", 5, 30, 10, 1)}, "selected": st.sidebar.checkbox("Run Turtle Trading")},
    "Breakout": {"class": BreakoutStrategy, "params": {"lookback": st.sidebar.slider("Breakout Lookback", 10, 60, 20, 1)}, "selected": st.sidebar.checkbox("Run Breakout")},
    "Mean Reversion": {"class": MeanReversionStrategy, "params": {"window": st.sidebar.slider("Mean Reversion Window", 10, 60, 20, 1), "threshold": st.sidebar.slider("Mean Reversion Threshold", 1.0, 3.0, 2.0, 0.1)}, "selected": st.sidebar.checkbox("Run Mean Reversion")},
    "Momentum": {"class": MomentumStrategy, "params": {"period": st.sidebar.slider("Momentum Period", 5, 40, 10, 1)}, "selected": st.sidebar.checkbox("Run Momentum")},
    "On-Balance Volume": {"class": OBVStrategy, "params": {"signal_period": st.sidebar.slider("OBV Signal Period", 10, 50, 20, 1)}, "selected": st.sidebar.checkbox("Run On-Balance Volume")},
    "PSAR+MACD": {"class": PSARMACDStrategy, "params": {"fast_period": st.sidebar.slider("PSAR+MACD Fast", 5, 20, 12, 1), "slow_period": st.sidebar.slider("PSAR+MACD Slow", 15, 40, 26, 1)}, "selected": st.sidebar.checkbox("Run PSAR+MACD")},
    "SMA+RSI": {"class": SMA_RSIStrategy, "params": {"sma_period": st.sidebar.slider("SMA+RSI SMA Period", 10, 100, 50, 5), "rsi_period": st.sidebar.slider("SMA+RSI RSI Period", 5, 30, 14, 1)}, "selected": st.sidebar.checkbox("Run SMA+RSI")},
    "Supertrend": {"class": SupertrendStrategy, "params": {"atr_period": st.sidebar.slider("Supertrend ATR Period", 5, 30, 10, 1), "multiplier": st.sidebar.slider("Supertrend Multiplier", 1.0, 5.0, 3.0, 0.5)}, "selected": st.sidebar.checkbox("Run Supertrend")},
    "TRIX": {"class": TRIXStrategy, "params": {"period": st.sidebar.slider("TRIX Period", 5, 30, 15, 1)}, "selected": st.sidebar.checkbox("Run TRIX")},
    "Triple MA": {"class": TripleMovingAverageStrategy, "params": {"short_window": st.sidebar.slider("Triple MA Short", 5, 30, 9, 1), "mid_window": st.sidebar.slider("Triple MA Mid", 20, 70, 21, 1), "long_window": st.sidebar.slider("Triple MA Long", 50, 200, 50, 5)}, "selected": st.sidebar.checkbox("Run Triple MA")},
    "VWAP": {"class": VWAPStrategy, "params": {"period": st.sidebar.slider("VWAP Period", 1, 30, 14, 1)}, "selected": st.sidebar.checkbox("Run VWAP")},
    "Money Flow Index": {"class": MoneyFlowIndexStrategy, "params": {"period": st.sidebar.slider("MFI Period", 5, 30, 14, 1), "overbought": st.sidebar.slider("MFI Overbought", 50, 90, 80, 5), "oversold": st.sidebar.slider("MFI Oversold", 10, 50, 20, 5)}, "selected": st.sidebar.checkbox("Run Money Flow Index")},
    "Vortex Indicator": {"class": VortexIndicatorStrategy, "params": {"period": st.sidebar.slider("Vortex Period", 5, 30, 14, 1)}, "selected": st.sidebar.checkbox("Run Vortex Indicator")},
}

# Button to run all strategies
if st.sidebar.button("Run All Strategies", key="run_all"):
    with st.spinner("Running backtest for all selected strategies..."):
        try:
            # Format dates properly
            start_date_str = start_date.strftime('%Y-%m-%d')
            end_date_str = end_date.strftime('%Y-%m-%d')
            
            # Download data from Yahoo Finance
            ticker_data = yf.download(ticker, start=start_date_str, end=end_date_str)
            
            # Save to CSV for the data handler to use
            if not os.path.exists('data'):
                os.makedirs('data')
            csv_path = f'data/{ticker}.csv'
            ticker_data.to_csv(csv_path)
            
            # Initialize results storage
            st.session_state.strategies_results = {}
            
            # Run each selected strategy
            for strategy_name, strategy_info in strategies.items():
                if strategy_info["selected"]:
                    with st.spinner(f"Running backtest for: {strategy_name}..."):
                        # Initialize components
                        events = queue.Queue()
                        try:
                            # Initialize data handler
                            data_handler = HistoricCSVDataHandler(events, csv_dir='data', symbol_list=[ticker])
                            
                            # Initialize execution handler
                            execution_handler = SimulatedExecutionHandler(events)
                            
                            # Initialize strategy with parameters
                            strategy = strategy_info["class"](data_handler, events, **strategy_info["params"])
                            
                            # Convert position size from percentage to decimal
                            position_size = float(position_size_pct) / 100.0
                            
                            # Initialize portfolio with explicit type conversion
                            portfolio = Portfolio(
                                data_handler=data_handler,
                                events=events,
                                start_date=start_date_str,
                                initial_capital=float(initial_capital),
                                position_size=position_size
                            )
                            
                            # Create and run the backtest
                            backtest = Backtest(
                                data_handler,
                                events,
                                strategy,
                                portfolio,
                                execution_handler,
                                start_date_str,
                                end_date_str
                            )
                            backtest.simulate_trading()
                            
                            # Store results
                            results = backtest.get_results()
                            st.session_state.strategies_results[strategy_name] = results
                        except Exception as e:
                            st.error(f"Error running {strategy_name}: {str(e)}")
                            logging.error(f"Error in {strategy_name}: {str(e)}")
                            logging.error(traceback.format_exc())
        
        except Exception as e:
            st.error(f"Error in backtest setup: {str(e)}")
            logging.error(f"Setup error: {str(e)}")
            logging.error(traceback.format_exc())

# Display results if available
if st.session_state.strategies_results:
    # Prepare dataframe for displaying results
    results_data = []
    for strategy_name, results in st.session_state.strategies_results.items():
        if results is not None and 'stats' in results:
            stats = results['stats']
            results_data.append({
                'Strategy': strategy_name,
                'Net Profit ($)': stats.get('total_return_dollars', 0),
                'Return (%)': stats.get('total_return_pct', 0),
                'Max Drawdown (%)': stats.get('max_drawdown', 0),
                'Sharpe Ratio': stats.get('sharpe', 0),
                'Win Rate (%)': stats.get('win_rate', 0),
                'Profit Factor': stats.get('profit_factor', 0),
                'Trades': stats.get('trade_count', 0)
            })
    
    if results_data:
        # Convert to dataframe and sort by return percentage
        results_df = pd.DataFrame(results_data)
        results_df = results_df.sort_values('Return (%)', ascending=False).reset_index(drop=True)
        
        # Format columns
        results_df['Net Profit ($)'] = results_df['Net Profit ($)'].apply(lambda x: f"${x:,.2f}")
        results_df['Return (%)'] = results_df['Return (%)'].apply(lambda x: f"{x:.2f}%")
        results_df['Max Drawdown (%)'] = results_df['Max Drawdown (%)'].apply(lambda x: f"{x:.2f}%")
        results_df['Sharpe Ratio'] = results_df['Sharpe Ratio'].apply(lambda x: f"{x:.2f}")
        results_df['Win Rate (%)'] = results_df['Win Rate (%)'].apply(lambda x: f"{x:.2f}%")
        results_df['Profit Factor'] = results_df['Profit Factor'].apply(lambda x: f"{x:.2f}")
        
        # Display the table with ranking
        st.header("Strategy Performance Ranking")
        st.dataframe(results_df, use_container_width=True)
        
        # Allow user to select a strategy for detailed view
        strategy_options = list(st.session_state.strategies_results.keys())
        selected_strategy = st.selectbox("Select a strategy to view details:", strategy_options)
        
        # Display detailed results for selected strategy
        if selected_strategy in st.session_state.strategies_results:
            st.header(f"Detailed Analysis: {selected_strategy}")
            
            results = st.session_state.strategies_results[selected_strategy]
            
            # Create tabs for different sections
            tab1, tab2, tab3 = st.tabs(["Performance Metrics", "Equity Curve", "Trade Log"])
            
            with tab1:
                st.subheader("Key Metrics")
                cols = st.columns(4)
                
                stats = results['stats']
                
                # Display key metrics in columns
                cols[0].metric("Total Return", f"{stats.get('total_return_pct', 0):.2f}%")
                cols[1].metric("Net Profit", f"${stats.get('total_return_dollars', 0):,.2f}")
                cols[2].metric("Sharpe Ratio", f"{stats.get('sharpe', 0):.2f}")
                cols[3].metric("Max Drawdown", f"{stats.get('max_drawdown', 0):.2f}%")
                
                # Second row of metrics
                cols = st.columns(4)
                cols[0].metric("Win Rate", f"{stats.get('win_rate', 0):.2f}%")
                cols[1].metric("Profit Factor", f"{stats.get('profit_factor', 0):.2f}")
                cols[2].metric("Total Trades", f"{stats.get('trade_count', 0)}")
                cols[3].metric("Avg Profit per Trade", f"${stats.get('avg_profit_per_trade', 0):.2f}")
                
            with tab2:
                st.subheader("Equity Curve")
                
                # Get equity curve
                if 'equity_curve' in results:
                    equity_df = results['equity_curve']
                    
                    # Create equity curve figure with Plotly
                    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                                        vertical_spacing=0.05,
                                        row_heights=[0.7, 0.3])
                    
                    # Add equity curve trace
                    fig.add_trace(
                        go.Scatter(
                            x=equity_df.index, 
                            y=equity_df['total'], 
                            mode='lines',
                            name='Portfolio Value',
                            line=dict(color='royalblue', width=2)
                        ),
                        row=1, col=1
                    )
                    
                    # Add returns trace in the bottom subplot
                    fig.add_trace(
                        go.Scatter(
                            x=equity_df.index, 
                            y=equity_df['returns']*100, 
                            mode='lines',
                            name='Daily Returns (%)',
                            line=dict(color='green', width=1)
                        ),
                        row=2, col=1
                    )
                    
                    # Add zero line for returns
                    fig.add_hline(
                        y=0, 
                        line_dash="dash", 
                        line_color="gray",
                        row=2, col=1
                    )
                    
                    # Update layout
                    fig.update_layout(
                        height=600,
                        title_text=f"Portfolio Equity Curve - {selected_strategy}",
                        xaxis_title="Date",
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
                        margin=dict(l=0, r=0, t=30, b=0)
                    )
                    
                    fig.update_yaxes(title_text="Portfolio Value ($)", row=1, col=1)
                    fig.update_yaxes(title_text="Daily Return (%)", row=2, col=1)
                    
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Equity curve data not available for this strategy.")
                    
            with tab3:
                st.subheader("Trade Log")
                
                # Display trade log if available
                if 'trade_log' in results and not results['trade_log'].empty:
                    trade_log = results['trade_log'].copy()
                    
                    # Format columns
                    trade_log['Entry Date'] = pd.to_datetime(trade_log['entry_date']).dt.strftime('%Y-%m-%d')
                    trade_log['Exit Date'] = pd.to_datetime(trade_log['exit_date']).dt.strftime('%Y-%m-%d')
                    trade_log['Entry Price'] = trade_log['entry_price'].apply(lambda x: f"${x:.2f}")
                    trade_log['Exit Price'] = trade_log['exit_price'].apply(lambda x: f"${x:.2f}")
                    trade_log['Profit/Loss'] = trade_log['profit_loss'].apply(lambda x: f"${x:.2f}")
                    trade_log['Return'] = trade_log['return_pct'].apply(lambda x: f"{x:.2f}%")
                    
                    # Select columns to display
                    display_cols = ['Entry Date', 'Exit Date', 'Entry Price', 'Exit Price', 'Shares', 'Profit/Loss', 'Return']
                    st.dataframe(trade_log[display_cols], use_container_width=True)
                else:
                    st.info("No trades were executed for this strategy.")

# Explanatory section at the bottom
st.markdown("---")
st.subheader("About This Backtester")
st.write("""
This comprehensive stock backtesting tool allows you to evaluate multiple trading strategies against historical market data.
The tool calculates important metrics like total return, max drawdown, Sharpe ratio, and win rate to help you identify the best strategies for your investment style.

**Key Features:**
- Test 25+ technical analysis strategies
- Customize strategy parameters
- Set position sizing as a percentage of portfolio
- Compare strategy performance metrics
- View detailed equity curves and trade logs
""")

st.markdown("---")
st.caption("© 2025 Comprehensive Stock Backtester | For educational purposes only. Not financial advice.")