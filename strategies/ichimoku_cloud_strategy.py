import pandas as pd
import numpy as np
from backtest.strategy import Strategy
from backtest.event import SignalEvent

class IchimokuCloudStrategy(Strategy):
    def __init__(self, data_handler, events, tenkan_period=9, kijun_period=26):
        self.data_handler = data_handler
        self.events = events
        self.symbol_list = self.data_handler.symbol_list
        self.tenkan_period = tenkan_period
        self.kijun_period = kijun_period
        self.bought = {s: False for s in self.symbol_list}

    def calculate_signals(self, event):
        if event.type == 'MARKET':
            for s in self.symbol_list:
                try:
                    bars = self.data_handler.get_latest_bars(s, self.kijun_period)
                    if len(bars) < self.kijun_period:
                        continue

                    tenkan_high = bars['High'].rolling(window=self.tenkan_period).max()
                    tenkan_low = bars['Low'].rolling(window=self.tenkan_period).min()
                    tenkan_sen = (tenkan_high + tenkan_low) / 2

                    kijun_high = bars['High'].rolling(window=self.kijun_period).max()
                    kijun_low = bars['Low'].rolling(window=self.kijun_period).min()
                    kijun_sen = (kijun_high + kijun_low) / 2
                    
                    # Extract scalar values
                    tenkan_sen_last = float(tenkan_sen.iloc[-1])
                    tenkan_sen_prev = float(tenkan_sen.iloc[-2])
                    kijun_sen_last = float(kijun_sen.iloc[-1])
                    kijun_sen_prev = float(kijun_sen.iloc[-2])
                    
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
                    if (np.isnan(tenkan_sen_last) or np.isnan(tenkan_sen_prev) or
                        np.isnan(kijun_sen_last) or np.isnan(kijun_sen_prev)):
                        continue

                    if tenkan_sen_last > kijun_sen_last and tenkan_sen_prev <= kijun_sen_prev and not self.bought[s]:
                        signal = SignalEvent(self.__class__.__name__, s, dt, 'LONG', 1.0)
                        self.events.put(signal)
                        self.bought[s] = True
                    elif tenkan_sen_last < kijun_sen_last and tenkan_sen_prev >= kijun_sen_prev and self.bought[s]:
                        signal = SignalEvent(self.__class__.__name__, s, dt, 'EXIT', 1.0)
                        self.events.put(signal)
                        self.bought[s] = False
                        
                except Exception as e:
                    print(f"Error in calculate_signals for symbol {s}: {e}")
                    continue