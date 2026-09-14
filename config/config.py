"""Configuration management for Episodic Pivot Scanner."""
import os
from dotenv import load_dotenv
from dataclasses import dataclass
from typing import Optional

load_dotenv()


@dataclass
class ScannerConfig:
    """Scanner-specific configuration."""
    # Price filters
    min_price: float = 5.0
    max_price: float = 500.0
    
    # Market cap filters (in dollars)
    min_market_cap: float = 50_000_000  # $50M
    max_market_cap: float = 10_000_000_000  # $10B
    
    # Gap filters
    min_gap_pct: float = 10.0  # 10% minimum gap
    
    # Volume filters
    min_relative_volume: float = 5.0  # 5x average volume
    min_volume: int = 500_000  # Minimum shares traded
    min_avg_dollar_volume: float = 10_000_000  # $10M average daily
    
    # Scanning interval
    scan_interval_seconds: int = int(os.getenv('SCAN_INTERVAL_SECONDS', '60'))
    
    # Market hours (ET)
    market_open_hour: int = 9
    market_open_minute: int = 30
    market_close_hour: int = 16
    market_close_minute: int = 0
    
    # Premarket scanning
    enable_premarket: bool = True
    premarket_start_hour: int = 4
    premarket_start_minute: int = 0


@dataclass
class BacktestConfig:
    """Backtesting configuration."""
    start_date: str = os.getenv('BACKTEST_START_DATE', '2023-01-01')
    end_date: str = os.getenv('BACKTEST_END_DATE', '2024-01-01')
    initial_cash: float = 100_000.0
    commission_pct: float = 0.001  # 0.1% commission
    slippage_pct: float = 0.002  # 0.2% slippage
    position_size_pct: float = 0.05  # Risk 5% per trade


@dataclass
class AlertConfig:
    """Alert and notification configuration."""
    # Email settings
    smtp_server: str = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port: int = int(os.getenv('SMTP_PORT', '587'))
    smtp_email: str = os.getenv('SMTP_EMAIL', '')
    smtp_password: str = os.getenv('SMTP_PASSWORD', '')
    alert_recipients: list = None
    
    # SMS settings (Twilio)
    twilio_account_sid: str = os.getenv('TWILIO_ACCOUNT_SID', '')
    twilio_auth_token: str = os.getenv('TWILIO_AUTH_TOKEN', '')
    twilio_from: str = os.getenv('TWILIO_PHONE_FROM', '')
    twilio_to: str = os.getenv('TWILIO_PHONE_TO', '')
    
    # Alert thresholds
    alert_on_gap_above_pct: float = 10.0
    alert_on_relative_volume_above: float = 5.0
    
    def __post_init__(self):
        if self.alert_recipients is None:
            recipients = os.getenv('ALERT_RECIPIENTS', '')
            self.alert_recipients = [r.strip() for r in recipients.split(',') if r.strip()]


@dataclass
class DataConfig:
    """Data source configuration."""
    # Yahoo Finance (free, no key required)
    use_yahoo_finance: bool = True
    
    # Alpaca (requires API key)
    use_alpaca: bool = True
    alpaca_api_key: str = os.getenv('ALPACA_API_KEY', '')
    alpaca_secret_key: str = os.getenv('ALPACA_SECRET_KEY', '')
    alpaca_base_url: str = os.getenv('ALPACA_BASE_URL', 'https://paper-trading.alpaca.markets')
    
    # News APIs
    newsapi_key: str = os.getenv('NEWSAPI_KEY', '')
    twitter_bearer_token: str = os.getenv('TWITTER_BEARER_TOKEN', '')
    reddit_client_id: str = os.getenv('REDDIT_CLIENT_ID', '')
    reddit_client_secret: str = os.getenv('REDDIT_CLIENT_SECRET', '')
    
    # Database
    database_url: str = os.getenv('DATABASE_URL', 'sqlite:///./episodic_pivot.db')


@dataclass
class PaperTradingConfig:
    """Paper trading configuration."""
    initial_capital: float = 100_000.0
    max_position_size_pct: float = 0.1  # Max 10% per position
    max_daily_loss_pct: float = 0.02  # Stop if down 2% daily
    take_profit_pct: float = 0.15  # Take profit at 15% gain
    stop_loss_pct: float = 0.05  # Stop loss at 5% loss


class Config:
    """Master configuration class."""
    scanner = ScannerConfig()
    backtest = BacktestConfig()
    alert = AlertConfig()
    data = DataConfig()
    paper_trading = PaperTradingConfig()


# Export for easy access
config = Config()
