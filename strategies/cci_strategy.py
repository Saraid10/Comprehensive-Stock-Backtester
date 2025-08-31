import pandas as pd
import numpy as np
from backtest.strategy import Strategy
from backtest.event import SignalEvent

class CCIStrategy(Strategy):
    def __init__(self, data_handler, events, period=20, oversold=-100, overbought=100):
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
                    
                    tp = (bars['High'] + bars['Low'] + bars['Close']) / 3
                    sma_tp = tp.rolling(window=self.period).mean()
                    mean_dev = tp.rolling(window=self.period).apply(lambda x: np.abs(x - x.mean()).mean())
                    cci = (tp - sma_tp) / (0.015 * mean_dev)
                    
                    # Extract scalar values
                    cci_last = float(cci.iloc[-1])
                    cci_prev = float(cci.iloc[-2])
                    
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
                    if np.isnan(cci_last) or np.isnan(cci_prev):
                        continue

                    if cci_last > self.oversold and cci_prev <= self.oversold and not self.bought[s]:
                        signal = SignalEvent(self.__class__.__name__, s, dt, 'LONG', 1.0)
                        self.events.put(signal)
                        self.bought[s] = True
                    elif cci_last < self.overbought and cci_prev >= self.overbought and self.bought[s]:
                        signal = SignalEvent(self.__class__.__name__, s, dt, 'EXIT', 1.0)
                        self.events.put(signal)
                        self.bought[s] = False
                        
                except Exception as e:
                    print(f"Error in calculate_signals for symbol {s}: {e}")
                    continue