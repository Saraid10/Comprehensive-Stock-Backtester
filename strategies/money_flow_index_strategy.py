import pandas as pd
import numpy as np
from backtest.strategy import Strategy
from backtest.event import SignalEvent

class MoneyFlowIndexStrategy(Strategy):
    def __init__(self, data_handler, events, period=14, oversold=20, overbought=80):
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
                    bars = self.data_handler.get_latest_bars(s, self.period + 1)
                    if len(bars) < self.period + 1:
                        continue

                    typical_price = (bars['High'] + bars['Low'] + bars['Close']) / 3
                    raw_money_flow = typical_price * bars['Volume']
                    
                    mf_sign = np.sign(typical_price.diff(1))
                    positive_mf = np.where(mf_sign > 0, raw_money_flow, 0)
                    negative_mf = np.where(mf_sign < 0, raw_money_flow, 0)

                    positive_mf_sum = pd.Series(positive_mf).rolling(window=self.period).sum()
                    negative_mf_sum = pd.Series(negative_mf).rolling(window=self.period).sum()

                    money_ratio = positive_mf_sum / negative_mf_sum
                    mfi = 100 - (100 / (1 + money_ratio))
                    
                    # Extract scalar value
                    mfi_last = float(mfi.iloc[-1])
                    
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
                    if np.isnan(mfi_last):
                        continue

                    if mfi_last < self.oversold and not self.bought[s]:
                        signal = SignalEvent(self.__class__.__name__, s, dt, 'LONG', 1.0)
                        self.events.put(signal)
                        self.bought[s] = True
                    elif mfi_last > self.overbought and self.bought[s]:
                        signal = SignalEvent(self.__class__.__name__, s, dt, 'EXIT', 1.0)
                        self.events.put(signal)
                        self.bought[s] = False
                        
                except Exception as e:
                    print(f"Error in calculate_signals for symbol {s}: {e}")
                    continue