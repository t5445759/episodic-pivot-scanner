"""FastAPI web application for Episodic Pivot Scanner."""
from fastapi import FastAPI, HTTPException, Depends, WebSocket
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import asyncio
import json
from datetime import datetime

from config.config import config
from src.db.session import init_db, get_db, SessionLocal
from src.db.manager import DatabaseManager
from src.scanner.core import StockScanner
from src.data.fetcher import YahooFinanceFetcher
from src.backtest.backtester import EpisodicPivotBacktester
from src.trading.paper_trading import PaperTradingAccount
from src.alerts.news_catalyst import NewsCatalystFetcher
from src.orchestrator.orchestrator import EpisodicPivotOrchestrator

# Initialize FastAPI app
app = FastAPI(
    title="Episodic Pivot Scanner",
    description="Gap up stock screener with backtesting, alerts, and paper trading",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database
@app.on_event("startup")
def startup_event():
    init_db()


# ======================== Health & Status ========================

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Episodic Pivot Scanner API",
        "version": "0.1.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now()}


@app.get("/config")
async def get_config():
    """Get current configuration."""
    return {
        "scanner": {
            "min_price": config.scanner.min_price,
            "max_price": config.scanner.max_price,
            "min_market_cap": config.scanner.min_market_cap,
            "max_market_cap": config.scanner.max_market_cap,
            "min_gap_pct": config.scanner.min_gap_pct,
            "min_relative_volume": config.scanner.min_relative_volume,
            "min_volume": config.scanner.min_volume,
            "min_avg_dollar_volume": config.scanner.min_avg_dollar_volume
        },
        "backtest": {
            "initial_cash": config.backtest.initial_cash,
            "commission_pct": config.backtest.commission_pct,
            "position_size_pct": config.backtest.position_size_pct
        },
        "paper_trading": {
            "initial_capital": config.paper_trading.initial_capital,
            "take_profit_pct": config.paper_trading.take_profit_pct,
            "stop_loss_pct": config.paper_trading.stop_loss_pct
        }
    }


# ======================== Scanner Endpoints ========================

@app.post("/api/scan")
async def scan_stocks(tickers: List[str], db: Session = Depends(get_db)):
    """Scan stocks for episodic pivot criteria.
    
    Args:
        tickers: List of stock tickers to scan
        
    Returns:
        List of scan results
    """
    try:
        fetcher = YahooFinanceFetcher()
        scanner = StockScanner(fetcher)
        results = await scanner.scan_universe(tickers)
        
        db_manager = DatabaseManager(db)
        for result in results:
            db_manager.save_scan_result(result)
        
        return {
            "status": "success",
            "count": len(results),
            "results": results,
            "timestamp": datetime.now()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/scan/results")
async def get_scan_results(
    ticker: Optional[str] = None,
    limit: int = 100,
    days: int = 7,
    db: Session = Depends(get_db)
):
    """Get historical scan results.
    
    Args:
        ticker: Optional ticker filter
        limit: Maximum results to return
        days: Look back N days
        
    Returns:
        List of scan results
    """
    try:
        db_manager = DatabaseManager(db)
        results = db_manager.get_scan_results(ticker=ticker, limit=limit, days=days)
        
        return {
            "status": "success",
            "count": len(results),
            "results": [
                {
                    "id": r.id,
                    "scan_date": r.scan_date,
                    "ticker": r.ticker,
                    "price": r.price,
                    "gap_pct": r.gap_pct,
                    "change_pct": r.change_pct,
                    "volume": r.volume,
                    "relative_volume": r.relative_volume,
                    "market_cap": r.market_cap,
                    "sector": r.sector,
                    "score": r.score
                }
                for r in results
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/scan/top")
async def get_top_scans(
    limit: int = 20,
    days: int = 1,
    db: Session = Depends(get_db)
):
    """Get top scan results by score.
    
    Args:
        limit: Maximum results
        days: Look back N days
        
    Returns:
        List of top scan results sorted by score
    """
    try:
        db_manager = DatabaseManager(db)
        results = db_manager.get_top_scans_by_score(limit=limit, days=days)
        
        return {
            "status": "success",
            "count": len(results),
            "results": [
                {
                    "ticker": r.ticker,
                    "price": r.price,
                    "gap_pct": r.gap_pct,
                    "relative_volume": r.relative_volume,
                    "score": r.score,
                    "scan_date": r.scan_date
                }
                for r in results
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ======================== Backtest Endpoints ========================

@app.post("/api/backtest")
async def backtest_ticker(
    ticker: str,
    start_date: str,
    end_date: str,
    initial_capital: float = 100000,
    db: Session = Depends(get_db)
):
    """Run backtest for a ticker.
    
    Args:
        ticker: Stock ticker symbol
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        initial_capital: Initial capital for backtest
        
    Returns:
        Backtest results
    """
    try:
        backtester = EpisodicPivotBacktester(initial_capital)
        result = await backtester.backtest_ticker(ticker, start_date, end_date)
        
        if 'error' in result:
            raise HTTPException(status_code=400, detail=result['error'])
        
        # Save to database
        db_manager = DatabaseManager(db)
        result['start_date'] = start_date
        result['end_date'] = end_date
        db_manager.save_backtest_result(result)
        
        return {
            "status": "success",
            "result": result
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/backtest/results")
async def get_backtest_results(
    ticker: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get backtest results.
    
    Args:
        ticker: Optional ticker filter
        limit: Maximum results
        
    Returns:
        List of backtest results
    """
    try:
        db_manager = DatabaseManager(db)
        results = db_manager.get_backtest_results(ticker=ticker, limit=limit)
        
        return {
            "status": "success",
            "count": len(results),
            "results": [
                {
                    "id": r.id,
                    "ticker": r.ticker,
                    "start_date": r.start_date,
                    "end_date": r.end_date,
                    "total_return_pct": r.total_return_pct,
                    "buy_hold_return_pct": r.buy_hold_return_pct,
                    "excess_return_pct": r.excess_return_pct,
                    "win_rate_pct": r.win_rate_pct,
                    "total_trades": r.total_trades
                }
                for r in results
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ======================== Paper Trading Endpoints ========================

paper_account = PaperTradingAccount()  # Global account for demo


@app.post("/api/paper-trade/buy")
async def paper_buy(
    ticker: str,
    price: float,
    shares: int,
    db: Session = Depends(get_db)
):
    """Execute a paper trading buy order.
    
    Args:
        ticker: Stock ticker symbol
        price: Purchase price per share
        shares: Number of shares to buy
        
    Returns:
        Trade confirmation
    """
    try:
        success = paper_account.buy(ticker, price, shares)
        
        if success:
            db_manager = DatabaseManager(db)
            trade = {
                'ticker': ticker,
                'type': 'BUY',
                'price': price,
                'shares': shares,
                'cost': shares * price * (1 + config.backtest.commission_pct),
                'timestamp': datetime.now()
            }
            db_manager.save_trade(trade)
        
        return {
            "status": "success" if success else "failed",
            "message": f"{'BUY' if success else 'Failed to BUY'} {shares} {ticker} @ ${price:.2f}",
            "account_summary": paper_account.get_summary()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/paper-trade/sell")
async def paper_sell(
    ticker: str,
    price: float,
    shares: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Execute a paper trading sell order.
    
    Args:
        ticker: Stock ticker symbol
        price: Sale price per share
        shares: Number of shares to sell (optional, defaults to all)
        
    Returns:
        Trade confirmation
    """
    try:
        success = paper_account.sell(ticker, price, shares)
        
        if success:
            db_manager = DatabaseManager(db)
            trade = {
                'ticker': ticker,
                'type': 'SELL',
                'price': price,
                'shares': shares or 0,
                'proceeds': (shares or 0) * price * (1 - config.backtest.commission_pct),
                'timestamp': datetime.now()
            }
            db_manager.save_trade(trade)
        
        return {
            "status": "success" if success else "failed",
            "message": f"{'SELL' if success else 'Failed to SELL'} {shares or 'all'} {ticker} @ ${price:.2f}",
            "account_summary": paper_account.get_summary()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/paper-trade/account")
async def get_paper_account():
    """Get paper trading account summary.
    
    Returns:
        Account summary including cash, positions, P&L
    """
    return {
        "status": "success",
        "account": paper_account.get_summary(),
        "positions": paper_account.get_positions_summary()
    }


@app.get("/api/paper-trade/trades")
async def get_paper_trades(limit: int = 100):
    """Get paper trade history.
    
    Args:
        limit: Maximum trades to return
        
    Returns:
        List of trade records
    """
    return {
        "status": "success",
        "count": len(paper_account.trades),
        "trades": paper_account.get_trade_history(limit)
    }


# ======================== News & Catalyst Endpoints ========================

@app.get("/api/news/{ticker}")
async def get_stock_news(ticker: str, limit: int = 5, db: Session = Depends(get_db)):
    """Get news and sentiment for a stock.
    
    Args:
        ticker: Stock ticker symbol
        limit: Maximum articles to return
        
    Returns:
        News articles and sentiment analysis
    """
    try:
        fetcher = NewsCatalystFetcher(config.data.newsapi_key)
        summary = await fetcher.get_catalyst_summary(ticker, ticker)
        
        # Save articles to database
        db_manager = DatabaseManager(db)
        for article in summary['articles'][:limit]:
            db_manager.save_news_article(article, ticker)
        
        return {
            "status": "success",
            "ticker": ticker,
            "sentiment": summary['sentiment'],
            "articles": summary['articles'][:limit]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ======================== Dashboard ========================

@app.get("/dashboard")
async def get_dashboard():
    """Get dashboard HTML."""
    return HTMLResponse(content=get_dashboard_html())


def get_dashboard_html() -> str:
    """Generate dashboard HTML."""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Episodic Pivot Scanner Dashboard</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js"></script>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: #0f1419;
                color: #e0e6ed;
            }
            
            header {
                background: #1a1f2e;
                padding: 20px 40px;
                border-bottom: 2px solid #2ecc71;
                box-shadow: 0 2px 10px rgba(46, 204, 113, 0.2);
            }
            
            h1 {
                color: #2ecc71;
                font-size: 28px;
                display: flex;
                align-items: center;
                gap: 10px;
            }
            
            .container {
                max-width: 1400px;
                margin: 0 auto;
                padding: 30px 20px;
            }
            
            .grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }
            
            .card {
                background: #1a1f2e;
                border: 1px solid #2ecc71;
                border-radius: 8px;
                padding: 20px;
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
            }
            
            .card h2 {
                color: #2ecc71;
                margin-bottom: 15px;
                font-size: 18px;
            }
            
            .stat {
                display: flex;
                justify-content: space-between;
                padding: 10px 0;
                border-bottom: 1px solid #2c3e50;
            }
            
            .stat:last-child {
                border-bottom: none;
            }
            
            .stat-label {
                color: #a0a0a0;
            }
            
            .stat-value {
                color: #2ecc71;
                font-weight: bold;
            }
            
            .button {
                background: #2ecc71;
                color: #0f1419;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                cursor: pointer;
                font-weight: bold;
                margin-top: 15px;
                width: 100%;
                transition: background 0.3s;
            }
            
            .button:hover {
                background: #27ae60;
            }
            
            .chart-container {
                position: relative;
                height: 300px;
                margin-top: 20px;
            }
            
            table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
            }
            
            table th {
                background: #2c3e50;
                color: #2ecc71;
                padding: 12px;
                text-align: left;
                font-weight: bold;
            }
            
            table td {
                padding: 12px;
                border-bottom: 1px solid #2c3e50;
            }
            
            table tr:hover {
                background: #1e2333;
            }
            
            .positive {
                color: #2ecc71;
            }
            
            .negative {
                color: #e74c3c;
            }
            
            .icon {
                font-size: 20px;
            }
        </style>
    </head>
    <body>
        <header>
            <h1><span class="icon">🚀</span> Episodic Pivot Scanner Dashboard</h1>
        </header>
        
        <div class="container">
            <div class="grid">
                <div class="card">
                    <h2>📊 Today's Scans</h2>
                    <div class="stat">
                        <span class="stat-label">Total Matches</span>
                        <span class="stat-value">--</span>
                    </div>
                    <div class="stat">
                        <span class="stat-label">Avg Gap</span>
                        <span class="stat-value">--</span>
                    </div>
                    <div class="stat">
                        <span class="stat-label">Avg Volume (Relative)</span>
                        <span class="stat-value">--</span>
                    </div>
                    <button class="button">Run Scan Now</button>
                </div>
                
                <div class="card">
                    <h2>💼 Paper Trading Account</h2>
                    <div class="stat">
                        <span class="stat-label">Account Value</span>
                        <span class="stat-value">$100,000</span>
                    </div>
                    <div class="stat">
                        <span class="stat-label">P&L Today</span>
                        <span class="stat-value positive">+0.00%</span>
                    </div>
                    <div class="stat">
                        <span class="stat-label">Open Positions</span>
                        <span class="stat-value">0</span>
                    </div>
                    <button class="button">View Account</button>
                </div>
                
                <div class="card">
                    <h2>📈 Backtest Results</h2>
                    <div class="stat">
                        <span class="stat-label">Total Backtests</span>
                        <span class="stat-value">0</span>
                    </div>
                    <div class="stat">
                        <span class="stat-label">Avg Win Rate</span>
                        <span class="stat-value">--</span>
                    </div>
                    <div class="stat">
                        <span class="stat-label">Best Return</span>
                        <span class="stat-value positive">--</span>
                    </div>
                    <button class="button">Run Backtest</button>
                </div>
            </div>
            
            <div class="card">
                <h2>📋 Recent Scan Results</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Ticker</th>
                            <th>Price</th>
                            <th>Gap %</th>
                            <th>Volume (Relative)</th>
                            <th>Score</th>
                            <th>Timestamp</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td colspan="6" style="text-align: center; color: #a0a0a0;">No scan data yet. Run a scan to see results.</td>
                        </tr>
                    </tbody>
                </table>
            </div>
            
            <div class="card">
                <h2>🔔 Recent Alerts</h2>
                <p style="color: #a0a0a0;">No alerts sent yet.</p>
            </div>
        </div>
        
        <script>
            // Load data from API
            async function loadData() {
                try {
                    const response = await fetch('/api/scan/results?limit=20');
                    const data = await response.json();
                    
                    if (data.results) {
                        const tbody = document.querySelector('table tbody');
                        tbody.innerHTML = '';
                        
                        data.results.forEach(result => {
                            const row = `
                                <tr>
                                    <td>${result.ticker}</td>
                                    <td>$${result.price.toFixed(2)}</td>
                                    <td class="${result.gap_pct > 0 ? 'positive' : 'negative'}">${result.gap_pct.toFixed(2)}%</td>
                                    <td>${result.relative_volume.toFixed(2)}x</td>
                                    <td>${result.score.toFixed(3)}</td>
                                    <td>${new Date(result.scan_date).toLocaleString()}</td>
                                </tr>
                            `;
                            tbody.innerHTML += row;
                        });
                    }
                } catch (error) {
                    console.error('Error loading data:', error);
                }
            }
            
            // Load data on page load
            window.addEventListener('load', loadData);
            
            // Refresh data every 30 seconds
            setInterval(loadData, 30000);
        </script>
    </body>
    </html>
    """
