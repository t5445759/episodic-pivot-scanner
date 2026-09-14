"""Example 2: Backtesting

This example demonstrates how to backtest the episodic pivot strategy.
"""

import asyncio
from src.backtest.backtester import EpisodicPivotBacktester


async def main():
    """Run a backtest example."""
    print("\n📈 Example 2: Backtesting\n")
    print("="*80)
    
    # Create backtester
    backtester = EpisodicPivotBacktester(initial_capital=100000)
    
    # Run backtest
    ticker = 'TSLA'
    start_date = '2023-01-01'
    end_date = '2024-01-01'
    
    print(f"\nBacktesting {ticker} from {start_date} to {end_date}...\n")
    result = await backtester.backtest_ticker(ticker, start_date, end_date)
    
    # Display results
    if 'error' in result:
        print(f"❌ Error: {result['error']}")
    else:
        print(f"✅ Backtest Complete\n")
        print(f"Initial Capital: ${result['initial_capital']:,.2f}")
        print(f"Final Capital: ${result['final_capital']:,.2f}")
        print(f"Total Return: {result['total_return_pct']:.2f}%")
        print(f"Buy & Hold Return: {result['buy_hold_return_pct']:.2f}%")
        print(f"Excess Return: {result['excess_return_pct']:.2f}%")
        print(f"\nTotal Trades: {result['total_trades']}")
        print(f"Winning Trades: {result['winning_trades']}")
        print(f"Losing Trades: {result['losing_trades']}")
        print(f"Win Rate: {result['win_rate_pct']:.1f}%")
        print(f"Avg Win: {result['avg_win_pct']:.2f}%")
        print(f"Avg Loss: {result['avg_loss_pct']:.2f}%")
        print(f"Profit Factor: {result['profit_factor']:.2f}")


if __name__ == "__main__":
    asyncio.run(main())
