import pandas as pd
import numpy as np
from backtest.strategy import Strategy
from backtest.event import SignalEvent

class OnBalanceVolumeStrategy(Strategy):
    def __init__(self, data_handler, events, obv_ma_period=20):
        self.data_handler = data_handler
        self.events = events
        self.symbol_list = self.data_handler.symbol_list
        self.obv_ma_period = obv_ma_period
        self.bought = {s: False for s in self.symbol_list}

    def calculate_signals(self, event):
        if event.type == 'MARKET':
            for s in self.symbol_list:
                try:
                    bars = self.data_handler.get_latest_bars(s, self.obv_ma_period + 1)
                    if len(bars) < self.obv_ma_period + 1:
                        continue
                    
                    obv = (np.sign(bars['Close'].diff()) * bars['Volume']).fillna(0).cumsum()
                    obv_ma = obv.rolling(window=self.obv_ma_period).mean()
                    
                    # Extract scalar values
                    obv_last = float(obv.iloc[-1])
                    obv_prev = float(obv.iloc[-2])
                    obv_ma_last = float(obv_ma.iloc[-1])
                    obv_ma_prev = float(obv_ma.iloc[-2])
                    
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
                    if (np.isnan(obv_last) or np.isnan(obv_prev) or
                        np.isnan(obv_ma_last) or np.isnan(obv_ma_prev)):
                        continue

                    if obv_last > obv_ma_last and obv_prev <= obv_ma_prev and not self.bought[s]:
                        signal = SignalEvent(self.__class__.__name__, s, dt, 'LONG', 1.0)
                        self.events.put(signal)
                        self.bought[s] = True
                    elif obv_last < obv_ma_last and obv_prev >= obv_ma_prev and self.bought[s]:
                        signal = SignalEvent(self.__class__.__name__, s, dt, 'EXIT', 1.0)
                        self.events.put(signal)
                        self.bought[s] = False
                        
                except Exception as e:
                    print(f"Error in calculate_signals for symbol {s}: {e}")
                    continue