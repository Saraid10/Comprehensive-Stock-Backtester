import pandas as pd
import numpy as np
from backtest.strategy import Strategy
from backtest.event import SignalEvent

class RateOfChangeStrategy(Strategy):
    def __init__(self, data_handler, events, roc_period=12, ma_period=20):
        self.data_handler = data_handler
        self.events = events
        self.symbol_list = self.data_handler.symbol_list
        self.roc_period = roc_period
        self.ma_period = ma_period
        self.bought = {s: False for s in self.symbol_list}

    def calculate_signals(self, event):
        if event.type == 'MARKET':
            for s in self.symbol_list:
                try:
                    bars = self.data_handler.get_latest_bars(s, self.roc_period + self.ma_period)
                    if len(bars) < self.roc_period + self.ma_period:
                        continue

                    roc = (bars['Close'] - bars['Close'].shift(self.roc_period)) / bars['Close'].shift(self.roc_period) * 100
                    roc_ma = roc.rolling(window=self.ma_period).mean()
                    
                    # Extract scalar values
                    roc_last = float(roc.iloc[-1])
                    roc_prev = float(roc.iloc[-2])
                    roc_ma_last = float(roc_ma.iloc[-1])
                    roc_ma_prev = float(roc_ma.iloc[-2])
                    
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
                    if (np.isnan(roc_last) or np.isnan(roc_prev) or
                        np.isnan(roc_ma_last) or np.isnan(roc_ma_prev)):
                        continue

                    if roc_last > roc_ma_last and roc_prev <= roc_ma_prev and not self.bought[s]:
                        signal = SignalEvent(self.__class__.__name__, s, dt, 'LONG', 1.0)
                        self.events.put(signal)
                        self.bought[s] = True
                    elif roc_last < roc_ma_last and roc_prev >= roc_ma_prev and self.bought[s]:
                        signal = SignalEvent(self.__class__.__name__, s, dt, 'EXIT', 1.0)
                        self.events.put(signal)
                        self.bought[s] = False
                        
                except Exception as e:
                    print(f"Error in calculate_signals for symbol {s}: {e}")
                    continue