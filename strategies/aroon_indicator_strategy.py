import pandas as pd
import numpy as np
from backtest.strategy import Strategy
from backtest.event import SignalEvent

class AroonIndicatorStrategy(Strategy):
    """
    A trend-following strategy using the Aroon Indicator.
    A buy signal is generated when Aroon Up crosses above Aroon Down.
    An exit signal is generated when Aroon Down crosses above Aroon Up.
    """
    def __init__(self, data_handler, events, period=25):
        self.data_handler = data_handler
        self.events = events
        self.symbol_list = self.data_handler.symbol_list
        self.period = period
        self.bought = self._calculate_initial_bought()

    def _calculate_initial_bought(self):
        bought = {}
        for s in self.symbol_list:
            bought[s] = False
        return bought

    def calculate_signals(self, event):
        if event.type == 'MARKET':
            for s in self.symbol_list:
                try:
                    bars = self.data_handler.get_latest_bars(s, self.period + 1)
                    if len(bars) < self.period + 1:
                        continue

                    high_series = bars['High']
                    low_series = bars['Low']

                    aroon_up = (high_series.rolling(window=self.period).apply(np.argmax, raw=True) / self.period) * 100
                    aroon_down = (low_series.rolling(window=self.period).apply(np.argmin, raw=True) / self.period) * 100
                    
                    # Extract scalar values
                    aroon_up_last = float(aroon_up.iloc[-1])
                    aroon_down_last = float(aroon_down.iloc[-1])
                    
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
                    if np.isnan(aroon_up_last) or np.isnan(aroon_down_last):
                        continue

                    if aroon_up_last > aroon_down_last and not self.bought[s]:
                        signal = SignalEvent(self.__class__.__name__, s, dt, 'LONG', 1.0)
                        self.events.put(signal)
                        self.bought[s] = True
                    elif aroon_up_last < aroon_down_last and self.bought[s]:
                        signal = SignalEvent(self.__class__.__name__, s, dt, 'EXIT', 1.0)
                        self.events.put(signal)
                        self.bought[s] = False
                        
                except Exception as e:
                    print(f"Error in calculate_signals for symbol {s}: {e}")
                    continue