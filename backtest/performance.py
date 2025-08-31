import numpy as np
import pandas as pd

def calculate_sharpe_ratio(returns, risk_free_rate=0.0):
    trading_days = 252
    # Check if standard deviation is zero or NaN
    if returns.std() == 0 or pd.isna(returns.std()):
        return 0.0

    excess_returns = returns - (risk_free_rate / trading_days)
    # Check again after calculating excess returns
    if excess_returns.std() == 0 or pd.isna(excess_returns.std()):
        return 0.0
        
    sharpe_ratio = np.sqrt(trading_days) * (excess_returns.mean() / excess_returns.std())
    # Handle potential NaN or Inf results
    if pd.isna(sharpe_ratio) or np.isinf(sharpe_ratio):
        return 0.0
    return sharpe_ratio

def calculate_max_drawdown(equity_curve_total):
    # The input 'equity_curve_total' is a pandas Series (the 'total' column)
    
    # NEW, MORE ROBUST CHECK:
    # If the standard deviation is 0, the line is flat (no trades), so drawdown is 0.
    if equity_curve_total.std() == 0:
        return 0.0
        
    running_max = equity_curve_total.cummax()
    drawdown = (equity_curve_total - running_max) / running_max
    max_drawdown = drawdown.min()
    
    # Handle case where drawdown might be NaN
    if pd.isna(max_drawdown):
        return 0.0
    return max_drawdown * 100

def get_performance_metrics(equity_curve, trade_log, initial_capital):
    # Check for empty or invalid equity curve
    if equity_curve is None or equity_curve.empty or 'total' not in equity_curve.columns:
        return {
            "Total Return": 0.0,
            "Net Profit": 0.0,
            "Max Drawdown": 0.0,
            "Sharpe Ratio": 0.0,
            "Total Trades": 0
        }

    total_return = (equity_curve['total'].iloc[-1] / initial_capital) - 1
    net_profit = equity_curve['total'].iloc[-1] - initial_capital
    max_drawdown = calculate_max_drawdown(equity_curve['total'])
    sharpe_ratio = calculate_sharpe_ratio(equity_curve['returns'])
    
    metrics = {
        "Total Return": total_return * 100,
        "Net Profit": net_profit,
        "Max Drawdown": max_drawdown,
        "Sharpe Ratio": sharpe_ratio,
        "Total Trades": len(trade_log)
    }
    
    return metrics