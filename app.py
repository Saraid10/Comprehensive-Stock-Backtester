import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime
import queue

# --- Local Module Imports ---
from backtest.data import HistoricDataHandler
from backtest.portfolio import Portfolio
from backtest.execution import SimulatedExecutionHandler
from backtest.engine import Backtest
from backtest.performance import get_performance_metrics
from strategies.buy_and_hold import BuyAndHoldStrategy
from strategies.sma_crossover import SMACrossoverStrategy
from strategies.rsi_strategy import RSIStrategy
from strategies.bollinger_bands_strategy import BollingerBandsStrategy
from strategies.macd_strategy import MACDStrategy
from strategies.parabolic_sar_strategy import ParabolicSARStrategy
from strategies.stochastic_oscillator_strategy import StochasticOscillatorStrategy
from strategies.on_balance_volume_strategy import OnBalanceVolumeStrategy
from strategies.ichimoku_cloud_strategy import IchimokuCloudStrategy
from strategies.atr_channel_strategy import ATRChannelStrategy
from strategies.rate_of_change_strategy import RateOfChangeStrategy
from strategies.awesome_oscillator_strategy import AwesomeOscillatorStrategy
from strategies.keltner_channel_strategy import KeltnerChannelStrategy
from strategies.vwap_crossover_strategy import VWAPCrossoverStrategy
from strategies.donchian_channel_strategy import DonchianChannelStrategy
from strategies.cci_strategy import CCIStrategy
from strategies.ma_ribbon_strategy import MARibbonStrategy
from strategies.chaikin_money_flow_strategy import ChaikinMoneyFlowStrategy
from strategies.williams_r_strategy import WilliamsRStrategy
from strategies.aroon_indicator_strategy import AroonIndicatorStrategy
from strategies.money_flow_index_strategy import MoneyFlowIndexStrategy
from strategies.trix_strategy import TrixStrategy
from strategies.vortex_indicator_strategy import VortexIndicatorStrategy
from strategies.dema_crossover_strategy import DEMACrossoverStrategy
from strategies.tema_crossover_strategy import TEMACrossoverStrategy

