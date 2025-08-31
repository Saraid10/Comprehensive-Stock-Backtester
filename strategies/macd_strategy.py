import pandas as pd
import numpy as np
from backtest.strategy import Strategy
from backtest.event import SignalEvent

class MACDStrategy(Strategy):
    def __init__(self, data_handler, events, short_ema_period=12, long_ema_period=26, signal_ema_period=9):
        self.data_handler = data_handler
        self.events = events
        self.symbol_list = self.data_handler.symbol_list
        self.short_ema_period = short_ema_period
        self.long_ema_period = long_ema_period
        self.signal_ema_period = signal_ema_period
        self.bought = {s: False for s in self.symbol_list}

    def calculate_signals(self, event):
        if event.type == 'MARKET':
            for s in self.symbol_list:
                try:
                    bars = self.data_handler.get_latest_bars(s, self.long_ema_period + self.signal_ema_period)
                    if len(bars) < self.long_ema_period:
                        continue

                    short_ema = bars['Close'].ewm(span=self.short_ema_period, adjust=False).mean()
                    long_ema = bars['Close'].ewm(span=self.long_ema_period, adjust=False).mean()
                    macd_line = short_ema - long_ema
                    signal_line = macd_line.ewm(span=self.signal_ema_period, adjust=False).mean()
                    
                    # Extract scalar values
                    macd_line_last = float(macd_line.iloc[-1])
                    macd_line_prev = float(macd_line.iloc[-2])
                    signal_line_last = float(signal_line.iloc[-1])
                    signal_line_prev = float(signal_line.iloc[-2])
                    
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
                    if (np.isnan(macd_line_last) or np.isnan(macd_line_prev) or
                        np.isnan(signal_line_last) or np.isnan(signal_line_prev)):
                        continue

                    if macd_line_last > signal_line_last and macd_line_prev <= signal_line_prev and not self.bought[s]:
                        signal = SignalEvent(self.__class__.__name__, s, dt, 'LONG', 1.0)
                        self.events.put(signal)
                        self.bought[s] = True
                    elif macd_line_last < signal_line_last and macd_line_prev >= signal_line_prev and self.bought[s]:
                        signal = SignalEvent(self.__class__.__name__, s, dt, 'EXIT', 1.0)
                        self.events.put(signal)
                        self.bought[s] = False
                        
                except Exception as e:
                    print(f"Error in calculate_signals for symbol {s}: {e}")
                    continue