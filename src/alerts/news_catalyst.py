"""News catalyst and sentiment analysis module."""
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import json


class NewsCatalystFetcher:
    """Fetch and analyze news catalysts for stocks."""
    
    def __init__(self, newsapi_key: str = None):
        """Initialize news fetcher.
        
        Args:
            newsapi_key: API key for NewsAPI
        """
        self.newsapi_key = newsapi_key
    
    async def fetch_news(self, ticker: str, company_name: str, limit: int = 5) -> List[Dict]:
        """Fetch recent news for a stock.
        
        Args:
            ticker: Stock ticker symbol
            company_name: Full company name
            limit: Maximum number of articles to fetch
            
        Returns:
            List of news articles with title, source, URL, date, summary
        """
        if not self.newsapi_key:
            print("⚠️  NewsAPI key not configured")
            return []
        
        try:
            import httpx
            from datetime import datetime, timedelta
            
            # Search for news about the company
            queries = [company_name, ticker]
            articles = []
            
            for query in queries:
                url = "https://newsapi.org/v2/everything"
                params = {
                    'q': query,
                    'sortBy': 'publishedAt',
                    'language': 'en',
                    'pageSize': limit,
                    'apiKey': self.newsapi_key
                }
                
                async with httpx.AsyncClient() as client:
                    response = await client.get(url, params=params)
                    
                    if response.status_code == 200:
                        data = response.json()
                        if 'articles' in data:
                            articles.extend(data['articles'])
            
            # Remove duplicates and format
            seen_urls = set()
            unique_articles = []
            
            for article in articles:
                url = article.get('url', '')
                if url not in seen_urls:
                    seen_urls.add(url)
                    unique_articles.append({
                        'title': article.get('title', 'N/A'),
                        'source': article.get('source', {}).get('name', 'Unknown'),
                        'url': url,
                        'published_at': article.get('publishedAt', ''),
                        'description': article.get('description', ''),
                        'image': article.get('urlToImage', '')
                    })
            
            return unique_articles[:limit]
            
        except Exception as e:
            print(f"❌ Error fetching news for {ticker}: {e}")
            return []
    
    async def analyze_sentiment(self, articles: List[Dict]) -> Dict:
        """Analyze sentiment of news articles (basic keyword-based).
        
        Args:
            articles: List of article dictionaries
            
        Returns:
            Dictionary with sentiment analysis results
        """
        if not articles:
            return {'sentiment': 'NEUTRAL', 'score': 0.0, 'articles_analyzed': 0}
        
        try:
            from transformers import pipeline
            
            # Use zero-shot classification for sentiment
            classifier = pipeline(
                "zero-shot-classification",
                model="facebook/bart-large-mnli"
            )
            
            sentiments = []
            scores = []
            
            for article in articles:
                text = article.get('title', '') + " " + article.get('description', '')
                
                if text.strip():
                    result = classifier(text, ['positive', 'negative', 'neutral'])
                    sentiments.append(result['labels'][0])
                    scores.append(result['scores'][0])
            
            # Calculate aggregate sentiment
            if sentiments:
                positive_count = sentiments.count('positive')
                negative_count = sentiments.count('negative')
                neutral_count = sentiments.count('neutral')
                
                sentiment_score = (positive_count - negative_count) / len(sentiments)
                
                if sentiment_score > 0.3:
                    overall_sentiment = 'POSITIVE'
                elif sentiment_score < -0.3:
                    overall_sentiment = 'NEGATIVE'
                else:
                    overall_sentiment = 'NEUTRAL'
                
                return {
                    'sentiment': overall_sentiment,
                    'score': sentiment_score,
                    'articles_analyzed': len(sentiments),
                    'positive_count': positive_count,
                    'negative_count': negative_count,
                    'neutral_count': neutral_count
                }
            
            return {'sentiment': 'NEUTRAL', 'score': 0.0, 'articles_analyzed': 0}
            
        except Exception as e:
            print(f"⚠️  Error analyzing sentiment: {e}")
            # Fallback to simple keyword-based sentiment
            return self._simple_sentiment_analysis(articles)
    
    def _simple_sentiment_analysis(self, articles: List[Dict]) -> Dict:
        """Simple keyword-based sentiment analysis."""
        positive_keywords = ['surge', 'soar', 'rally', 'profit', 'gain', 'beat', 'upgrade', 'approval', 'success']
        negative_keywords = ['plunge', 'crash', 'decline', 'loss', 'miss', 'downgrade', 'warning', 'recall', 'delay']
        
        positive_count = 0
        negative_count = 0
        
        for article in articles:
            text = (article.get('title', '') + " " + article.get('description', '')).lower()
            
            for keyword in positive_keywords:
                if keyword in text:
                    positive_count += 1
            
            for keyword in negative_keywords:
                if keyword in text:
                    negative_count += 1
        
        sentiment_score = (positive_count - negative_count) / max(len(articles), 1)
        
        if sentiment_score > 0.3:
            overall_sentiment = 'POSITIVE'
        elif sentiment_score < -0.3:
            overall_sentiment = 'NEGATIVE'
        else:
            overall_sentiment = 'NEUTRAL'
        
        return {
            'sentiment': overall_sentiment,
            'score': sentiment_score,
            'articles_analyzed': len(articles),
            'positive_count': positive_count,
            'negative_count': negative_count
        }
    
    async def get_catalyst_summary(self, ticker: str, company_name: str) -> Dict:
        """Get comprehensive catalyst summary for a stock.
        
        Args:
            ticker: Stock ticker symbol
            company_name: Full company name
            
        Returns:
            Dictionary with news articles and sentiment analysis
        """
        articles = await self.fetch_news(ticker, company_name)
        sentiment = await self.analyze_sentiment(articles)
        
        return {
            'ticker': ticker,
            'articles': articles,
            'sentiment': sentiment,
            'timestamp': datetime.now()
        }
