"""Backtesting engine for episodic pivot strategy."""
import pandas as pd
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from config.config import config
from src.data.fetcher import YahooFinanceFetcher
import numpy as np


class EpisodicPivotBacktester:
    """Backtester for episodic pivot strategy."""
    
    def __init__(self, initial_capital: float = None):
        """Initialize backtester.
        
        Args:
            initial_capital: Starting capital (default from config)
        """
        self.initial_capital = initial_capital or config.backtest.initial_cash
        self.capital = self.initial_capital
        self.positions = {}  # {ticker: shares}
        self.trades = []  # History of trades
        self.portfolio_values = [self.initial_capital]
        self.fetcher = YahooFinanceFetcher()
    
    async def backtest_ticker(self, ticker: str, start_date: str, end_date: str) -> Dict:
        """Backtest a single ticker.
        
        Args:
            ticker: Stock ticker symbol
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            Dictionary with backtest results
        """
        # Fetch historical data
        hist_df = await self.fetcher.fetch_historical_data(ticker, period='5y')
        if hist_df is None or hist_df.empty:
            return {'error': f'Could not fetch data for {ticker}'}
        
        # Filter to date range
        hist_df = hist_df[start_date:end_date]
        if hist_df.empty:
            return {'error': f'No data for {ticker} in range {start_date} to {end_date}'}
        
        # Reset tracking
        self.capital = self.initial_capital
        self.positions = {}
        self.trades = []
        self.portfolio_values = [self.initial_capital]
        
        # Calculate signals
        signals = self._generate_signals(hist_df)
        
        # Execute backtest
        for i, (date, row) in enumerate(hist_df.iterrows()):
            if i < 20:  # Need at least 20 periods for indicators
                continue
            
            signal = signals.iloc[i] if i < len(signals) else 'HOLD'
            price = row['Close']
            
            if signal == 'BUY' and ticker not in self.positions:
                self._execute_buy(ticker, price, date, row['Volume'])
            elif signal == 'SELL' and ticker in self.positions:
                self._execute_sell(ticker, price, date, row['Volume'])
            elif signal == 'HOLD' and ticker in self.positions:
                # Check stop loss and take profit
                self._check_exit_conditions(ticker, price, date, row['Volume'])
            
            # Update portfolio value
            portfolio_value = self._calculate_portfolio_value(hist_df.loc[:date])
            self.portfolio_values.append(portfolio_value)
        
        # Close any open positions at end
        if ticker in self.positions:
            last_price = hist_df['Close'].iloc[-1]
            self._execute_sell(ticker, last_price, hist_df.index[-1], hist_df['Volume'].iloc[-1])
        
        return self._generate_report(ticker, hist_df)
    
    def _generate_signals(self, df: pd.DataFrame) -> pd.Series:
        """Generate buy/sell signals based on episodic pivot criteria.
        
        Criteria:
        - Gap up > 10%
        - Relative volume > 5x
        - Price > 20-day SMA
        """
        signals = pd.Series('HOLD', index=df.index)
        
        # Calculate previous close (simulated)
        df['prev_close'] = df['Close'].shift(1)
        df['gap_pct'] = ((df['Open'] - df['prev_close']) / df['prev_close']) * 100
        
        # Calculate relative volume
        df['avg_volume_20d'] = df['Volume'].rolling(20).mean()
        df['relative_volume'] = df['Volume'] / df['avg_volume_20d']
        
        # Calculate SMAs
        df['sma_20'] = df['Close'].rolling(20).mean()
        df['sma_50'] = df['Close'].rolling(50).mean()
        
        # Buy signals: gap up + high volume + price above SMAs
        buy_condition = (
            (df['gap_pct'] >= config.scanner.min_gap_pct) &
            (df['relative_volume'] >= config.scanner.min_relative_volume) &
            (df['Close'] > df['sma_20']) &
            (df['Close'] > df['sma_50']) &
            (df['Volume'] >= config.scanner.min_volume)
        )
        signals[buy_condition] = 'BUY'
        
        # Sell signals: price below 10-day SMA or after N days in position
        df['sma_10'] = df['Close'].rolling(10).mean()
        sell_condition = (df['Close'] < df['sma_10'])
        signals[sell_condition] = 'SELL'
        
        return signals
    
    def _execute_buy(self, ticker: str, price: float, date, volume: int):
        """Execute a buy order."""
        # Calculate shares to buy (risk 5% per trade)
        position_size = self.capital * config.backtest.position_size_pct
        shares = int(position_size / price)
        
        if shares <= 0:
            return
        
        cost = shares * price * (1 + config.backtest.commission_pct)
        
        if cost > self.capital:
            shares = int(self.capital / price / (1 + config.backtest.commission_pct))
            cost = shares * price * (1 + config.backtest.commission_pct)
        
        if shares > 0:
            self.capital -= cost
            self.positions[ticker] = {
                'shares': shares,
                'entry_price': price,
                'entry_date': date,
                'stop_loss': price * (1 - config.paper_trading.stop_loss_pct),
                'take_profit': price * (1 + config.paper_trading.take_profit_pct)
            }
            
            self.trades.append({
                'type': 'BUY',
                'ticker': ticker,
                'price': price,
                'shares': shares,
                'date': date,
                'cost': cost
            })
    
    def _execute_sell(self, ticker: str, price: float, date, volume: int):
        """Execute a sell order."""
        if ticker not in self.positions:
            return
        
        position = self.positions[ticker]
        shares = position['shares']
        entry_price = position['entry_price']
        
        proceeds = shares * price * (1 - config.backtest.commission_pct)
        profit_loss = proceeds - (shares * entry_price * (1 + config.backtest.commission_pct))
        profit_loss_pct = (profit_loss / (shares * entry_price)) * 100
        
        self.capital += proceeds
        
        self.trades.append({
            'type': 'SELL',
            'ticker': ticker,
            'price': price,
            'shares': shares,
            'date': date,
            'proceeds': proceeds,
            'profit_loss': profit_loss,
            'profit_loss_pct': profit_loss_pct
        })
        
        del self.positions[ticker]
    
    def _check_exit_conditions(self, ticker: str, price: float, date, volume: int):
        """Check if position should be exited due to stop loss or take profit."""
        if ticker not in self.positions:
            return
        
        position = self.positions[ticker]
        
        if price <= position['stop_loss']:
            self._execute_sell(ticker, price, date, volume)
        elif price >= position['take_profit']:
            self._execute_sell(ticker, price, date, volume)
    
    def _calculate_portfolio_value(self, hist_df: pd.DataFrame) -> float:
        """Calculate current portfolio value."""
        value = self.capital
        
        if not hist_df.empty and not self.positions:
            current_prices = hist_df['Close'].iloc[-1]
            for ticker, position in self.positions.items():
                if ticker in current_prices:
                    value += position['shares'] * current_prices[ticker]
        
        return value
    
    def _generate_report(self, ticker: str, hist_df: pd.DataFrame) -> Dict:
        """Generate backtest report."""
        if not self.trades:
            return {
                'ticker': ticker,
                'error': 'No trades executed',
                'initial_capital': self.initial_capital,
                'final_capital': self.capital
            }
        
        buy_trades = [t for t in self.trades if t['type'] == 'BUY']
        sell_trades = [t for t in self.trades if t['type'] == 'SELL']
        
        total_return = ((self.capital - self.initial_capital) / self.initial_capital) * 100
        winning_trades = [t for t in sell_trades if t['profit_loss'] > 0]
        losing_trades = [t for t in sell_trades if t['profit_loss'] < 0]
        
        avg_win = np.mean([t['profit_loss_pct'] for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t['profit_loss_pct'] for t in losing_trades]) if losing_trades else 0
        
        # Calculate buy and hold return
        buy_hold_return = ((hist_df['Close'].iloc[-1] - hist_df['Close'].iloc[0]) / hist_df['Close'].iloc[0]) * 100
        
        return {
            'ticker': ticker,
            'initial_capital': self.initial_capital,
            'final_capital': self.capital,
            'total_return_pct': total_return,
            'buy_hold_return_pct': buy_hold_return,
            'excess_return_pct': total_return - buy_hold_return,
            'total_trades': len(self.trades),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate_pct': (len(winning_trades) / len(sell_trades) * 100) if sell_trades else 0,
            'avg_win_pct': avg_win,
            'avg_loss_pct': avg_loss,
            'profit_factor': abs(sum([t['profit_loss'] for t in winning_trades]) / sum([t['profit_loss'] for t in losing_trades])) if losing_trades and sum([t['profit_loss'] for t in losing_trades]) != 0 else 0,
            'portfolio_values': self.portfolio_values
        }
