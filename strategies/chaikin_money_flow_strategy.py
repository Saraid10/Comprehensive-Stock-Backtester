import pandas as pd
import numpy as np
from backtest.strategy import Strategy
from backtest.event import SignalEvent

class ChaikinMoneyFlowStrategy(Strategy):
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
                    bars = self.data_handler.get_latest_bars(s, self.period)
                    if len(bars) < self.period:
                        continue

                    mf_multiplier = ((bars['Close'] - bars['Low']) - (bars['High'] - bars['Close'])) / (bars['High'] - bars['Low'])
                    mf_volume = mf_multiplier * bars['Volume']
                    cmf = mf_volume.rolling(window=self.period).sum() / bars['Volume'].rolling(window=self.period).sum()
                    
                    # Extract scalar values
                    cmf_last = float(cmf.iloc[-1])
                    cmf_prev = float(cmf.iloc[-2])
                    
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
                    if np.isnan(cmf_last) or np.isnan(cmf_prev):
                        continue

                    if cmf_last > 0 and cmf_prev <= 0 and not self.bought[s]:
                        signal = SignalEvent(self.__class__.__name__, s, dt, 'LONG', 1.0)
                        self.events.put(signal)
                        self.bought[s] = True
                    elif cmf_last < 0 and cmf_prev >= 0 and self.bought[s]:
                        signal = SignalEvent(self.__class__.__name__, s, dt, 'EXIT', 1.0)
                        self.events.put(signal)
                        self.bought[s] = False
                        
                except Exception as e:
                    print(f"Error in calculate_signals for symbol {s}: {e}")
                    continue