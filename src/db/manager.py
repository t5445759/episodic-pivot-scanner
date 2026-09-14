"""Database operations for managing scan results and trades."""
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Optional
from src.db.models import ScanResult, Alert, PaperTrade, BacktestResult, NewsArticle
import json


class DatabaseManager:
    """Manager for database operations."""
    
    def __init__(self, db: Session):
        """Initialize database manager.
        
        Args:
            db: SQLAlchemy session
        """
        self.db = db
    
    # ==================== Scan Results ====================
    
    def save_scan_result(self, result: dict) -> ScanResult:
        """Save a scan result to database.
        
        Args:
            result: Dictionary with scan result data
            
        Returns:
            ScanResult object
        """
        scan = ScanResult(
            scan_date=result.get('timestamp', datetime.utcnow()),
            ticker=result.get('ticker'),
            price=result.get('price'),
            gap_pct=result.get('gap_pct'),
            change_pct=result.get('change_pct'),
            volume=result.get('volume'),
            relative_volume=result.get('relative_volume'),
            market_cap=result.get('market_cap'),
            sector=result.get('sector'),
            avg_dollar_volume=result.get('avg_dollar_volume'),
            sma_10=result.get('sma_10'),
            sma_20=result.get('sma_20'),
            week_performance=result.get('week_performance'),
            month_performance=result.get('month_performance'),
            score=result.get('score'),
            data=result
        )
        self.db.add(scan)
        self.db.commit()
        self.db.refresh(scan)
        return scan
    
    def get_scan_results(self, ticker: str = None, limit: int = 100, days: int = 7) -> List[ScanResult]:
        """Get scan results.
        
        Args:
            ticker: Optional ticker filter
            limit: Maximum results to return
            days: Look back N days (default: 7)
            
        Returns:
            List of ScanResult objects
        """
        query = self.db.query(ScanResult)
        
        if ticker:
            query = query.filter(ScanResult.ticker == ticker)
        
        # Filter by date range
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        query = query.filter(ScanResult.scan_date >= cutoff_date)
        
        return query.order_by(ScanResult.scan_date.desc()).limit(limit).all()
    
    def get_top_scans_by_score(self, limit: int = 20, days: int = 1) -> List[ScanResult]:
        """Get top scan results by score.
        
        Args:
            limit: Maximum results
            days: Look back N days
            
        Returns:
            List of ScanResult objects sorted by score
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        return self.db.query(ScanResult).filter(
            ScanResult.scan_date >= cutoff_date
        ).order_by(ScanResult.score.desc()).limit(limit).all()
    
    # ==================== Alerts ====================
    
    def save_alert(self, alert: dict, success: bool = True, handler_type: str = 'email') -> Alert:
        """Save an alert to database.
        
        Args:
            alert: Dictionary with alert data
            success: Whether alert was sent successfully
            handler_type: Type of handler used ('email', 'sms', 'webhook')
            
        Returns:
            Alert object
        """
        alert_record = Alert(
            alert_date=datetime.utcnow(),
            ticker=alert.get('ticker'),
            alert_type='gap_up',  # Default type, can be extended
            message=json.dumps(alert),
            success=success,
            handler_type=handler_type,
            data=alert
        )
        self.db.add(alert_record)
        self.db.commit()
        self.db.refresh(alert_record)
        return alert_record
    
    def get_alerts(self, ticker: str = None, limit: int = 100, days: int = 7) -> List[Alert]:
        """Get alerts.
        
        Args:
            ticker: Optional ticker filter
            limit: Maximum results
            days: Look back N days
            
        Returns:
            List of Alert objects
        """
        query = self.db.query(Alert)
        
        if ticker:
            query = query.filter(Alert.ticker == ticker)
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        query = query.filter(Alert.alert_date >= cutoff_date)
        
        return query.order_by(Alert.alert_date.desc()).limit(limit).all()
    
    # ==================== Paper Trades ====================
    
    def save_trade(self, trade: dict) -> PaperTrade:
        """Save a paper trade to database.
        
        Args:
            trade: Dictionary with trade data
            
        Returns:
            PaperTrade object
        """
        paper_trade = PaperTrade(
            trade_date=trade.get('timestamp', datetime.utcnow()),
            ticker=trade.get('ticker'),
            trade_type=trade.get('type'),  # 'BUY' or 'SELL'
            price=trade.get('price'),
            shares=trade.get('shares'),
            commission=trade.get('cost', 0) - trade.get('proceeds', trade.get('cost', 0)) * 0.999,
            profit_loss=trade.get('profit_loss'),
            profit_loss_pct=trade.get('profit_loss_pct'),
            notes=trade.get('notes'),
            data=trade
        )
        self.db.add(paper_trade)
        self.db.commit()
        self.db.refresh(paper_trade)
        return paper_trade
    
    def get_trades(self, ticker: str = None, trade_type: str = None, limit: int = 100) -> List[PaperTrade]:
        """Get trades.
        
        Args:
            ticker: Optional ticker filter
            trade_type: Optional trade type filter ('BUY' or 'SELL')
            limit: Maximum results
            
        Returns:
            List of PaperTrade objects
        """
        query = self.db.query(PaperTrade)
        
        if ticker:
            query = query.filter(PaperTrade.ticker == ticker)
        
        if trade_type:
            query = query.filter(PaperTrade.trade_type == trade_type)
        
        return query.order_by(PaperTrade.trade_date.desc()).limit(limit).all()
    
    # ==================== Backtest Results ====================
    
    def save_backtest_result(self, result: dict) -> BacktestResult:
        """Save a backtest result to database.
        
        Args:
            result: Dictionary with backtest data
            
        Returns:
            BacktestResult object
        """
        backtest = BacktestResult(
            backtest_date=datetime.utcnow(),
            ticker=result.get('ticker'),
            start_date=result.get('start_date', ''),
            end_date=result.get('end_date', ''),
            initial_capital=result.get('initial_capital'),
            final_capital=result.get('final_capital'),
            total_return_pct=result.get('total_return_pct'),
            buy_hold_return_pct=result.get('buy_hold_return_pct'),
            excess_return_pct=result.get('excess_return_pct'),
            total_trades=result.get('total_trades'),
            winning_trades=result.get('winning_trades'),
            losing_trades=result.get('losing_trades'),
            win_rate_pct=result.get('win_rate_pct'),
            avg_win_pct=result.get('avg_win_pct'),
            avg_loss_pct=result.get('avg_loss_pct'),
            profit_factor=result.get('profit_factor'),
            data=result
        )
        self.db.add(backtest)
        self.db.commit()
        self.db.refresh(backtest)
        return backtest
    
    def get_backtest_results(self, ticker: str = None, limit: int = 100) -> List[BacktestResult]:
        """Get backtest results.
        
        Args:
            ticker: Optional ticker filter
            limit: Maximum results
            
        Returns:
            List of BacktestResult objects
        """
        query = self.db.query(BacktestResult)
        
        if ticker:
            query = query.filter(BacktestResult.ticker == ticker)
        
        return query.order_by(BacktestResult.backtest_date.desc()).limit(limit).all()
    
    # ==================== News Articles ====================
    
    def save_news_article(self, article: dict, ticker: str) -> NewsArticle:
        """Save a news article to database.
        
        Args:
            article: Dictionary with article data
            ticker: Stock ticker symbol
            
        Returns:
            NewsArticle object
        """
        news = NewsArticle(
            fetch_date=datetime.utcnow(),
            ticker=ticker,
            title=article.get('title'),
            source=article.get('source'),
            url=article.get('url'),
            published_at=article.get('published_at'),
            description=article.get('description'),
            sentiment=article.get('sentiment'),
            sentiment_score=article.get('sentiment_score', 0),
            data=article
        )
        self.db.add(news)
        self.db.commit()
        self.db.refresh(news)
        return news
    
    def get_news_articles(self, ticker: str, limit: int = 50, days: int = 30) -> List[NewsArticle]:
        """Get news articles for a ticker.
        
        Args:
            ticker: Stock ticker symbol
            limit: Maximum results
            days: Look back N days
            
        Returns:
            List of NewsArticle objects
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        return self.db.query(NewsArticle).filter(
            NewsArticle.ticker == ticker,
            NewsArticle.fetch_date >= cutoff_date
        ).order_by(NewsArticle.published_at.desc()).limit(limit).all()
