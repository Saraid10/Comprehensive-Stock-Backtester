import pandas as pd
import numpy as np
from backtest.strategy import Strategy
from backtest.event import SignalEvent

class VortexIndicatorStrategy(Strategy):
    def __init__(self, data_handler, events, period=14):
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

                    tr = (bars['High'] - bars['Low']).abs().combine_first((bars['High'] - bars['Close'].shift()).abs()).combine_first((bars['Low'] - bars['Close'].shift()).abs())
                    tr_sum = tr.rolling(window=self.period).sum()
                    
                    vm_plus = (bars['High'] - bars['Low'].shift()).abs()
                    vm_minus = (bars['Low'] - bars['High'].shift()).abs()
                    
                    vi_plus = vm_plus.rolling(window=self.period).sum() / tr_sum
                    vi_minus = vm_minus.rolling(window=self.period).sum() / tr_sum
                    
                    # Extract scalar values
                    vi_plus_last = float(vi_plus.iloc[-1])
                    vi_plus_prev = float(vi_plus.iloc[-2])
                    vi_minus_last = float(vi_minus.iloc[-1])
                    vi_minus_prev = float(vi_minus.iloc[-2])
                    
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
                    if (np.isnan(vi_plus_last) or np.isnan(vi_plus_prev) or
                        np.isnan(vi_minus_last) or np.isnan(vi_minus_prev)):
                        continue

                    if vi_plus_last > vi_minus_last and vi_plus_prev <= vi_minus_prev and not self.bought[s]:
                        signal = SignalEvent(self.__class__.__name__, s, dt, 'LONG', 1.0)
                        self.events.put(signal)
                        self.bought[s] = True
                    elif vi_plus_last < vi_minus_last and vi_plus_prev >= vi_minus_prev and self.bought[s]:
                        signal = SignalEvent(self.__class__.__name__, s, dt, 'EXIT', 1.0)
                        self.events.put(signal)
                        self.bought[s] = False
                        
                except Exception as e:
                    print(f"Error in calculate_signals for symbol {s}: {e}")
                    continue