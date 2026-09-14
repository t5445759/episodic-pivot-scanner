"""Example 6: Complete End-to-End Workflow

This example demonstrates a complete workflow: scan, backtest, paper trade, and alerts.
"""

import asyncio
from src.data.fetcher import YahooFinanceFetcher
from src.scanner.core import StockScanner
from src.backtest.backtester import EpisodicPivotBacktester
from src.trading.paper_trading import PaperTradingAccount
from src.alerts.handlers import AlertManager, EmailAlertHandler
from datetime import datetime


async def main():
    """Run complete workflow example."""
    print("\n🚀 Example 6: Complete End-to-End Workflow\n")
    print("="*80)
    
    # Step 1: Scan for episodic pivot stocks
    print("\n📍 STEP 1: Scanning for Episodic Pivot Stocks")
    print("-" * 80)
    
    fetcher = YahooFinanceFetcher()
    scanner = StockScanner(fetcher)
    tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA']
    
    print(f"\nScanning {len(tickers)} stocks...")
    scan_results = await scanner.scan_universe(tickers)
    
    if not scan_results:
        print("No stocks matched criteria. Exiting.")
        return
    
    print(f"✅ Found {len(scan_results)} stocks\n")
    for result in scan_results[:3]:  # Show top 3
        print(f"  {result['ticker']}: Score {result['score']:.3f}")
    
    # Step 2: Backtest the top candidate
    print("\n📍 STEP 2: Backtesting Top Candidate")
    print("-" * 80)
    
    top_ticker = scan_results[0]['ticker']
    print(f"\nBacktesting {top_ticker}...")
    
    backtester = EpisodicPivotBacktester(initial_capital=100000)
    backtest_result = await backtester.backtest_ticker(
        top_ticker, '2023-01-01', '2024-01-01'
    )
    
    if 'error' not in backtest_result:
        print(f"✅ Backtest Complete")
        print(f"   Total Return: {backtest_result['total_return_pct']:.2f}%")
        print(f"   Win Rate: {backtest_result['win_rate_pct']:.1f}%")
        print(f"   Total Trades: {backtest_result['total_trades']}")
    else:
        print(f"❌ Backtest failed: {backtest_result['error']}")
    
    # Step 3: Setup paper trading
    print("\n📍 STEP 3: Paper Trading Setup")
    print("-" * 80)
    
    account = PaperTradingAccount(initial_capital=100000)
    print(f"\n💵 Account initialized with $100,000")
    
    # Simulate buying the top stock at scan price
    price = scan_results[0]['price']
    shares = 100
    print(f"   Buying 100 shares of {top_ticker} @ ${price:.2f}")
    account.buy(top_ticker, price, shares)
    
    print(f"\n✅ Paper Trading Account:")
    summary = account.get_summary()
    print(f"   Current Value: ${summary['current_value']:,.2f}")
    print(f"   Cash: ${summary['cash']:,.2f}")
    
    # Step 4: Setup alerts
    print("\n📍 STEP 4: Alert Setup")
    print("-" * 80)
    
    alert_manager = AlertManager()
    # Note: Requires .env configuration for actual alerts
    print(f"\n✅ Alert manager initialized")
    print(f"   Note: Configure .env for email/SMS alerts")
    
    # Create and send sample alert
    alert = {
        'ticker': top_ticker,
        'price': price,
        'gap_pct': scan_results[0]['gap_pct'],
        'relative_volume': scan_results[0]['relative_volume'],
        'score': scan_results[0]['score'],
        'timestamp': datetime.now()
    }
    
    print(f"\n   Sample alert created for {top_ticker}")
    
    # Summary
    print("\n📍 WORKFLOW COMPLETE")
    print("="*80)
    print(f"\n✅ Summary:")
    print(f"   • Found {len(scan_results)} episodic pivot candidates")
    print(f"   • Backtested {top_ticker}")
    print(f"   • Setup paper trading account")
    print(f"   • Configured alerts")
    print(f"\n📊 Next Steps:")
    print(f"   1. Monitor paper trading account")
    print(f"   2. Review news and sentiment for {top_ticker}")
    print(f"   3. Consider live trading on Alpaca/Robinhood")
    print()


if __name__ == "__main__":
    asyncio.run(main())
