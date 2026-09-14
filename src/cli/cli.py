"""Command-line interface for the scanner."""
import click
import asyncio
from datetime import datetime
from typing import List
import json
from tabulate import tabulate
from config.config import config
from src.data.fetcher import YahooFinanceFetcher
from src.scanner.core import StockScanner
from src.backtest.backtester import EpisodicPivotBacktester
from src.alerts.handlers import AlertManager, EmailAlertHandler, SMSAlertHandler
from src.alerts.news_catalyst import NewsCatalystFetcher
from src.trading.paper_trading import PaperTradingAccount
from src.db.session import init_db, SessionLocal
from src.db.manager import DatabaseManager


@click.group()
def cli():
    """Episodic Pivot Scanner - Gap up stock screener with backtesting and paper trading."""
    pass


@cli.command()
@click.option('--universe', default='sp500', help='Stock universe: sp500, nasdaq, russell2000, all')
@click.option('--limit', default=None, type=int, help='Limit number of stocks to scan')
@click.option('--output', default=None, help='Output file (JSON or CSV)')
async def scan(universe: str, limit: int, output: str):
    """Run real-time scan for episodic pivot stocks."""
    click.echo("\n" + "="*80)
    click.echo("🚀 EPISODIC PIVOT SCANNER - Starting Real-Time Scan")
    click.echo("="*80)
    
    # Initialize database
    init_db()
    db = SessionLocal()
    db_manager = DatabaseManager(db)
    
    # Initialize fetcher and scanner
    fetcher = YahooFinanceFetcher()
    scanner = StockScanner(fetcher)
    
    # Get stock universe
    tickers = _get_stock_universe(universe, limit)
    click.echo(f"\n📊 Scanning {len(tickers)} stocks from {universe.upper()}...")
    
    # Run scan
    results = await scanner.scan_universe(tickers)
    
    if not results:
        click.echo("\n❌ No stocks matched the criteria.")
        return
    
    # Display results
    click.echo(f"\n✅ Found {len(results)} stocks matching criteria\n")
    _display_scan_results(results)
    
    # Save to database
    for result in results:
        db_manager.save_scan_result(result)
    
    # Save to file if specified
    if output:
        _save_results_to_file(results, output)
        click.echo(f"\n💾 Results saved to {output}")
    
    db.close()


@cli.command()
@click.argument('ticker')
@click.option('--start-date', default='2023-01-01', help='Backtest start date (YYYY-MM-DD)')
@click.option('--end-date', default='2024-01-01', help='Backtest end date (YYYY-MM-DD)')
@click.option('--initial-capital', default=100000, type=float, help='Initial capital')
async def backtest(ticker: str, start_date: str, end_date: str, initial_capital: float):
    """Run backtest for a specific ticker."""
    click.echo("\n" + "="*80)
    click.echo(f"📈 BACKTESTING {ticker}")
    click.echo("="*80)
    
    # Initialize database
    init_db()
    db = SessionLocal()
    db_manager = DatabaseManager(db)
    
    # Run backtest
    backtester = EpisodicPivotBacktester(initial_capital)
    click.echo(f"\nBacktesting {ticker} from {start_date} to {end_date}...")
    
    result = await backtester.backtest_ticker(ticker, start_date, end_date)
    
    if 'error' in result:
        click.echo(f"\n❌ Error: {result['error']}")
        return
    
    # Display results
    click.echo("\n" + "-"*80)
    click.echo("📊 BACKTEST RESULTS")
    click.echo("-"*80)
    
    results_table = [
        ['Initial Capital', f"${result['initial_capital']:,.2f}"],
        ['Final Capital', f"${result['final_capital']:,.2f}"],
        ['Total Return', f"{result['total_return_pct']:.2f}%"],
        ['Buy & Hold Return', f"{result['buy_hold_return_pct']:.2f}%"],
        ['Excess Return', f"{result['excess_return_pct']:.2f}%"],
        ['Total Trades', result['total_trades']],
        ['Winning Trades', result['winning_trades']],
        ['Losing Trades', result['losing_trades']],
        ['Win Rate', f"{result['win_rate_pct']:.1f}%"],
        ['Avg Win', f"{result['avg_win_pct']:.2f}%"],
        ['Avg Loss', f"{result['avg_loss_pct']:.2f}%"],
        ['Profit Factor', f"{result['profit_factor']:.2f}"]
    ]
    
    click.echo(tabulate(results_table, tablefmt='grid'))
    
    # Save to database
    result['start_date'] = start_date
    result['end_date'] = end_date
    db_manager.save_backtest_result(result)
    
    click.echo(f"\n✅ Backtest results saved to database")
    db.close()


