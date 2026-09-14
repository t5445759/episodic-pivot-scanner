"""Base data fetcher interface."""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
import pandas as pd
from datetime import datetime, timedelta


class DataFetcher(ABC):
    """Abstract base class for data fetchers."""
    
    @abstractmethod
    async def fetch_quote(self, ticker: str) -> Optional[Dict]:
        """Fetch current quote for a ticker.
        
        Returns:
            Dictionary with keys: price, volume, change_pct, market_cap, gap_pct
        """
        pass
    
    @abstractmethod
    async def fetch_historical_data(self, ticker: str, period: str = '1y') -> Optional[pd.DataFrame]:
        """Fetch historical OHLCV data.
        
        Returns:
            DataFrame with columns: Open, High, Low, Close, Volume
        """
        pass
    
    @abstractmethod
    async def fetch_fundamentals(self, ticker: str) -> Optional[Dict]:
        """Fetch fundamental data.
        
        Returns:
            Dictionary with keys: market_cap, sector, float_shares, avg_volume
        """
        pass


class YahooFinanceFetcher(DataFetcher):
    """Yahoo Finance data fetcher."""
    
    def __init__(self):
        import yfinance as yf
        self.yf = yf
    
    async def fetch_quote(self, ticker: str) -> Optional[Dict]:
        """Fetch current quote from Yahoo Finance."""
        try:
            stock = self.yf.Ticker(ticker)
            info = stock.info
            
            prev_close = info.get('previousClose', 0)
            current_price = info.get('currentPrice') or info.get('regularMarketPrice', 0)
            current_volume = info.get('volume', 0)
            
            gap_pct = 0
            if prev_close > 0:
                gap_pct = ((current_price - prev_close) / prev_close) * 100
            
            return {
                'ticker': ticker,
                'price': current_price,
                'volume': current_volume,
                'change_pct': info.get('regularMarketChangePercent', 0),
                'market_cap': info.get('marketCap', 0),
                'gap_pct': gap_pct,
                'prev_close': prev_close,
                'open': info.get('open', 0),
                'high': info.get('dayHigh', 0),
                'low': info.get('dayLow', 0),
                'timestamp': datetime.now()
            }
        except Exception as e:
            print(f"Error fetching quote for {ticker}: {e}")
            return None
    
    async def fetch_historical_data(self, ticker: str, period: str = '1y') -> Optional[pd.DataFrame]:
        """Fetch historical data from Yahoo Finance."""
        try:
            stock = self.yf.Ticker(ticker)
            df = stock.history(period=period)
            return df
        except Exception as e:
            print(f"Error fetching historical data for {ticker}: {e}")
            return None
    
    async def fetch_fundamentals(self, ticker: str) -> Optional[Dict]:
        """Fetch fundamental data from Yahoo Finance."""
        try:
            stock = self.yf.Ticker(ticker)
            info = stock.info
            
            # Calculate average volume
            hist = stock.history(period='3mo')
            avg_volume = hist['Volume'].mean() if not hist.empty else 0
            
            return {
                'ticker': ticker,
                'market_cap': info.get('marketCap', 0),
                'sector': info.get('sector', 'Unknown'),
                'industry': info.get('industry', 'Unknown'),
                'float_shares': info.get('floatShares', 0),
                'avg_volume_30d': avg_volume,
                'pe_ratio': info.get('trailingPE', 0),
                'market_cap_readable': info.get('marketCapReadable', 'N/A')
            }
        except Exception as e:
            print(f"Error fetching fundamentals for {ticker}: {e}")
            return None


class AlpacaDataFetcher(DataFetcher):
    """Alpaca API data fetcher."""
    
    def __init__(self, api_key: str, secret_key: str, base_url: str):
        from alpaca.data.historical import StockHistoricalDataClient
        from alpaca.data.requests import StockLatestQuoteRequest, StockBarsRequest
        
        self.client = StockHistoricalDataClient(api_key, secret_key, url_base=base_url)
        self.quote_request = StockLatestQuoteRequest
        self.bars_request = StockBarsRequest
    
    async def fetch_quote(self, ticker: str) -> Optional[Dict]:
        """Fetch current quote from Alpaca."""
        try:
            request = self.quote_request(symbol_or_symbols=ticker)
            quotes = self.client.get_stock_latest_quote(request)
            
            if ticker in quotes:
                quote = quotes[ticker]
                return {
                    'ticker': ticker,
                    'price': quote.ask_price,
                    'bid': quote.bid_price,
                    'ask': quote.ask_price,
                    'timestamp': quote.timestamp
                }
        except Exception as e:
            print(f"Error fetching quote from Alpaca for {ticker}: {e}")
        return None
    
    async def fetch_historical_data(self, ticker: str, period: str = '1y') -> Optional[pd.DataFrame]:
        """Fetch historical bars from Alpaca."""
        try:
            from datetime import datetime, timedelta
            
            # Parse period
            if period == '1y':
                start_date = datetime.now() - timedelta(days=365)
            elif period == '3mo':
                start_date = datetime.now() - timedelta(days=90)
            elif period == '1mo':
                start_date = datetime.now() - timedelta(days=30)
            else:
                start_date = datetime.now() - timedelta(days=365)
            
            request = self.bars_request(
                symbol_or_symbols=ticker,
                start=start_date,
                timeframe='1day'
            )
            bars = self.client.get_stock_bars(request)
            
            if ticker in bars:
                df = bars[ticker].df
                return df
        except Exception as e:
            print(f"Error fetching historical data from Alpaca for {ticker}: {e}")
        return None
    
    async def fetch_fundamentals(self, ticker: str) -> Optional[Dict]:
        """Alpaca doesn't provide fundamentals; use Yahoo Finance fallback."""
        # Implement fallback to Yahoo Finance
        fetcher = YahooFinanceFetcher()
        return await fetcher.fetch_fundamentals(ticker)
