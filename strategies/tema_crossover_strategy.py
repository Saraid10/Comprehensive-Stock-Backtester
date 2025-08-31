import pandas as pd
import numpy as np
from backtest.strategy import Strategy
from backtest.event import SignalEvent

class TEMACrossoverStrategy(Strategy):
    def __init__(self, data_handler, events, short_window=50, long_window=200, short_period=None, long_period=None):
        self.data_handler = data_handler
        self.events = events
        self.symbol_list = self.data_handler.symbol_list
        
        # Accept either window or period naming convention
        self.short_window = short_period if short_period is not None else short_window
        self.long_window = long_period if long_period is not None else long_window
        
        self.bought = self._calculate_initial_bought()

    def _calculate_initial_bought(self):
        bought = {}
        for s in self.symbol_list:
            bought[s] = False
        return bought
    
    def calculate_tema(self, data, window):
        # Triple Exponential Moving Average
        ema1 = data.ewm(span=window, adjust=False).mean()
        ema2 = ema1.ewm(span=window, adjust=False).mean()
        ema3 = ema2.ewm(span=window, adjust=False).mean()
        tema = 3 * ema1 - 3 * ema2 + ema3
        return tema

    def calculate_signals(self, event):
        if event.type == 'MARKET':
            for s in self.symbol_list:
                try:
                    # Get the necessary bars
                    bars = self.data_handler.get_latest_bars(s, self.long_window)
                    if len(bars) < self.long_window:
                        continue
                    
                    # Calculate TEMAs
                    short_tema = self.calculate_tema(bars['Close'], self.short_window)
                    long_tema = self.calculate_tema(bars['Close'], self.long_window)
                    
                    # Extract scalar values
                    short_tema_last = float(short_tema.iloc[-1])
                    short_tema_prev = float(short_tema.iloc[-2])
                    long_tema_last = float(long_tema.iloc[-1])
                    long_tema_prev = float(long_tema.iloc[-2])
                    
                    # Get datetime
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
                    if (np.isnan(short_tema_last) or np.isnan(short_tema_prev) or 
                        np.isnan(long_tema_last) or np.isnan(long_tema_prev)):
                        continue
                    
                    # Buy signal: short TEMA crosses above long TEMA
                    if short_tema_last > long_tema_last and short_tema_prev <= long_tema_prev:
                        if not self.bought[s]:
                            signal = SignalEvent(self.__class__.__name__, s, dt, 'LONG', 1.0)
                            self.events.put(signal)
                            self.bought[s] = True
                    
                    # Sell signal: short TEMA crosses below long TEMA
                    elif short_tema_last < long_tema_last and short_tema_prev >= long_tema_prev:
                        if self.bought[s]:
                            signal = SignalEvent(self.__class__.__name__, s, dt, 'EXIT', 1.0)
                            self.events.put(signal)
                            self.bought[s] = False
                            
                except Exception as e:
                    print(f"Error in calculate_signals for symbol {s}: {e}")
                    continue