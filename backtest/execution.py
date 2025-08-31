from backtest.event import FillEvent, OrderEvent

class ExecutionHandler:
    def execute_order(self, event):
        raise NotImplementedError("Should implement execute_order()")

class SimulatedExecutionHandler(ExecutionHandler):
    def __init__(self, events, data_handler):
        self.events = events
        self.data_handler = data_handler

    def execute_order(self, event):
        if event.type == 'ORDER':
            # Use the new, safer function to get the close price
            fill_price = self.data_handler.get_latest_bar_value(event.symbol, 'Close')
            if fill_price is not None:
                timeindex = self.data_handler.get_latest_bar(event.symbol).index[0]
                fill_cost = fill_price * event.quantity
                fill_event = FillEvent(timeindex, event.symbol, 'ARCA', event.quantity, event.direction, fill_cost)
                self.events.put(fill_event)