@cli.command()
@click.argument('ticker')
@click.option('--price', required=True, type=float, help='Entry price')
@click.option('--shares', required=True, type=int, help='Number of shares')
async def paper_buy(ticker: str, price: float, shares: int):
    """Execute a paper trading BUY order."""
    init_db()
    db = SessionLocal()
    db_manager = DatabaseManager(db)
    
    # TODO: Integrate with persistent account
    account = PaperTradingAccount()
    success = account.buy(ticker, price, shares)
    
    if success:
        trade = {
            'ticker': ticker,
            'type': 'BUY',
            'price': price,
            'shares': shares,
            'cost': shares * price * (1 + config.backtest.commission_pct),
            'timestamp': datetime.now()
        }
        db_manager.save_trade(trade)
        click.echo(f"\n✅ Paper trade BUY recorded")
    else:
        click.echo(f"\n❌ Paper trade failed")
    
    db.close()


@cli.command()
@click.argument('ticker')
@click.option('--price', required=True, type=float, help='Sale price')
@click.option('--shares', type=int, help='Number of shares (default: all)')
async def paper_sell(ticker: str, price: float, shares: int):
    """Execute a paper trading SELL order."""
    init_db()
    db = SessionLocal()
    db_manager = DatabaseManager(db)
    
    # TODO: Integrate with persistent account
    account = PaperTradingAccount()
    success = account.sell(ticker, price, shares)
    
    if success:
        trade = {
            'ticker': ticker,
            'type': 'SELL',
            'price': price,
            'shares': shares or 0,
            'proceeds': shares * price * (1 - config.backtest.commission_pct),
            'timestamp': datetime.now()
        }
        db_manager.save_trade(trade)
        click.echo(f"\n✅ Paper trade SELL recorded")
    else:
        click.echo(f"\n❌ Paper trade failed")
    
    db.close()


@cli.command()
@click.argument('ticker')
@click.option('--company-name', help='Company full name (for news search)')
async def news(ticker: str, company_name: str):
    """Get news and sentiment for a stock."""
    click.echo(f"\n📰 NEWS & SENTIMENT - {ticker}")
    click.echo("="*80)
    
    init_db()
    db = SessionLocal()
    db_manager = DatabaseManager(db)
    
    fetcher = NewsCatalystFetcher(config.data.newsapi_key)
    
    if not company_name:
        company_name = ticker
    
    click.echo(f"\nFetching news for {company_name}...")
    summary = await fetcher.get_catalyst_summary(ticker, company_name)
    
    # Display sentiment
    sentiment = summary['sentiment']
    click.echo(f"\n📊 SENTIMENT ANALYSIS")
    click.echo("-"*80)
    sentiment_table = [
        ['Overall Sentiment', sentiment['sentiment']],
        ['Sentiment Score', f"{sentiment['score']:.2f}"],
        ['Articles Analyzed', sentiment['articles_analyzed']],
        ['Positive', sentiment.get('positive_count', 0)],
        ['Negative', sentiment.get('negative_count', 0)],
        ['Neutral', sentiment.get('neutral_count', 0)]
    ]
    click.echo(tabulate(sentiment_table, tablefmt='grid'))
    
    # Display articles
    if summary['articles']:
        click.echo(f"\n📄 RECENT ARTICLES (Top 5)")
        click.echo("-"*80)
        for i, article in enumerate(summary['articles'][:5], 1):
            click.echo(f"\n{i}. {article['title']}")
            click.echo(f"   Source: {article['source']}")
            click.echo(f"   Date: {article['published_at']}")
            click.echo(f"   URL: {article['url']}")
    
    db.close()


