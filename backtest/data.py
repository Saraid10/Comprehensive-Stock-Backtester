import pandas as pd
from backtest.event import MarketEvent

class DataHandler:
    def get_latest_bar(self, symbol):
        raise NotImplementedError("Should implement get_latest_bar()")
    def get_latest_bars(self, symbol, N=1):
        raise NotImplementedError("Should implement get_latest_bars()")
    def get_latest_bar_value(self, symbol, val_type):
        raise NotImplementedError("Should implement get_latest_bar_value()")
    def update_bars(self):
        raise NotImplementedError("Should implement update_bars()")

class HistoricDataHandler(DataHandler):
    def __init__(self, events, symbol_list, data):
        self.events = events
        self.symbol_list = symbol_list
        # Ensure the data index is datetime
        data.index = pd.to_datetime(data.index)
        self.symbol_data = {s: data for s in self.symbol_list}
        self.latest_symbol_data = {s: pd.DataFrame() for s in self.symbol_list}
        self.data_stream = self._create_data_stream()
        self.continue_backtest = True

    def _create_data_stream(self):
        # Assuming single symbol data for simplicity
        return self.symbol_data[self.symbol_list[0]].iterrows()

    def update_bars(self):
        try:
            index, row = next(self.data_stream)
            for s in self.symbol_list:
                df_row = pd.DataFrame([row], index=[index])
                # Use concat instead of append for performance and future compatibility
                self.latest_symbol_data[s] = pd.concat([self.latest_symbol_data[s], df_row])
            self.events.put(MarketEvent())
        except StopIteration:
            self.continue_backtest = False

    def get_latest_bar(self, symbol):
        return self.latest_symbol_data[symbol].iloc[-1:]

    def get_latest_bars(self, symbol, N=1):
        return self.latest_symbol_data[symbol].tail(N)

    def get_latest_bar_value(self, symbol, val_type):
        """
        Returns the latest value for a given bar component (e.g., 'Close').
        """
        if len(self.latest_symbol_data[symbol]) > 0:
            return self.latest_symbol_data[symbol][val_type].iloc[-1]
        return None