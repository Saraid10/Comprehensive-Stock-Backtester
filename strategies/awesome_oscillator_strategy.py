import pandas as pd
import numpy as np
from backtest.strategy import Strategy
from backtest.event import SignalEvent

class AwesomeOscillatorStrategy(Strategy):
    def __init__(self, data_handler, events, short_period=5, long_period=34):
        self.data_handler = data_handler
        self.events = events
        self.symbol_list = self.data_handler.symbol_list
        self.short_period = short_period
        self.long_period = long_period
        self.bought = {s: False for s in self.symbol_list}

    def calculate_signals(self, event):
        if event.type == 'MARKET':
            for s in self.symbol_list:
                try:
                    bars = self.data_handler.get_latest_bars(s, self.long_period)
                    if len(bars) < self.long_period:
                        continue

                    midpoint = (bars['High'] + bars['Low']) / 2
                    short_ma = midpoint.rolling(window=self.short_period).mean()
                    long_ma = midpoint.rolling(window=self.long_period).mean()
                    ao = short_ma - long_ma
                    
                    # Extract scalar values
                    ao_last = float(ao.iloc[-1])
                    ao_prev = float(ao.iloc[-2])
                    
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
                    
                    # Check for NaN values
                    if np.isnan(ao_last) or np.isnan(ao_prev):
                        continue

                    if ao_last > 0 and ao_prev <= 0 and not self.bought[s]:
                        signal = SignalEvent(self.__class__.__name__, s, dt, 'LONG', 1.0)
                        self.events.put(signal)
                        self.bought[s] = True
                    elif ao_last < 0 and ao_prev >= 0 and self.bought[s]:
                        signal = SignalEvent(self.__class__.__name__, s, dt, 'EXIT', 1.0)
                        self.events.put(signal)
                        self.bought[s] = False
                        
                except Exception as e:
                    print(f"Error in calculate_signals for symbol {s}: {e}")
                    continue