@cli.command()
@click.option('--days', default=7, type=int, help='Look back N days')
@click.option('--limit', default=50, type=int, help='Maximum results')
async def history(days: int, limit: int):
    """View scan history."""
    click.echo(f"\n📋 SCAN HISTORY (Last {days} days)")
    click.echo("="*80)
    
    init_db()
    db = SessionLocal()
    db_manager = DatabaseManager(db)
    
    results = db_manager.get_scan_results(limit=limit, days=days)
    
    if not results:
        click.echo("\nNo scan results found.")
        return
    
    table_data = []
    for result in results[:20]:  # Show top 20
        table_data.append([
            result.scan_date.strftime('%Y-%m-%d %H:%M'),
            result.ticker,
            f"${result.price:.2f}",
            f"{result.gap_pct:.2f}%",
            f"{result.relative_volume:.2f}x",
            f"{result.volume:,}",
            f"{result.score:.3f}"
        ])
    
    headers = ['Date', 'Ticker', 'Price', 'Gap %', 'Rel Vol', 'Volume', 'Score']
    click.echo("\n" + tabulate(table_data, headers=headers, tablefmt='grid'))
    
    db.close()


@cli.command()
@click.option('--output', default='config.json', help='Output config file')
def config_show(output: str):
    """Display current configuration."""
    click.echo("\n⚙️  CURRENT CONFIGURATION")
    click.echo("="*80)
    
    cfg_dict = {
        'scanner': {
            'min_price': config.scanner.min_price,
            'max_price': config.scanner.max_price,
            'min_market_cap': f"${config.scanner.min_market_cap:,.0f}",
            'max_market_cap': f"${config.scanner.max_market_cap:,.0f}",
            'min_gap_pct': f"{config.scanner.min_gap_pct}%",
            'min_relative_volume': f"{config.scanner.min_relative_volume}x",
            'min_volume': f"{config.scanner.min_volume:,}",
            'min_avg_dollar_volume': f"${config.scanner.min_avg_dollar_volume:,.0f}"
        },
        'backtest': {
            'initial_cash': f"${config.backtest.initial_cash:,.2f}",
            'commission_pct': f"{config.backtest.commission_pct*100:.2f}%",
            'position_size_pct': f"{config.backtest.position_size_pct*100:.1f}%"
        },
        'paper_trading': {
            'initial_capital': f"${config.paper_trading.initial_capital:,.2f}",
            'take_profit_pct': f"{config.paper_trading.take_profit_pct*100:.1f}%",
            'stop_loss_pct': f"{config.paper_trading.stop_loss_pct*100:.1f}%"
        }
    }
    
    click.echo(json.dumps(cfg_dict, indent=2))
    
    if output:
        with open(output, 'w') as f:
            json.dump(cfg_dict, f, indent=2)
        click.echo(f"\n💾 Configuration saved to {output}")


def _get_stock_universe(universe: str, limit: int = None) -> List[str]:
    """Get list of tickers for the specified universe."""
    # These are placeholder lists - in production, fetch from reliable source
    universes = {
        'sp500': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'JPM', 'V', 'JNJ'],  # Sample
        'nasdaq': ['QQQ', 'NVDA', 'TSLA', 'META', 'CSCO', 'ADBE', 'PYPL', 'INTC'],
        'russell2000': ['IWM', 'DIS', 'DOC', 'MSTR', 'RIOT'],
        'all': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
    }
    
    tickers = universes.get(universe.lower(), universes['sp500'])
    
    if limit:
        tickers = tickers[:limit]
    
    return tickers


def _display_scan_results(results: List[dict]):
    """Display scan results in a formatted table."""
    table_data = []
    
    for result in results:
        table_data.append([
            result['ticker'],
            f"${result['price']:.2f}",
            f"{result['gap_pct']:.2f}%",
            f"{result['change_pct']:.2f}%",
            f"{result['relative_volume']:.2f}x",
            f"{result['volume']:,}",
            result['market_cap_readable'],
            result['sector'],
            f"{result['week_performance']:.2f}%",
            f"{result['month_performance']:.2f}%",
            f"{result['sma_10']:.2f}",
            f"{result['sma_20']:.2f}",
            f"{result['score']:.3f}"
        ])
    
    headers = [
        'Ticker', 'Price', 'Gap %', 'Change %', 'Rel Vol',
        'Volume', 'Market Cap', 'Sector', '1W%', '1M%', 'SMA10', 'SMA20', 'Score'
    ]
    
    click.echo("\n" + tabulate(table_data, headers=headers, tablefmt='grid'))


def _save_results_to_file(results: List[dict], filepath: str):
    """Save results to JSON or CSV file."""
    if filepath.endswith('.json'):
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2, default=str)
    elif filepath.endswith('.csv'):
        import csv
        if results:
            with open(filepath, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=results[0].keys())
                writer.writeheader()
                writer.writerows(results)


if __name__ == '__main__':
    cli()
