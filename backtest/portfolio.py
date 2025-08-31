import pandas as pd
from backtest.event import OrderEvent

class Portfolio:
    def __init__(self, data_handler, events, start_date, initial_capital=100000.0, position_size=0.02):
        self.data_handler = data_handler
        self.events = events
        self.symbol_list = data_handler.symbol_list
        self.start_date = pd.to_datetime(start_date)
        self.initial_capital = float(initial_capital)  # Force to float
        self.position_size = float(position_size)  # Position size as percentage of portfolio (default 2%)

        self.all_positions = self._construct_all_positions()
        self.current_positions = {s: 0.0 for s in self.symbol_list}

        self.all_holdings = self._construct_all_holdings()
        self.current_holdings = self._construct_current_holdings()

        self.equity_curve = None

    def _construct_all_positions(self):
        d = {s: 0 for s in self.symbol_list}
        d['datetime'] = self.start_date
        return [d]

    def _construct_all_holdings(self):
        d = {s: 0.0 for s in self.symbol_list}
        d['datetime'] = self.start_date
        d['cash'] = self.initial_capital
        d['commission'] = 0.0
        d['total'] = self.initial_capital
        return [d]

    def _construct_current_holdings(self):
        d = {s: 0.0 for s in self.symbol_list}
        d['cash'] = self.initial_capital
        d['commission'] = 0.0
        d['total'] = self.initial_capital
        return d

    def update_timeindex(self, event):
        latest_datetime = self.data_handler.get_latest_bar(self.symbol_list[0]).index[0]

        dp = {s: self.current_positions[s] for s in self.symbol_list}
        dp['datetime'] = latest_datetime
        self.all_positions.append(dp)

        dh = {s: 0.0 for s in self.symbol_list}
        dh['datetime'] = latest_datetime
        dh['cash'] = self.current_holdings['cash']
        dh['commission'] = self.current_holdings['commission']
        dh['total'] = self.current_holdings['cash']

        for s in self.symbol_list:
            close_price = self.data_handler.get_latest_bar_value(s, 'Close')
            if close_price is not None:
                # Force everything to a basic Python float
                market_value = float(self.current_positions[s]) * float(close_price)
                dh[s] = market_value
                dh['total'] = float(dh['total']) + market_value

        self.all_holdings.append(dh)

    def update_positions_from_fill(self, fill):
        fill_dir = 1 if fill.direction == 'BUY' else -1
        self.current_positions[fill.symbol] += fill_dir * fill.quantity

    def update_holdings_from_fill(self, fill):
        fill_dir = 1 if fill.direction == 'BUY' else -1
        # Force everything to a basic Python float
        cost = float(fill_dir) * float(fill.fill_cost)
        self.current_holdings[fill.symbol] += cost
        self.current_holdings['commission'] += float(fill.commission)
        self.current_holdings['cash'] -= (cost + float(fill.commission))
        self.current_holdings['total'] -= float(fill.commission)

    def update_fill(self, event):
        if event.type == 'FILL':
            self.update_positions_from_fill(event)
            self.update_holdings_from_fill(event)

    def generate_naive_order(self, signal):
        order = None
        symbol = signal.symbol
        direction = signal.signal_type
        
        # Get the current price of the stock
        price = self.data_handler.get_latest_bar_value(symbol, 'Close')
        
        # Fix for Series vs scalar value issue - handle pandas Series properly
        # If price is a pandas Series, get its first value
        if hasattr(price, 'iloc'):
            try:
                price = price.iloc[-1]  # Get the last value in the Series
            except:
                # If any issues, try another approach
                try:
                    price = float(price)
                except:
                    price = None
                    
        # Now check if price is valid
        if price is None or pd.isna(price) or float(price) <= 0:
            return None
            
        # Ensure price is a float
        price = float(price)
            
        # Calculate total portfolio value
        portfolio_value = float(self.current_holdings['total'])
        
        # Calculate order size based on position sizing
        # Use a percentage of the portfolio for each position
        capital_per_trade = portfolio_value * self.position_size
        
        # Calculate quantity, ensuring it's an integer
        mkt_quantity = int(capital_per_trade / price)
        
        # Ensure we buy at least 1 share, but don't exceed what we can afford
        available_cash = float(self.current_holdings['cash'])
        max_affordable = int(available_cash / price)
        mkt_quantity = max(1, min(mkt_quantity, max_affordable))
        
        cur_quantity = self.current_positions[symbol]
        order_type = 'MKT'

        if direction == 'LONG' and cur_quantity == 0:
            order = OrderEvent(symbol, order_type, mkt_quantity, 'BUY')
        elif direction == 'EXIT' and cur_quantity > 0:
            order = OrderEvent(symbol, order_type, abs(cur_quantity), 'SELL')
        return order

    def update_signal(self, event):
        if event.type == 'SIGNAL':
            order_event = self.generate_naive_order(event)
            if order_event:
                self.events.put(order_event)

    def create_equity_curve_dataframe(self):
        curve = pd.DataFrame(self.all_holdings)
        curve.set_index('datetime', inplace=True)
        # Ensure the 'total' column is numeric before calculations
        curve['total'] = pd.to_numeric(curve['total'], errors='coerce')
        curve.dropna(subset=['total'], inplace=True)
        
        curve['returns'] = curve['total'].pct_change()
        curve['equity_curve'] = (1.0 + curve['returns']).cumprod()
        self.equity_curve = curve