# --- App Configuration ---
st.set_page_config(
    page_title="Comprehensive Stock Backtester",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Strategy Registry with Default Parameters ---
DEFAULT_STRATEGY_REGISTRY = {
    "Buy and Hold": {"class": BuyAndHoldStrategy, "params": {}},
    "SMA Crossover (50/200)": {"class": SMACrossoverStrategy, "params": {"short_window": 50, "long_window": 200}},
    "DEMA Crossover (50/200)": {"class": DEMACrossoverStrategy, "params": {"short_period": 50, "long_period": 200}},
    "TEMA Crossover (50/200)": {"class": TEMACrossoverStrategy, "params": {"short_period": 50, "long_period": 200}},
    "RSI (14/30/70)": {"class": RSIStrategy, "params": {"rsi_period": 14, "oversold_threshold": 30, "overbought_threshold": 70}},
    "Bollinger Bands (20/2)": {"class": BollingerBandsStrategy, "params": {"bb_period": 20, "bb_std_dev": 2.0}},
    "MACD (12/26/9)": {"class": MACDStrategy, "params": {"short_ema_period": 12, "long_ema_period": 26, "signal_ema_period": 9}},
    "Parabolic SAR (0.02/0.2)": {"class": ParabolicSARStrategy, "params": {"initial_af": 0.02, "max_af": 0.2}},
    "Stochastic Oscillator (14/20/80)": {"class": StochasticOscillatorStrategy, "params": {"k_period": 14, "oversold_threshold": 20, "overbought_threshold": 80}},
    "OBV Crossover (20)": {"class": OnBalanceVolumeStrategy, "params": {"obv_ma_period": 20}},
    "Ichimoku Cloud (9/26)": {"class": IchimokuCloudStrategy, "params": {"tenkan_period": 9, "kijun_period": 26}},
    "ATR Channel Breakout (20/14/2)": {"class": ATRChannelStrategy, "params": {"sma_period": 20, "atr_period": 14, "atr_multiplier": 2.0}},
    "Rate of Change (12/20)": {"class": RateOfChangeStrategy, "params": {"roc_period": 12, "ma_period": 20}},
    "Awesome Oscillator (5/34)": {"class": AwesomeOscillatorStrategy, "params": {"short_period": 5, "long_period": 34}},
    "Keltner Channel (20/10/2)": {"class": KeltnerChannelStrategy, "params": {"ema_period": 20, "atr_period": 10, "atr_multiplier": 2.0}},
    "VWAP Crossover (20)": {"class": VWAPCrossoverStrategy, "params": {"vwap_ma_period": 20}},
    "Donchian Channel (20)": {"class": DonchianChannelStrategy, "params": {"period": 20}},
    "CCI (20/-100/100)": {"class": CCIStrategy, "params": {"period": 20, "oversold": -100, "overbought": 100}},
    "MA Ribbon (5/10/20)": {"class": MARibbonStrategy, "params": {"short_period": 5, "medium_period": 10, "long_period": 20}},
    "Chaikin Money Flow (20)": {"class": ChaikinMoneyFlowStrategy, "params": {"period": 20}},
    "Williams %R (14/-80/-20)": {"class": WilliamsRStrategy, "params": {"period": 14, "oversold": -80, "overbought": -20}},
    "Aroon Indicator (25)": {"class": AroonIndicatorStrategy, "params": {"period": 25}},
    "Money Flow Index (14/20/80)": {"class": MoneyFlowIndexStrategy, "params": {"period": 14, "oversold": 20, "overbought": 80}},
    "TRIX (15/9)": {"class": TrixStrategy, "params": {"period": 15, "signal_period": 9}},
    "Vortex Indicator (14)": {"class": VortexIndicatorStrategy, "params": {"period": 14}},
}

# --- Caching ---
@st.cache_data
def get_stock_data(ticker, start_date, end_date):
    try:
        data = yf.download(ticker, start=start_date, end=end_date)
        if data.empty:
            st.error(f"Error: No data found for ticker '{ticker}'. It might be delisted or an invalid ticker.")
            return None
        return data
    except Exception as e:
        st.error(f"An error occurred while fetching data for {ticker}: {e}")
        return None

# --- Sidebar for User Inputs ---
st.sidebar.header("Backtest Configuration")
ticker = st.sidebar.text_input("Stock Ticker", "AAPL").upper()
start_date = st.sidebar.date_input("Start Date", datetime(2020, 1, 1))
end_date = st.sidebar.date_input("End Date", datetime.now())
initial_capital = st.sidebar.number_input("Initial Capital", 1000, 1000000, 100000, step=1000)

# --- Position Sizing Settings ---
st.sidebar.header("Position Sizing")
position_size_pct = st.sidebar.slider("Position Size (% of Portfolio)", 1, 100, 5, 1, 
                                    help="What percentage of the portfolio to invest in each position")

# Display warning for aggressive position sizing
if position_size_pct > 20:
    st.sidebar.warning("⚠️ **High Risk Alert**: Position sizes above 20% reduce diversification and significantly increase risk. This approach is not recommended for most trading strategies.", icon="⚠️")
elif position_size_pct > 10:
    st.sidebar.info("ℹ️ Position sizes between 10-20% represent an aggressive approach with higher risk.", icon="ℹ️")

# --- Strategy Parameter Customization ---
st.sidebar.header("Strategy Parameters")

# Create a copy of the default registry that we'll modify with user inputs
STRATEGY_REGISTRY = DEFAULT_STRATEGY_REGISTRY.copy()

# Create expandable sections for each strategy with parameter controls
strategy_toggles = {}
for strategy_name, config in DEFAULT_STRATEGY_REGISTRY.items():
    strategy_toggles[strategy_name] = st.sidebar.checkbox(f"Run {strategy_name}", value=True)
    
    if strategy_toggles[strategy_name]:
        with st.sidebar.expander(f"Customize {strategy_name}"):
            custom_params = {}
            for param_name, param_value in config["params"].items():
                if isinstance(param_value, int):
                    custom_params[param_name] = st.number_input(
                        f"{param_name}", 
                        min_value=1 if 'period' in param_name else None,
                        value=param_value, 
                        key=f"{strategy_name}_{param_name}"
                    )
                elif isinstance(param_value, float):
                    custom_params[param_name] = st.number_input(
                        f"{param_name}", 
                        value=param_value, 
                        format="%.2f", 
                        step=0.1, 
                        key=f"{strategy_name}_{param_name}"
                    )
                else:
                    custom_params[param_name] = param_value
                    
            # Update the registry with custom parameters
            STRATEGY_REGISTRY[strategy_name]["params"] = custom_params

run_button = st.sidebar.button("Run All Strategies", type="primary")

# --- Main Application Area ---
st.title("📈 Comprehensive Stock Backtester")
st.write("""
This tool runs multiple trading strategies against historical stock data to identify the top performers. 
Configure your backtest on the left and click 'Run All Strategies' to begin.
""")

if run_button and ticker:
    data = get_stock_data(ticker, start_date, end_date)
    if data is not None:
        all_results = []
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Filter strategies based on toggles
        active_strategies = {name: config for name, config in STRATEGY_REGISTRY.items() if strategy_toggles[name]}
        
        for i, (name, config) in enumerate(active_strategies.items()):
            status_text.text(f"Running backtest for: {name}...")
            
            # --- Initialize and Run Backtest for each strategy ---
            events = queue.Queue()
            symbol_list = [ticker]
            
            data_handler = HistoricDataHandler(events, symbol_list, data)
            strategy = config["class"](data_handler, events, **config["params"])
            # Pass position size percentage to the Portfolio
            portfolio = Portfolio(data_handler, events, start_date, initial_capital, position_size_pct/100.0)
            execution_handler = SimulatedExecutionHandler(events, data_handler)

            backtest = Backtest(data_handler, strategy, portfolio, execution_handler)
            equity_curve, trade_log = backtest.simulate_trading()
            
            # --- Store Results ---
            performance = get_performance_metrics(equity_curve, trade_log, initial_capital)
            all_results.append({
                "name": name,
                "performance": performance,
                "equity_curve": equity_curve,
                "trade_log": trade_log
            })
            
            progress_bar.progress((i + 1) / len(active_strategies))

        status_text.text("All backtests complete! Compiling results...")

        # --- Rank and Display Results ---
        if all_results:
            all_results.sort(key=lambda x: x["performance"]["Net Profit"], reverse=True)
            
            st.subheader("🏆 Strategy Performance Ranking")
            
            rank_data = []
            for i, result in enumerate(all_results):
                p = result["performance"]
                rank_data.append({
                    "Rank": i + 1,
                    "Strategy": result["name"],
                    "Net Profit ($)": f"{p['Net Profit']:,.2f}",
                    "Sharpe Ratio": f"{p['Sharpe Ratio']:.2f}",
                    "Max Drawdown (%)": f"{p['Max Drawdown']:.2f}",
                    "Total Trades": p["Total Trades"]
                })
            
            rank_df = pd.DataFrame(rank_data).set_index("Rank")
            st.dataframe(rank_df)
            
            st.subheader("Comparative Equity Curves (Top 5)")
            top_5_results = all_results[:5]
            equity_curves_df = pd.DataFrame()
            for result in top_5_results:
                if 'equity_curve' in result['equity_curve'].columns:
                    curve = result['equity_curve'][['equity_curve']].rename(columns={'equity_curve': result['name']})
                    if equity_curves_df.empty:
                        equity_curves_df = curve
                    else:
                        equity_curves_df = equity_curves_df.join(curve, how='outer')
            
            equity_curves_df.ffill(inplace=True)
            st.line_chart(equity_curves_df)
            
            st.subheader("Detailed Analysis of Top Performers")
            for result in top_5_results:
                with st.expander(f"View Details for: {result['name']}"):
                    rank_info = rank_df[rank_df['Strategy'] == result['name']]
                    st.dataframe(rank_info)
                    st.line_chart(result['equity_curve']['equity_curve'])
                    st.write("Trade Log")
                    st.dataframe(pd.DataFrame(result['trade_log']))
        
        progress_bar.empty()
        status_text.success("Analysis complete!")

elif run_button and not ticker:
    st.error("Please enter a stock ticker to begin.")