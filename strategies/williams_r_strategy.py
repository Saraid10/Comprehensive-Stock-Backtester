import pandas as pd
import numpy as np
from backtest.strategy import Strategy
from backtest.event import SignalEvent

class WilliamsRStrategy(Strategy):
    def __init__(self, data_handler, events, period=14, oversold=-80, overbought=-20):
        self.data_handler = data_handler
        self.events = events
        self.symbol_list = self.data_handler.symbol_list
        self.period = period
        self.oversold = oversold
        self.overbought = overbought
        self.bought = {s: False for s in self.symbol_list}

    def calculate_signals(self, event):
        if event.type == 'MARKET':
            for s in self.symbol_list:
                try:
                    bars = self.data_handler.get_latest_bars(s, self.period)
                    if len(bars) < self.period:
                        continue

                    highest_high = bars['High'].rolling(window=self.period).max()
                    lowest_low = bars['Low'].rolling(window=self.period).min()
                    williams_r = -100 * (highest_high - bars['Close']) / (highest_high - lowest_low)
                    
                    # Extract scalar value
                    williams_r_last = float(williams_r.iloc[-1])
                    
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
                    if np.isnan(williams_r_last):
                        continue

                    if williams_r_last < self.oversold and not self.bought[s]:
                        signal = SignalEvent(self.__class__.__name__, s, dt, 'LONG', 1.0)
                        self.events.put(signal)
                        self.bought[s] = True
                    elif williams_r_last > self.overbought and self.bought[s]:
                        signal = SignalEvent(self.__class__.__name__, s, dt, 'EXIT', 1.0)
                        self.events.put(signal)
                        self.bought[s] = False
                        
                except Exception as e:
                    print(f"Error in calculate_signals for symbol {s}: {e}")
                    continue