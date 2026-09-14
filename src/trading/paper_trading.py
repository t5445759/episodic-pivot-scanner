"""Paper trading module for simulating trades without real money."""
import pandas as pd
from typing import List, Dict, Optional
from datetime import datetime
from config.config import config


class PaperTradingAccount:
    """Simulated trading account for paper trading."""
    
    def __init__(self, initial_capital: float = None):
        """Initialize paper trading account.
        
        Args:
            initial_capital: Starting capital (default from config)
        """
        self.initial_capital = initial_capital or config.paper_trading.initial_capital
        self.cash = self.initial_capital
        self.positions: Dict[str, Dict] = {}  # {ticker: {shares, entry_price, entry_time}}
        self.trades: List[Dict] = []  # History of all trades
        self.created_at = datetime.now()
    
    def buy(self, ticker: str, price: float, shares: int, timestamp: datetime = None) -> bool:
        """Execute a paper buy order.
        
        Args:
            ticker: Stock ticker symbol
            price: Purchase price per share
            shares: Number of shares to buy
            timestamp: Time of purchase
            
        Returns:
            True if successful, False otherwise
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        # Calculate cost with commission
        total_cost = shares * price * (1 + config.backtest.commission_pct)
        
        # Check if sufficient funds
        if total_cost > self.cash:
            print(f"❌ Insufficient funds. Need ${total_cost:.2f}, have ${self.cash:.2f}")
            return False
        
        # Update cash
        self.cash -= total_cost
        
        # Add position
        self.positions[ticker] = {
            'shares': shares,
            'entry_price': price,
            'entry_time': timestamp,
            'current_price': price
        }
        
        # Record trade
        self.trades.append({
            'type': 'BUY',
            'ticker': ticker,
            'price': price,
            'shares': shares,
            'cost': total_cost,
            'timestamp': timestamp,
            'cash_before': self.cash + total_cost,
            'cash_after': self.cash
        })
        
        print(f"✅ BUY {shares} {ticker} @ ${price:.2f} (Total: ${total_cost:.2f})")
        return True
    
    def sell(self, ticker: str, price: float, shares: int = None, timestamp: datetime = None) -> bool:
        """Execute a paper sell order.
        
        Args:
            ticker: Stock ticker symbol
            price: Sale price per share
            shares: Number of shares to sell (default: all)
            timestamp: Time of sale
            
        Returns:
            True if successful, False otherwise
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        # Check if position exists
        if ticker not in self.positions:
            print(f"❌ No position in {ticker}")
            return False
        
        position = self.positions[ticker]
        
        # Use all shares if not specified
        if shares is None:
            shares = position['shares']
        
        if shares > position['shares']:
            print(f"❌ Cannot sell {shares} shares, only have {position['shares']}")
            return False
        
        # Calculate proceeds
        proceeds = shares * price * (1 - config.backtest.commission_pct)
        entry_cost = shares * position['entry_price'] * (1 + config.backtest.commission_pct)
        profit_loss = proceeds - entry_cost
        profit_loss_pct = (profit_loss / entry_cost) * 100 if entry_cost > 0 else 0
        
        # Update cash
        self.cash += proceeds
        
        # Update position
        if shares == position['shares']:
            # Close entire position
            del self.positions[ticker]
        else:
            # Partial close
            position['shares'] -= shares
        
        # Record trade
        self.trades.append({
            'type': 'SELL',
            'ticker': ticker,
            'price': price,
            'shares': shares,
            'proceeds': proceeds,
            'profit_loss': profit_loss,
            'profit_loss_pct': profit_loss_pct,
            'timestamp': timestamp,
            'cash_before': self.cash - proceeds,
            'cash_after': self.cash
        })
        
        print(f"✅ SELL {shares} {ticker} @ ${price:.2f} (Proceeds: ${proceeds:.2f}, P/L: ${profit_loss:.2f} ({profit_loss_pct:.2f}%))")
        return True
    
    def update_position_price(self, ticker: str, current_price: float):
        """Update current price of open position.
        
        Args:
            ticker: Stock ticker symbol
            current_price: Current market price
        """
        if ticker in self.positions:
            self.positions[ticker]['current_price'] = current_price
    
    def get_portfolio_value(self) -> float:
        """Get total portfolio value (cash + positions).
        
        Returns:
            Total portfolio value
        """
        portfolio_value = self.cash
        
        for ticker, position in self.positions.items():
            portfolio_value += position['shares'] * position['current_price']
        
        return portfolio_value
    
    def get_position_value(self, ticker: str) -> float:
        """Get value of a specific position.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Current value of position
        """
        if ticker not in self.positions:
            return 0.0
        
        position = self.positions[ticker]
        return position['shares'] * position['current_price']
    
    def get_unrealized_pnl(self, ticker: str) -> Dict:
        """Get unrealized P&L for a position.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Dictionary with unrealized P&L details
        """
        if ticker not in self.positions:
            return {'ticker': ticker, 'error': 'No position'}
        
        position = self.positions[ticker]
        current_value = position['shares'] * position['current_price']
        entry_value = position['shares'] * position['entry_price']
        unrealized_pnl = current_value - entry_value
        unrealized_pnl_pct = (unrealized_pnl / entry_value) * 100 if entry_value > 0 else 0
        
        return {
            'ticker': ticker,
            'shares': position['shares'],
            'entry_price': position['entry_price'],
            'current_price': position['current_price'],
            'entry_value': entry_value,
            'current_value': current_value,
            'unrealized_pnl': unrealized_pnl,
            'unrealized_pnl_pct': unrealized_pnl_pct
        }
    
    def get_summary(self) -> Dict:
        """Get account summary.
        
        Returns:
            Dictionary with account summary statistics
        """
        total_value = self.get_portfolio_value()
        total_return = ((total_value - self.initial_capital) / self.initial_capital) * 100
        
        # Calculate trade statistics
        buy_trades = [t for t in self.trades if t['type'] == 'BUY']
        sell_trades = [t for t in self.trades if t['type'] == 'SELL']
        
        winning_trades = [t for t in sell_trades if t.get('profit_loss', 0) > 0]
        losing_trades = [t for t in sell_trades if t.get('profit_loss', 0) < 0]
        
        return {
            'initial_capital': self.initial_capital,
            'current_value': total_value,
            'cash': self.cash,
            'positions_value': total_value - self.cash,
            'total_return_pct': total_return,
            'num_positions': len(self.positions),
            'total_trades': len(self.trades),
            'buy_trades': len(buy_trades),
            'sell_trades': len(sell_trades),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate_pct': (len(winning_trades) / len(sell_trades) * 100) if sell_trades else 0,
            'created_at': self.created_at
        }
    
    def get_positions_summary(self) -> List[Dict]:
        """Get summary of all open positions.
        
        Returns:
            List of dictionaries with position details
        """
        positions_list = []
        
        for ticker, position in self.positions.items():
            pnl_info = self.get_unrealized_pnl(ticker)
            positions_list.append(pnl_info)
        
        return sorted(positions_list, key=lambda x: x.get('unrealized_pnl', 0), reverse=True)
    
    def get_trade_history(self, limit: int = 100) -> List[Dict]:
        """Get trade history.
        
        Args:
            limit: Maximum number of trades to return
            
        Returns:
            List of trade dictionaries
        """
        return self.trades[-limit:]
    
    def close_all_positions(self, current_prices: Dict[str, float]):
        """Close all open positions at specified prices.
        
        Args:
            current_prices: Dictionary mapping tickers to current prices
        """
        tickers_to_close = list(self.positions.keys())
        
        for ticker in tickers_to_close:
            if ticker in current_prices:
                self.sell(ticker, current_prices[ticker])
