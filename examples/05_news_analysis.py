"""Example 5: News & Sentiment Analysis

This example demonstrates news fetching and sentiment analysis.
"""

import asyncio
from src.alerts.news_catalyst import NewsCatalystFetcher
from config.config import config


async def main():
    """Run news example."""
    print("\n📰 Example 5: News & Sentiment Analysis\n")
    print("="*80)
    
    # Create news fetcher (requires NEWSAPI_KEY in .env)
    fetcher = NewsCatalystFetcher(config.data.newsapi_key)
    
    # Get news and sentiment for a stock
    ticker = 'NVDA'
    company_name = 'NVIDIA Corporation'
    
    print(f"\n📍 Fetching news for {company_name} ({ticker})...\n")
    
    summary = await fetcher.get_catalyst_summary(ticker, company_name)
    
    # Display sentiment
    sentiment = summary['sentiment']
    print(f"📊 Sentiment Analysis:")
    print(f"   Overall: {sentiment['sentiment']}")
    print(f"   Score: {sentiment['score']:.2f}")
    print(f"   Positive: {sentiment.get('positive_count', 0)}")
    print(f"   Negative: {sentiment.get('negative_count', 0)}")
    print(f"   Neutral: {sentiment.get('neutral_count', 0)}")
    
    # Display articles
    if summary['articles']:
        print(f"\n📄 Recent Articles (Top 5):\n")
        for i, article in enumerate(summary['articles'][:5], 1):
            print(f"{i}. {article['title']}")
            print(f"   Source: {article['source']}")
            print(f"   Date: {article['published_at']}")
            print(f"   URL: {article['url']}\n")
    else:
        print("\n⚠️  No articles found (check NEWSAPI_KEY in .env)")


if __name__ == "__main__":
    asyncio.run(main())
