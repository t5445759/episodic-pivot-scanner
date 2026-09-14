"""Example 3: Paper Trading

This example demonstrates how to use paper trading.
"""

from src.trading.paper_trading import PaperTradingAccount


def main():
    """Run a paper trading example."""
    print("\n💰 Example 3: Paper Trading\n")
    print("="*80)
    
    # Create paper trading account
    account = PaperTradingAccount(initial_capital=100000)
    
    print("\n📊 Initial Account Status:")
    summary = account.get_summary()
    print(f"   Capital: ${summary['initial_capital']:,.2f}")
    print(f"   Current Value: ${summary['current_value']:,.2f}")
    print(f"   Return: {summary['total_return_pct']:.2f}%\n")
    
    # Simulate some trades
    print("📝 Executing Trades:\n")
    
    # Buy AAPL
    print("1. Buying 100 shares of AAPL @ $150.00")
    account.buy('AAPL', 150.00, 100)
    
    # Buy MSFT
    print("2. Buying 50 shares of MSFT @ $300.00")
    account.buy('MSFT', 300.00, 50)
    
    # Update prices
    print("\n3. Updating market prices...")
    account.update_position_price('AAPL', 155.00)  # Up 5
    account.update_position_price('MSFT', 295.00)  # Down 5
    
    # Sell MSFT (with loss)
    print("4. Selling 50 shares of MSFT @ $295.00")
    account.sell('MSFT', 295.00)
    
    # View positions
    print("\n📊 Open Positions:")
    positions = account.get_positions_summary()
    for pos in positions:
        print(f"   {pos['ticker']}: {pos['shares']} shares")
        print(f"      Entry: ${pos['entry_price']:.2f}, Current: ${pos['current_price']:.2f}")
        print(f"      P&L: ${pos['unrealized_pnl']:.2f} ({pos['unrealized_pnl_pct']:.2f}%)\n")
    
    # Final account status
    print("\n💵 Final Account Status:")
    summary = account.get_summary()
    print(f"   Cash: ${summary['cash']:,.2f}")
    print(f"   Positions Value: ${summary['positions_value']:,.2f}")
    print(f"   Total Value: ${summary['current_value']:,.2f}")
    print(f"   Total Return: {summary['total_return_pct']:.2f}%")
    print(f"   Total Trades: {summary['total_trades']}")
    print(f"   Win Rate: {summary['win_rate_pct']:.1f}%")


if __name__ == "__main__":
    main()
