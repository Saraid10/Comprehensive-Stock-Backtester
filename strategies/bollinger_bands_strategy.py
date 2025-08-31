import pandas as pd
import numpy as np
from backtest.strategy import Strategy
from backtest.event import SignalEvent

class BollingerBandsStrategy(Strategy):
    def __init__(self, data_handler, events, bb_period=20, bb_std_dev=2.0):
        self.data_handler = data_handler
        self.events = events
        self.symbol_list = self.data_handler.symbol_list
        self.bb_period = bb_period
        self.bb_std_dev = bb_std_dev
        self.bought = {s: False for s in self.symbol_list}

    def calculate_signals(self, event):
        if event.type == 'MARKET':
            for s in self.symbol_list:
                try:
                    bars = self.data_handler.get_latest_bars(s, self.bb_period)
                    if len(bars) < self.bb_period:
                        continue
                    
                    # Extract scalar values directly
                    middle_band = float(bars['Close'].rolling(window=self.bb_period).mean().iloc[-1])
                    std_dev = float(bars['Close'].rolling(window=self.bb_period).std().iloc[-1])
                    lower_band = middle_band - (std_dev * self.bb_std_dev)
                    upper_band = middle_band + (std_dev * self.bb_std_dev)
                    
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
                    if np.isnan(lower_band) or np.isnan(upper_band) or np.isnan(price):
                        continue

                    if price < lower_band and not self.bought[s]:
                        signal = SignalEvent(self.__class__.__name__, s, dt, 'LONG', 1.0)
                        self.events.put(signal)
                        self.bought[s] = True
                    elif price > upper_band and self.bought[s]:
                        signal = SignalEvent(self.__class__.__name__, s, dt, 'EXIT', 1.0)
                        self.events.put(signal)
                        self.bought[s] = False
                        
                except Exception as e:
                    print(f"Error in calculate_signals for symbol {s}: {e}")
                    continue