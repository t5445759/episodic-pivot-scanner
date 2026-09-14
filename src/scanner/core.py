"""Core scanner logic for gap and volume detection."""
import pandas as pd
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from config.config import config
import asyncio


class StockScanner:
    """Main scanner for detecting gap up stocks with high volume."""
    
    def __init__(self, data_fetcher):
        """Initialize scanner with a data fetcher.
        
        Args:
            data_fetcher: Instance of DataFetcher (Yahoo or Alpaca)
        """
        self.fetcher = data_fetcher
        self.results = []
    
    async def scan_ticker(self, ticker: str) -> Optional[Dict]:
        """Scan a single ticker for episodic pivot criteria.
        
        Returns:
            Dictionary with scan results if criteria met, None otherwise
        """
        try:
            # Fetch current quote
            quote = await self.fetcher.fetch_quote(ticker)
            if not quote:
                return None
            
            # Fetch fundamentals
            fundamentals = await self.fetcher.fetch_fundamentals(ticker)
            if not fundamentals:
                return None
            
            # Fetch historical data for calculations
            hist_data = await self.fetcher.fetch_historical_data(ticker, period='3mo')
            if hist_data is None or hist_data.empty:
                return None
            
            # Apply filters
            if not self._passes_filters(quote, fundamentals, hist_data):
                return None
            
            # Calculate technical indicators
            sma_10 = self._calculate_sma(hist_data, 10)
            sma_20 = self._calculate_sma(hist_data, 20)
            relative_volume = self._calculate_relative_volume(hist_data)
            
            # Calculate performance
            week_perf = self._calculate_performance(hist_data, days=5)
            month_perf = self._calculate_performance(hist_data, days=20)
            
            result = {
                'ticker': ticker,
                'price': quote.get('price', 0),
                'gap_pct': quote.get('gap_pct', 0),
                'change_pct': quote.get('change_pct', 0),
                'volume': quote.get('volume', 0),
                'relative_volume': relative_volume,
                'market_cap': fundamentals.get('market_cap', 0),
                'market_cap_readable': fundamentals.get('market_cap_readable', 'N/A'),
                'sector': fundamentals.get('sector', 'Unknown'),
                'avg_volume_30d': fundamentals.get('avg_volume_30d', 0),
                'avg_dollar_volume': quote.get('price', 0) * fundamentals.get('avg_volume_30d', 0),
                'sma_10': sma_10,
                'sma_20': sma_20,
                'week_performance': week_perf,
                'month_performance': month_perf,
                'high': quote.get('high', 0),
                'low': quote.get('low', 0),
                'open': quote.get('open', 0),
                'prev_close': quote.get('prev_close', 0),
                'timestamp': quote.get('timestamp', datetime.now())
            }
            
            return result
            
        except Exception as e:
            print(f"Error scanning {ticker}: {e}")
            return None
    
    def _passes_filters(self, quote: Dict, fundamentals: Dict, hist_data: pd.DataFrame) -> bool:
        """Check if quote passes all filter criteria.
        
        Returns:
            True if all filters pass, False otherwise
        """
        cfg = config.scanner
        
        # Price filter
        price = quote.get('price', 0)
        if price < cfg.min_price or price > cfg.max_price:
            return False
        
        # Market cap filter
        market_cap = fundamentals.get('market_cap', 0)
        if market_cap < cfg.min_market_cap or market_cap > cfg.max_market_cap:
            return False
        
        # Gap filter
        gap_pct = quote.get('gap_pct', 0)
        if gap_pct < cfg.min_gap_pct:
            return False
        
        # Volume filter
        volume = quote.get('volume', 0)
        if volume < cfg.min_volume:
            return False
        
        # Relative volume filter
        avg_volume = hist_data['Volume'].mean()
        relative_volume = volume / avg_volume if avg_volume > 0 else 0
        if relative_volume < cfg.min_relative_volume:
            return False
        
        # Average dollar volume filter
        avg_dollar_volume = price * avg_volume
        if avg_dollar_volume < cfg.min_avg_dollar_volume:
            return False
        
        return True
    
    def _calculate_relative_volume(self, hist_data: pd.DataFrame) -> float:
        """Calculate relative volume (current / average)."""
        if hist_data.empty:
            return 0.0
        
        current_volume = hist_data['Volume'].iloc[-1]
        avg_volume = hist_data['Volume'].mean()
        
        return current_volume / avg_volume if avg_volume > 0 else 0.0
    
    def _calculate_sma(self, hist_data: pd.DataFrame, period: int) -> float:
        """Calculate simple moving average."""
        if hist_data.empty or len(hist_data) < period:
            return 0.0
        
        return hist_data['Close'].tail(period).mean()
    
    def _calculate_performance(self, hist_data: pd.DataFrame, days: int) -> float:
        """Calculate performance over N trading days."""
        if hist_data.empty or len(hist_data) < days:
            return 0.0
        
        current_price = hist_data['Close'].iloc[-1]
        past_price = hist_data['Close'].iloc[-days]
        
        return ((current_price - past_price) / past_price) * 100 if past_price > 0 else 0.0
    
    async def scan_universe(self, tickers: List[str]) -> List[Dict]:
        """Scan a universe of tickers.
        
        Args:
            tickers: List of ticker symbols to scan
            
        Returns:
            List of dictionaries containing results for stocks meeting criteria
        """
        self.results = []
        
        # Scan tickers concurrently
        tasks = [self.scan_ticker(ticker) for ticker in tickers]
        results = await asyncio.gather(*tasks)
        
        # Filter out None results and sort by score
        self.results = [r for r in results if r is not None]
        self.results = self._score_and_rank(self.results)
        
        return self.results
    
    def _score_and_rank(self, results: List[Dict]) -> List[Dict]:
        """Score and rank results by episodic pivot strength.
        
        Scoring factors:
        - Gap percentage (40%)
        - Relative volume (30%)
        - Price action (20%)
        - Market cap (10%)
        """
        for result in results:
            gap_score = min(result['gap_pct'] / config.scanner.min_gap_pct * 0.4, 0.4)
            vol_score = min(result['relative_volume'] / config.scanner.min_relative_volume * 0.3, 0.3)
            price_score = min(result['change_pct'] / 100 * 0.2, 0.2)  # Capped at 20% daily gain
            
            # Market cap score (larger caps slightly preferred for liquidity)
            mcap_score = min(result['market_cap'] / 1_000_000_000 * 0.1, 0.1)
            
            result['score'] = gap_score + vol_score + price_score + mcap_score
        
        # Sort by score descending
        return sorted(results, key=lambda x: x['score'], reverse=True)
    
    def get_results(self) -> List[Dict]:
        """Get latest scan results."""
        return self.results
