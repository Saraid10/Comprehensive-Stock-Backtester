import pandas as pd
import numpy as np
from backtest.strategy import Strategy
from backtest.event import SignalEvent

class SMACrossoverStrategy(Strategy):
    def __init__(self, data_handler, events, short_window=50, long_window=200):
        self.data_handler = data_handler
        self.events = events
        self.symbol_list = self.data_handler.symbol_list
        self.short_window = short_window
        self.long_window = long_window
        self.bought = self._calculate_initial_bought()
        # Add debug counter
        self.debug_count = 0

    def _calculate_initial_bought(self):
        bought = {}
        for s in self.symbol_list:
            bought[s] = False
        return bought

    def calculate_signals(self, event):
        if event.type == 'MARKET':
            for s in self.symbol_list:
                try:
                    bars = self.data_handler.get_latest_bars(s, self.long_window)
                    if len(bars) < self.long_window:
                        continue
                    
                    short_sma = bars['Close'].rolling(window=self.short_window).mean()
                    long_sma = bars['Close'].rolling(window=self.long_window).mean()
                    
                    # Add debug print to see what's happening
                    self.debug_count += 1
                    if self.debug_count % 10 == 0:  # Print every 10th check to avoid flooding logs
                        print(f"DEBUG - Symbol: {s}, Latest bar date: {bars.index[-1]}")
                        print(f"Short SMA: {short_sma.iloc[-1]}, Long SMA: {long_sma.iloc[-1]}")
                    
                    # Get datetime safely
                    latest_bar = self.data_handler.get_latest_bar(s)
                    if latest_bar is None or latest_bar.empty:
                        continue
                    
                    dt = latest_bar.index[0]
                    
                    # Extract scalar values but with less restrictive NaN handling
                    # Only check the current values, not previous ones
                    short_sma_last = float(short_sma.iloc[-1]) if not pd.isna(short_sma.iloc[-1]) else None
                    long_sma_last = float(long_sma.iloc[-1]) if not pd.isna(long_sma.iloc[-1]) else None
                    
                    if short_sma_last is None or long_sma_last is None:
                        continue
                        
                    short_sma_prev = float(short_sma.iloc[-2]) if not pd.isna(short_sma.iloc[-2]) else short_sma_last
                    long_sma_prev = float(long_sma.iloc[-2]) if not pd.isna(long_sma.iloc[-2]) else long_sma_last

                    # Buy signal: short SMA crosses above long SMA
                    if short_sma_last > long_sma_last and short_sma_prev <= long_sma_prev:
                        if not self.bought[s]:
                            print(f"GENERATE BUY SIGNAL for {s} at {dt}")
                            signal = SignalEvent(self.__class__.__name__, s, dt, 'LONG', 1.0)
                            self.events.put(signal)
                            self.bought[s] = True
                    
                    # Sell signal: short SMA crosses below long SMA
                    elif short_sma_last < long_sma_last and short_sma_prev >= long_sma_prev:
                        if self.bought[s]:
                            print(f"GENERATE SELL SIGNAL for {s} at {dt}")
                            signal = SignalEvent(self.__class__.__name__, s, dt, 'EXIT', 1.0)
                            self.events.put(signal)
                            self.bought[s] = False
                            
                except Exception as e:
                    print(f"Error in calculate_signals for symbol {s}: {e}")
                    continue