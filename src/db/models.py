"""SQLAlchemy models for storing scan results and trades."""
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class ScanResult(Base):
    """Model for storing scan results."""
    __tablename__ = 'scan_results'
    
    id = Column(Integer, primary_key=True, index=True)
    scan_date = Column(DateTime, default=datetime.utcnow, index=True)
    ticker = Column(String(10), index=True)
    price = Column(Float)
    gap_pct = Column(Float)
    change_pct = Column(Float)
    volume = Column(Integer)
    relative_volume = Column(Float)
    market_cap = Column(Float)
    sector = Column(String(50))
    avg_dollar_volume = Column(Float)
    sma_10 = Column(Float)
    sma_20 = Column(Float)
    week_performance = Column(Float)
    month_performance = Column(Float)
    score = Column(Float)
    data = Column(JSON)  # Store full result as JSON


class Alert(Base):
    """Model for storing sent alerts."""
    __tablename__ = 'alerts'
    
    id = Column(Integer, primary_key=True, index=True)
    alert_date = Column(DateTime, default=datetime.utcnow, index=True)
    ticker = Column(String(10), index=True)
    alert_type = Column(String(50))  # 'gap_up', 'high_volume', etc.
    message = Column(Text)
    success = Column(Boolean, default=True)
    handler_type = Column(String(50))  # 'email', 'sms', 'webhook'
    data = Column(JSON)


class PaperTrade(Base):
    """Model for storing paper trades."""
    __tablename__ = 'paper_trades'
    
    id = Column(Integer, primary_key=True, index=True)
    trade_date = Column(DateTime, default=datetime.utcnow, index=True)
    ticker = Column(String(10), index=True)
    trade_type = Column(String(10))  # 'BUY' or 'SELL'
    price = Column(Float)
    shares = Column(Integer)
    commission = Column(Float)
    profit_loss = Column(Float, nullable=True)
    profit_loss_pct = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)
    data = Column(JSON)


class BacktestResult(Base):
    """Model for storing backtest results."""
    __tablename__ = 'backtest_results'
    
    id = Column(Integer, primary_key=True, index=True)
    backtest_date = Column(DateTime, default=datetime.utcnow, index=True)
    ticker = Column(String(10), index=True)
    start_date = Column(String(10))
    end_date = Column(String(10))
    initial_capital = Column(Float)
    final_capital = Column(Float)
    total_return_pct = Column(Float)
    buy_hold_return_pct = Column(Float)
    excess_return_pct = Column(Float)
    total_trades = Column(Integer)
    winning_trades = Column(Integer)
    losing_trades = Column(Integer)
    win_rate_pct = Column(Float)
    avg_win_pct = Column(Float)
    avg_loss_pct = Column(Float)
    profit_factor = Column(Float)
    data = Column(JSON)


class NewsArticle(Base):
    """Model for storing news articles for stocks."""
    __tablename__ = 'news_articles'
    
    id = Column(Integer, primary_key=True, index=True)
    fetch_date = Column(DateTime, default=datetime.utcnow, index=True)
    ticker = Column(String(10), index=True)
    title = Column(String(500))
    source = Column(String(100))
    url = Column(String(500), unique=True, index=True)
    published_at = Column(DateTime)
    description = Column(Text)
    sentiment = Column(String(20))  # 'positive', 'negative', 'neutral'
    sentiment_score = Column(Float)
    data = Column(JSON)
