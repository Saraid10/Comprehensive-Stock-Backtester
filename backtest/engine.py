from queue import Empty # <--- THIS LINE IS ADDED
from backtest.event import FillEvent, OrderEvent

class Backtest:
    def __init__(self, data_handler, strategy, portfolio, execution_handler):
        self.data_handler = data_handler
        self.strategy = strategy
        self.portfolio = portfolio
        self.execution_handler = execution_handler
        self.events = data_handler.events
        self.trade_log = []

    def _run_backtest(self):
        while True:
            self.data_handler.update_bars()
            if not self.data_handler.continue_backtest:
                break

            while True:
                try:
                    event = self.events.get(False)
                except Empty: # <--- THIS LINE IS CHANGED
                    break
                else:
                    if event.type == 'MARKET':
                        self.strategy.calculate_signals(event)
                        self.portfolio.update_timeindex(event)
                    elif event.type == 'SIGNAL':
                        self.portfolio.update_signal(event)
                    elif event.type == 'ORDER':
                        self.execution_handler.execute_order(event)
                    elif event.type == 'FILL':
                        self.portfolio.update_fill(event)
                        self.trade_log.append(vars(event))

    def simulate_trading(self):
        self._run_backtest()
        self.portfolio.create_equity_curve_dataframe()
        return self.portfolio.equity_curve, self.trade_log