"""Example 1: Basic Scanning

This example demonstrates how to run a basic scan for episodic pivot stocks.
"""

import asyncio
from src.data.fetcher import YahooFinanceFetcher
from src.scanner.core import StockScanner


async def main():
    """Run a basic scan example."""
    print("\n🚀 Example 1: Basic Scanning\n")
    print("="*80)
    
    # Initialize fetcher and scanner
    fetcher = YahooFinanceFetcher()
    scanner = StockScanner(fetcher)
    
    # List of stocks to scan (sample)
    tickers = [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'JPM',
        'V', 'JNJ', 'WMT', 'PG', 'DIS', 'MA', 'HD'
    ]
    
    # Run scan
    print(f"\nScanning {len(tickers)} stocks for episodic pivot criteria...\n")
    results = await scanner.scan_universe(tickers)
    
    # Display results
    if results:
        print(f"✅ Found {len(results)} stocks matching criteria:\n")
        
        for i, result in enumerate(results, 1):
            print(f"{i}. {result['ticker']}")
            print(f"   Price: ${result['price']:.2f}")
            print(f"   Gap: {result['gap_pct']:.2f}%")
            print(f"   Relative Volume: {result['relative_volume']:.2f}x")
            print(f"   Market Cap: {result['market_cap_readable']}")
            print(f"   Sector: {result['sector']}")
            print(f"   Score: {result['score']:.3f}\n")
    else:
        print("❌ No stocks matched the criteria.")


if __name__ == "__main__":
    asyncio.run(main())
