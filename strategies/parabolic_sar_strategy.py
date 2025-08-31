import pandas as pd
import numpy as np
from backtest.strategy import Strategy
from backtest.event import SignalEvent

class ParabolicSARStrategy(Strategy):
    def __init__(self, data_handler, events, initial_af=0.02, max_af=0.2):
        self.data_handler = data_handler
        self.events = events
        self.symbol_list = self.data_handler.symbol_list
        self.initial_af = initial_af
        self.max_af = max_af
        self.bought = {s: False for s in self.symbol_list}
        self.sar = {s: None for s in self.symbol_list}
        self.ep = {s: None for s in self.symbol_list}
        self.af = {s: self.initial_af for s in self.symbol_list}

    def calculate_signals(self, event):
        if event.type == 'MARKET':
            for s in self.symbol_list:
                try:
                    bars = self.data_handler.get_latest_bars(s, 2)
                    if len(bars) < 2:
                        continue

                    # Extract scalar values
                    high = float(bars['High'].iloc[-1])
                    low = float(bars['Low'].iloc[-1])
                    prev_high = float(bars['High'].iloc[-2])
                    prev_low = float(bars['Low'].iloc[-2])
                    
                    # Check for NaN values
                    if np.isnan(high) or np.isnan(low) or np.isnan(prev_high) or np.isnan(prev_low):
                        continue

                    # Initialize on the first valid bar
                    if self.sar[s] is None:
                        if bars['Close'].iloc[-1] > bars['Close'].iloc[-2]:
                            self.bought[s] = True
                            self.sar[s] = prev_low
                            self.ep[s] = high
                        else:
                            self.bought[s] = False
                            self.sar[s] = prev_high
                            self.ep[s] = low
                        continue

                    prev_sar = self.sar[s]
                    
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
                    
                    if self.bought[s]: # Uptrend
                        self.sar[s] = prev_sar + self.af[s] * (self.ep[s] - prev_sar)
                        if high > self.ep[s]:
                            self.ep[s] = high
                            self.af[s] = min(self.af[s] + self.initial_af, self.max_af)
                        
                        if self.sar[s] > low: # Reversal to downtrend
                            signal = SignalEvent(self.__class__.__name__, s, dt, 'EXIT', 1.0)
                            self.events.put(signal)
                            self.bought[s] = False
                            self.sar[s] = self.ep[s] # The high point of the uptrend
                            self.ep[s] = low
                            self.af[s] = self.initial_af
                    else: # Downtrend
                        self.sar[s] = prev_sar - self.af[s] * (prev_sar - self.ep[s])
                        if low < self.ep[s]:
                            self.ep[s] = low
                            self.af[s] = min(self.af[s] + self.initial_af, self.max_af)

                        if self.sar[s] < high: # Reversal to uptrend
                            signal = SignalEvent(self.__class__.__name__, s, dt, 'LONG', 1.0)
                            self.events.put(signal)
                            self.bought[s] = True
                            self.sar[s] = self.ep[s] # The low point of the downtrend
                            self.ep[s] = high
                            self.af[s] = self.initial_af
                            
                except Exception as e:
                    print(f"Error in calculate_signals for symbol {s}: {e}")
                    continue