from backtest.strategy import Strategy
from backtest.event import SignalEvent

class BuyAndHoldStrategy(Strategy):
    """
    A simple strategy that buys on the first market event and holds.
    """
    def __init__(self, data_handler, events):
        self.data_handler = data_handler
        self.events = events
        self.symbol_list = self.data_handler.symbol_list
        self.bought = {s: False for s in self.symbol_list}

    def calculate_signals(self, event):
        if event.type == 'MARKET':
            for s in self.symbol_list:
                if not self.bought[s]:
                    dt = self.data_handler.get_latest_bar(s).index[0]
                    signal = SignalEvent(self.__class__.__name__, s, dt, 'LONG', 1.0)
                    self.events.put(signal)
                    self.bought[s] = True