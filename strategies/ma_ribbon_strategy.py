import pandas as pd
import numpy as np
from backtest.strategy import Strategy
from backtest.event import SignalEvent

class MARibbonStrategy(Strategy):
    def __init__(self, data_handler, events, short_period=5, medium_period=10, long_period=20):
        self.data_handler = data_handler
        self.events = events
        self.symbol_list = self.data_handler.symbol_list
        self.short_period = short_period
        self.medium_period = medium_period
        self.long_period = long_period
        self.bought = {s: False for s in self.symbol_list}

    def calculate_signals(self, event):
        if event.type == 'MARKET':
            for s in self.symbol_list:
                try:
                    bars = self.data_handler.get_latest_bars(s, self.long_period)
                    if len(bars) < self.long_period:
                        continue

                    short_ma = bars['Close'].rolling(window=self.short_period).mean()
                    medium_ma = bars['Close'].rolling(window=self.medium_period).mean()
                    long_ma = bars['Close'].rolling(window=self.long_period).mean()
                    
                    # Extract scalar values
                    short_ma_last = float(short_ma.iloc[-1])
                    short_ma_prev = float(short_ma.iloc[-2])
                    medium_ma_last = float(medium_ma.iloc[-1])
                    medium_ma_prev = float(medium_ma.iloc[-2])
                    long_ma_last = float(long_ma.iloc[-1])
                    
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
                    if (np.isnan(short_ma_last) or np.isnan(short_ma_prev) or
                        np.isnan(medium_ma_last) or np.isnan(medium_ma_prev) or
                        np.isnan(long_ma_last)):
                        continue
                    
                    trend_up = medium_ma_last > long_ma_last
                    buy_crossover = short_ma_last > medium_ma_last and short_ma_prev <= medium_ma_prev
                    sell_crossover = short_ma_last < medium_ma_last and short_ma_prev >= medium_ma_prev

                    if buy_crossover and trend_up and not self.bought[s]:
                        signal = SignalEvent(self.__class__.__name__, s, dt, 'LONG', 1.0)
                        self.events.put(signal)
                        self.bought[s] = True
                    elif sell_crossover and self.bought[s]:
                        signal = SignalEvent(self.__class__.__name__, s, dt, 'EXIT', 1.0)
                        self.events.put(signal)
                        self.bought[s] = False
                        
                except Exception as e:
                    print(f"Error in calculate_signals for symbol {s}: {e}")
                    continue