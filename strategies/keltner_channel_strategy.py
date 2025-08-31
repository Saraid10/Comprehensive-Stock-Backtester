import pandas as pd
import numpy as np
from backtest.strategy import Strategy
from backtest.event import SignalEvent

class KeltnerChannelStrategy(Strategy):
    def __init__(self, data_handler, events, ema_period=20, atr_period=10, atr_multiplier=2.0):
        self.data_handler = data_handler
        self.events = events
        self.symbol_list = self.data_handler.symbol_list
        self.ema_period = ema_period
        self.atr_period = atr_period
        self.atr_multiplier = atr_multiplier
        self.bought = {s: False for s in self.symbol_list}

    def calculate_signals(self, event):
        if event.type == 'MARKET':
            for s in self.symbol_list:
                try:
                    bars = self.data_handler.get_latest_bars(s, self.ema_period)
                    if len(bars) < self.ema_period:
                        continue

                    high_low = bars['High'] - bars['Low']
                    high_close = np.abs(bars['High'] - bars['Close'].shift())
                    low_close = np.abs(bars['Low'] - bars['Close'].shift())
                    ranges = pd.concat([high_low, high_close, low_close], axis=1)
                    true_range = np.max(ranges, axis=1)
                    
                    # Extract scalar values
                    atr = float(true_range.ewm(alpha=1/self.atr_period, adjust=False).mean().iloc[-1])
                    middle_line = float(bars['Close'].ewm(span=self.ema_period, adjust=False).mean().iloc[-1])
                    upper_channel = middle_line + (atr * self.atr_multiplier)
                    
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
                    if np.isnan(upper_channel) or np.isnan(middle_line) or np.isnan(price):
                        continue

                    if price > upper_channel and not self.bought[s]:
                        signal = SignalEvent(self.__class__.__name__, s, dt, 'LONG', 1.0)
                        self.events.put(signal)
                        self.bought[s] = True
                    elif price < middle_line and self.bought[s]:
                        signal = SignalEvent(self.__class__.__name__, s, dt, 'EXIT', 1.0)
                        self.events.put(signal)
                        self.bought[s] = False
                        
                except Exception as e:
                    print(f"Error in calculate_signals for symbol {s}: {e}")
                    continue