import pandas as pd
import numpy as np
from backtest.strategy import Strategy
from backtest.event import SignalEvent

class TrixStrategy(Strategy):
    def __init__(self, data_handler, events, period=15, signal_period=9):
        self.data_handler = data_handler
        self.events = events
        self.symbol_list = self.data_handler.symbol_list
        self.period = period
        self.signal_period = signal_period
        self.bought = {s: False for s in self.symbol_list}

    def calculate_signals(self, event):
        if event.type == 'MARKET':
            for s in self.symbol_list:
                try:
                    bars = self.data_handler.get_latest_bars(s, self.period * 3)
                    if len(bars) < self.period * 3:
                        continue

                    ema1 = bars['Close'].ewm(span=self.period, adjust=False).mean()
                    ema2 = ema1.ewm(span=self.period, adjust=False).mean()
                    ema3 = ema2.ewm(span=self.period, adjust=False).mean()
                    trix = (ema3 - ema3.shift(1)) / ema3.shift(1) * 100
                    trix_signal = trix.ewm(span=self.signal_period, adjust=False).mean()
                    
                    # Extract scalar values
                    trix_last = float(trix.iloc[-1])
                    trix_prev = float(trix.iloc[-2])
                    trix_signal_last = float(trix_signal.iloc[-1])
                    trix_signal_prev = float(trix_signal.iloc[-2])
                    
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
                    if (np.isnan(trix_last) or np.isnan(trix_prev) or
                        np.isnan(trix_signal_last) or np.isnan(trix_signal_prev)):
                        continue

                    if trix_last > trix_signal_last and trix_prev <= trix_signal_prev and not self.bought[s]:
                        signal = SignalEvent(self.__class__.__name__, s, dt, 'LONG', 1.0)
                        self.events.put(signal)
                        self.bought[s] = True
                    elif trix_last < trix_signal_last and trix_prev >= trix_signal_prev and self.bought[s]:
                        signal = SignalEvent(self.__class__.__name__, s, dt, 'EXIT', 1.0)
                        self.events.put(signal)
                        self.bought[s] = False
                        
                except Exception as e:
                    print(f"Error in calculate_signals for symbol {s}: {e}")
                    continue