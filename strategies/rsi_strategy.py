import pandas as pd
import numpy as np
from backtest.strategy import Strategy
from backtest.event import SignalEvent

class RSIStrategy(Strategy):
    def __init__(self, data_handler, events, rsi_period=14, oversold_threshold=30, overbought_threshold=70, 
                 period=None):  # Added period as alternative parameter name
        self.data_handler = data_handler
        self.events = events
        self.symbol_list = self.data_handler.symbol_list
        
        # Allow for alternative parameter name
        self.rsi_period = period if period is not None else rsi_period
        self.oversold_threshold = oversold_threshold
        self.overbought_threshold = overbought_threshold
        self.bought = {s: False for s in self.symbol_list}

    def calculate_signals(self, event):
        if event.type == 'MARKET':
            for s in self.symbol_list:
                try:
                    # Get the necessary bars
                    bars = self.data_handler.get_latest_bars(s, self.rsi_period + 1)
                    if len(bars) < self.rsi_period + 1:
                        continue

                    # Calculate RSI
                    delta = bars['Close'].diff()
                    gain = (delta.where(delta > 0, 0)).ewm(com=self.rsi_period - 1, min_periods=self.rsi_period).mean()
                    loss = (-delta.where(delta < 0, 0)).ewm(com=self.rsi_period - 1, min_periods=self.rsi_period).mean()
                    rs = gain / loss
                    rsi = 100 - (100 / (1 + rs))
                    
                    # Extract scalar RSI value
                    current_rsi = float(rsi.iloc[-1])
                    
                    # Get datetime safely
                    latest_bar = self.data_handler.get_latest_bar(s)
                    if latest_bar is None or latest_bar.empty:
                        continue
                        
                    try:
                        dt = latest_bar.index[0]
                        if isinstance(dt, pd.Series):
                            dt = dt.iloc[0]
                    except (IndexError, AttributeError):
                        continue
                    
                    # Check for NaN value
                    if np.isnan(current_rsi):
                        continue
                    
                    # Buy signal (oversold condition)
                    if current_rsi < self.oversold_threshold and not self.bought[s]:
                        signal = SignalEvent(self.__class__.__name__, s, dt, 'LONG', 1.0)
                        self.events.put(signal)
                        self.bought[s] = True
                    
                    # Sell signal (overbought condition)
                    elif current_rsi > self.overbought_threshold and self.bought[s]:
                        signal = SignalEvent(self.__class__.__name__, s, dt, 'EXIT', 1.0)
                        self.events.put(signal)
                        self.bought[s] = False
                
                except Exception as e:
                    print(f"Error in calculate_signals for symbol {s}: {e}")
                    continue