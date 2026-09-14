"""Main orchestrator for the scanner system."""
import asyncio
import logging
from datetime import datetime, time, timedelta
from typing import List
from config.config import config
from src.data.fetcher import YahooFinanceFetcher, AlpacaDataFetcher
from src.scanner.core import StockScanner
from src.alerts.handlers import AlertManager, EmailAlertHandler, SMSAlertHandler
from src.alerts.news_catalyst import NewsCatalystFetcher
from src.db.session import init_db, SessionLocal
from src.db.manager import DatabaseManager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EpisodicPivotOrchestrator:
    """Main orchestrator for scanning and alerting."""
    
    def __init__(self):
        """Initialize orchestrator."""
        self.scanner = None
        self.alert_manager = AlertManager()
        self.news_fetcher = NewsCatalystFetcher(config.data.newsapi_key)
        self.db_manager = None
        self.running = False
    
    async def initialize(self):
        """Initialize all components."""
        logger.info("🚀 Initializing Episodic Pivot Orchestrator")
        
        # Initialize database
        init_db()
        db = SessionLocal()
        self.db_manager = DatabaseManager(db)
        
        # Initialize data fetcher
        if config.data.use_yahoo_finance:
            fetcher = YahooFinanceFetcher()
            logger.info("✅ Yahoo Finance fetcher initialized")
        else:
            fetcher = AlpacaDataFetcher(
                config.data.alpaca_api_key,
                config.data.alpaca_secret_key,
                config.data.alpaca_base_url
            )
            logger.info("✅ Alpaca fetcher initialized")
        
        # Initialize scanner
        self.scanner = StockScanner(fetcher)
        logger.info("✅ Scanner initialized")
        
        # Setup alert handlers
        if config.alert.smtp_email and config.alert.alert_recipients:
            email_handler = EmailAlertHandler({
                'smtp_server': config.alert.smtp_server,
                'smtp_port': config.alert.smtp_port,
                'smtp_email': config.alert.smtp_email,
                'smtp_password': config.alert.smtp_password,
                'alert_recipients': config.alert.alert_recipients
            })
            self.alert_manager.add_handler(email_handler)
            logger.info("✅ Email alert handler configured")
        
        if config.alert.twilio_account_sid and config.alert.twilio_auth_token:
            sms_handler = SMSAlertHandler({
                'twilio_account_sid': config.alert.twilio_account_sid,
                'twilio_auth_token': config.alert.twilio_auth_token,
                'twilio_from': config.alert.twilio_from,
                'twilio_to': config.alert.twilio_to
            })
            self.alert_manager.add_handler(sms_handler)
            logger.info("✅ SMS alert handler configured")
        
        logger.info("✅ Orchestrator initialization complete\n")
    
    async def scan_and_alert(self, tickers: List[str]):
        """Scan stocks and send alerts for matches.
        
        Args:
            tickers: List of stock tickers to scan
        """
        logger.info(f"📊 Scanning {len(tickers)} stocks...")
        
        # Run scan
        results = await self.scanner.scan_universe(tickers)
        
        if not results:
            logger.info("❌ No stocks matched criteria")
            return
        
        logger.info(f"✅ Found {len(results)} stocks matching criteria")
        
        # Process each result
        for result in results:
            # Save to database
            if self.db_manager:
                self.db_manager.save_scan_result(result)
            
            # Check if should alert
            if self._should_alert(result):
                await self._send_alert_for_result(result)
    
    async def continuous_scan(self, tickers: List[str], interval_seconds: int = None):
        """Run continuous scanning loop.
        
        Args:
            tickers: List of stock tickers to scan
            interval_seconds: Scan interval (default from config)
        """
        if interval_seconds is None:
            interval_seconds = config.scanner.scan_interval_seconds
        
        self.running = True
        logger.info(f"🔄 Starting continuous scan loop (interval: {interval_seconds}s)")
        
        try:
            while self.running:
                # Check if within market hours (or premarket if enabled)
                if self._is_scan_time():
                    await self.scan_and_alert(tickers)
                else:
                    logger.debug("Outside market hours, waiting...")
                
                await asyncio.sleep(interval_seconds)
        
        except KeyboardInterrupt:
            logger.info("\n⏸  Scan loop interrupted by user")
            self.running = False
    
    async def backtest_multiple(self, tickers: List[str], start_date: str, end_date: str):
        """Run backtest on multiple tickers.
        
        Args:
            tickers: List of stock tickers
            start_date: Backtest start date (YYYY-MM-DD)
            end_date: Backtest end date (YYYY-MM-DD)
        """
        from src.backtest.backtester import EpisodicPivotBacktester
        
        logger.info(f"📈 Running backtest on {len(tickers)} tickers from {start_date} to {end_date}")
        
        backtester = EpisodicPivotBacktester()
        results = []
        
        for ticker in tickers:
            logger.info(f"Backtesting {ticker}...")
            result = await backtester.backtest_ticker(ticker, start_date, end_date)
            
            if 'error' not in result:
                results.append(result)
                if self.db_manager:
                    result['start_date'] = start_date
                    result['end_date'] = end_date
                    self.db_manager.save_backtest_result(result)
        
        logger.info(f"✅ Backtest complete. {len(results)} successful backtests.")
        return results
    
    def _is_scan_time(self) -> bool:
        """Check if current time is within scan window."""
        now = datetime.now()
        current_time = now.time()
        
        market_open = time(config.scanner.market_open_hour, config.scanner.market_open_minute)
        market_close = time(config.scanner.market_close_hour, config.scanner.market_close_minute)
        
        # Check if within regular market hours
        if market_open <= current_time <= market_close:
            return True
        
        # Check if within premarket hours
        if config.scanner.enable_premarket:
            premarket_start = time(config.scanner.premarket_start_hour, config.scanner.premarket_start_minute)
            if premarket_start <= current_time < market_open:
                return True
        
        return False
    
    def _should_alert(self, result: dict) -> bool:
        """Determine if result should trigger an alert."""
        gap_pct = result.get('gap_pct', 0)
        rel_vol = result.get('relative_volume', 0)
        
        # Alert if meets or exceeds thresholds
        return (gap_pct >= config.alert.alert_on_gap_above_pct and
                rel_vol >= config.alert.alert_on_relative_volume_above)
    
    async def _send_alert_for_result(self, result: dict):
        """Send alert for a specific result."""
        ticker = result['ticker']
        logger.info(f"📢 Sending alert for {ticker}")
        
        # Get news catalyst
        try:
            news_summary = await self.news_fetcher.get_catalyst_summary(ticker, ticker)
            result['catalyst_sentiment'] = news_summary['sentiment']
        except Exception as e:
            logger.warning(f"Could not fetch news for {ticker}: {e}")
        
        # Send alert through all handlers
        success = await self.alert_manager.send_alert(result)
        
        if success:
            if self.db_manager:
                self.db_manager.save_alert(result, success=True)
            logger.info(f"✅ Alert sent for {ticker}")
        else:
            logger.warning(f"⚠️  Alert failed for {ticker}")
    
    def stop(self):
        """Stop the orchestrator."""
        self.running = False
        logger.info("🛑 Orchestrator stopped")


async def run_orchestrator(tickers: List[str] = None, mode: str = 'scan'):
    """Run the orchestrator.
    
    Args:
        tickers: List of stock tickers to scan
        mode: 'scan' for continuous scanning, 'backtest' for historical backtest
    """
    orchestrator = EpisodicPivotOrchestrator()
    await orchestrator.initialize()
    
    if tickers is None:
        # Default to S&P 500 sample
        tickers = [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'JPM',
            'V', 'JNJ', 'WMT', 'PG', 'DIS', 'MA', 'HD', 'MRK', 'PEP', 'AXP'
        ]
    
    try:
        if mode == 'continuous':
            await orchestrator.continuous_scan(tickers)
        elif mode == 'backtest':
            results = await orchestrator.backtest_multiple(tickers, '2023-01-01', '2024-01-01')
            logger.info(f"Backtest results saved: {len(results)} tickers")
        else:
            await orchestrator.scan_and_alert(tickers)
    except Exception as e:
        logger.error(f"Orchestrator error: {e}", exc_info=True)
    finally:
        orchestrator.stop()


if __name__ == '__main__':
    # Run continuous scan
    asyncio.run(run_orchestrator(mode='continuous'))
