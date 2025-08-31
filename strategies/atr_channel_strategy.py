import pandas as pd
import numpy as np
from backtest.strategy import Strategy
from backtest.event import SignalEvent

class ATRChannelStrategy(Strategy):
    def __init__(self, data_handler, events, sma_period=20, atr_period=14, atr_multiplier=2.0):
        self.data_handler = data_handler
        self.events = events
        self.symbol_list = self.data_handler.symbol_list
        self.sma_period = sma_period
        self.atr_period = atr_period
        self.atr_multiplier = atr_multiplier
        self.bought = self._calculate_initial_bought()

    def _calculate_initial_bought(self):
        return {s: False for s in self.symbol_list}

    def calculate_signals(self, event):
        if event.type == 'MARKET':
            for s in self.symbol_list:
                try:
                    bars = self.data_handler.get_latest_bars(s, self.sma_period)
                    if len(bars) < self.sma_period:
                        continue

                    high_low = bars['High'] - bars['Low']
                    high_close = np.abs(bars['High'] - bars['Close'].shift())
                    low_close = np.abs(bars['Low'] - bars['Close'].shift())
                    ranges = pd.concat([high_low, high_close, low_close], axis=1)
                    true_range = np.max(ranges, axis=1)
                    atr = true_range.ewm(alpha=1/self.atr_period, adjust=False).mean()

                    sma = bars['Close'].rolling(window=self.sma_period).mean()
                    
                    # Extract scalar values
                    atr_last = float(atr.iloc[-1])
                    sma_last = float(sma.iloc[-1])
                    upper_channel = sma_last + (atr_last * self.atr_multiplier)
                    
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
                    
                    price = self.data_handler.get_latest_bar_value(s, 'Close')
                    
                    # Check for NaN values
                    if np.isnan(upper_channel) or np.isnan(price):
                        continue

                    if price > upper_channel and not self.bought[s]:
                        signal = SignalEvent(self.__class__.__name__, s, dt, 'LONG', 1.0)
                        self.events.put(signal)
                        self.bought[s] = True
                        
                except Exception as e:
                    print(f"Error in calculate_signals for symbol {s}: {e}")
                    continue