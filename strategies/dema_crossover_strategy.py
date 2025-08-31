import pandas as pd
import numpy as np
from backtest.strategy import Strategy
from backtest.event import SignalEvent

class DEMACrossoverStrategy(Strategy):
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
    
    def calculate_dema(self, data, window):
        ema1 = data.ewm(span=window, adjust=False).mean()
        ema2 = ema1.ewm(span=window, adjust=False).mean()
        dema = 2 * ema1 - ema2
        return dema

    def calculate_signals(self, event):
        if event.type == 'MARKET':
            for s in self.symbol_list:
                try:
                    # Get the necessary bars
                    bars = self.data_handler.get_latest_bars(s, self.long_window)
                    if len(bars) < self.long_window:
                        continue
                    
                    # Calculate DEMAs
                    short_dema = self.calculate_dema(bars['Close'], self.short_window)
                    long_dema = self.calculate_dema(bars['Close'], self.long_window)
                    
                    # Extract scalar values
                    short_dema_last = float(short_dema.iloc[-1])
                    short_dema_prev = float(short_dema.iloc[-2])
                    long_dema_last = float(long_dema.iloc[-1])
                    long_dema_prev = float(long_dema.iloc[-2])
                    
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
                    if (np.isnan(short_dema_last) or np.isnan(short_dema_prev) or 
                        np.isnan(long_dema_last) or np.isnan(long_dema_prev)):
                        continue
                    
                    # Buy signal: short DEMA crosses above long DEMA
                    if short_dema_last > long_dema_last and short_dema_prev <= long_dema_prev:
                        if not self.bought[s]:
                            signal = SignalEvent(self.__class__.__name__, s, dt, 'LONG', 1.0)
                            self.events.put(signal)
                            self.bought[s] = True
                    
                    # Sell signal: short DEMA crosses below long DEMA
                    elif short_dema_last < long_dema_last and short_dema_prev >= long_dema_prev:
                        if self.bought[s]:
                            signal = SignalEvent(self.__class__.__name__, s, dt, 'EXIT', 1.0)
                            self.events.put(signal)
                            self.bought[s] = False
                            
                except Exception as e:
                    print(f"Error in calculate_signals for symbol {s}: {e}")
                    continue