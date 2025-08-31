import pandas as pd
import numpy as np
from backtest.strategy import Strategy
from backtest.event import SignalEvent

class DonchianChannelStrategy(Strategy):
    def __init__(self, data_handler, events, period=20):
        self.data_handler = data_handler
        self.events = events
        self.symbol_list = self.data_handler.symbol_list
        self.period = period
        self.bought = {s: False for s in self.symbol_list}

    def calculate_signals(self, event):
        if event.type == 'MARKET':
            for s in self.symbol_list:
                try:
                    bars = self.data_handler.get_latest_bars(s, self.period + 1)
                    if len(bars) < self.period + 1:
                        continue

                    # Extract scalar values
                    upper_channel = float(bars['High'].shift(1).rolling(window=self.period).max().iloc[-1])
                    lower_channel = float(bars['Low'].shift(1).rolling(window=self.period).min().iloc[-1])
                    
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
                    
                    price = self.data_handler.get_latest_bar_value(s, 'Close')
                    
                    # Check for NaN values
                    if np.isnan(upper_channel) or np.isnan(lower_channel) or np.isnan(price):
                        continue

                    if price > upper_channel and not self.bought[s]:
                        signal = SignalEvent(self.__class__.__name__, s, dt, 'LONG', 1.0)
                        self.events.put(signal)
                        self.bought[s] = True
                    elif price < lower_channel and self.bought[s]:
                        signal = SignalEvent(self.__class__.__name__, s, dt, 'EXIT', 1.0)
                        self.events.put(signal)
                        self.bought[s] = False
                        
                except Exception as e:
                    print(f"Error in calculate_signals for symbol {s}: {e}")
                    continue