import pandas as pd
import numpy as np
from backtest.strategy import Strategy
from backtest.event import SignalEvent

class VWAPCrossoverStrategy(Strategy):
    def __init__(self, data_handler, events, vwap_ma_period=20):
        self.data_handler = data_handler
        self.events = events
        self.symbol_list = self.data_handler.symbol_list
        self.vwap_ma_period = vwap_ma_period
        self.bought = {s: False for s in self.symbol_list}

    def calculate_signals(self, event):
        if event.type == 'MARKET':
            for s in self.symbol_list:
                try:
                    bars = self.data_handler.get_latest_bars(s, self.vwap_ma_period)
                    if len(bars) < self.vwap_ma_period:
                        continue

                    # This is a simplification for daily bars. A true intraday VWAP is different.
                    q = bars['Volume'] * (bars['High'] + bars['Low'] + bars['Close']) / 3
                    vwap = q.cumsum() / bars['Volume'].cumsum()
                    vwap_ma = vwap.rolling(window=self.vwap_ma_period).mean()
                    
                    # Extract scalar values
                    vwap_last = float(vwap.iloc[-1])
                    vwap_prev = float(vwap.iloc[-2])
                    vwap_ma_last = float(vwap_ma.iloc[-1])
                    vwap_ma_prev = float(vwap_ma.iloc[-2])
                    
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
                    if (np.isnan(vwap_last) or np.isnan(vwap_prev) or
                        np.isnan(vwap_ma_last) or np.isnan(vwap_ma_prev)):
                        continue

                    if vwap_last > vwap_ma_last and vwap_prev <= vwap_ma_prev and not self.bought[s]:
                        signal = SignalEvent(self.__class__.__name__, s, dt, 'LONG', 1.0)
                        self.events.put(signal)
                        self.bought[s] = True
                    elif vwap_last < vwap_ma_last and vwap_prev >= vwap_ma_prev and self.bought[s]:
                        signal = SignalEvent(self.__class__.__name__, s, dt, 'EXIT', 1.0)
                        self.events.put(signal)
                        self.bought[s] = False
                        
                except Exception as e:
                    print(f"Error in calculate_signals for symbol {s}: {e}")
                    continue