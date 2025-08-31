import pandas as pd
import numpy as np
from backtest.strategy import Strategy
from backtest.event import SignalEvent

class StochasticOscillatorStrategy(Strategy):
    def __init__(self, data_handler, events, k_period=14, oversold_threshold=20, overbought_threshold=80):
        self.data_handler = data_handler
        self.events = events
        self.symbol_list = self.data_handler.symbol_list
        self.k_period = k_period
        self.oversold_threshold = oversold_threshold
        self.overbought_threshold = overbought_threshold
        self.bought = {s: False for s in self.symbol_list}

    def calculate_signals(self, event):
        if event.type == 'MARKET':
            for s in self.symbol_list:
                try:
                    bars = self.data_handler.get_latest_bars(s, self.k_period)
                    if len(bars) < self.k_period:
                        continue

                    low_k = bars['Low'].rolling(window=self.k_period).min()
                    high_k = bars['High'].rolling(window=self.k_period).max()
                    percent_k = 100 * (bars['Close'] - low_k) / (high_k - low_k)
                    
                    # Extract scalar value
                    percent_k_last = float(percent_k.iloc[-1])
                    
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
                    if np.isnan(percent_k_last):
                        continue

                    if percent_k_last < self.oversold_threshold and not self.bought[s]:
                        signal = SignalEvent(self.__class__.__name__, s, dt, 'LONG', 1.0)
                        self.events.put(signal)
                        self.bought[s] = True
                    elif percent_k_last > self.overbought_threshold and self.bought[s]:
                        signal = SignalEvent(self.__class__.__name__, s, dt, 'EXIT', 1.0)
                        self.events.put(signal)
                        self.bought[s] = False
                        
                except Exception as e:
                    print(f"Error in calculate_signals for symbol {s}: {e}")
                    continue