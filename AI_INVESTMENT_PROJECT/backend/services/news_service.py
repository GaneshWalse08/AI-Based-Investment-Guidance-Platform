"""
Daily Market News Module
Upgraded: Uses LIVE news from Finnhub API + VADER NLP Sentiment Analysis.
Includes an automatic fallback if the API key is missing or rate-limited.
"""
import requests
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from datetime import datetime, timedelta
import time
import os

# 🛑 PASTE YOUR FINNHUB API KEY HERE
FINNHUB_API_KEY = "d68loe9r01qq5rjg0g4gd68loe9r01qq5rjg0g50"

MARKET_LEADERS = ['AAPL', 'MSFT', 'JNJ', 'NEE', 'JPM', 'PG', 'DUK', 'XOM', 'CAT']

SECTOR_MAP = {
    'AAPL': 'Technology', 'MSFT': 'Technology',
    'JNJ': 'Healthcare', 'NEE': 'Clean Energy',
    'JPM': 'Finance', 'PG': 'Consumer Staples',
    'DUK': 'Utilities', 'XOM': 'Energy', 'CAT': 'Industrial'
}

# Fallback news in case the API is unavailable
FALLBACK_NEWS = [
    {'title': 'Tech stocks surge as AI demand grows globally', 'publisher': 'Reuters', 'ticker': 'MSFT'},
    {'title': 'Clean energy investments hit record high in Q3', 'publisher': 'Bloomberg', 'ticker': 'NEE'},
    {'title': 'Healthcare sector faces new regulatory challenges', 'publisher': 'WSJ', 'ticker': 'JNJ'},
    {'title': 'Bank earnings beat expectations despite inflation fears', 'publisher': 'CNBC', 'ticker': 'JPM'},
    {'title': 'Consumer spending slows down, impacting retail giants', 'publisher': 'Financial Times', 'ticker': 'PG'},
    {'title': 'Oil prices drop amidst global supply concerns', 'publisher': 'Reuters', 'ticker': 'XOM'},
    {'title': 'Industrial manufacturing sees slight decline this month', 'publisher': 'Bloomberg', 'ticker': 'CAT'},
    {'title': 'Apple announces breakthrough carbon-neutral supply chain', 'publisher': 'TechCrunch', 'ticker': 'AAPL'},
    {'title': 'Utility companies struggle with rising interest rates', 'publisher': 'WSJ', 'ticker': 'DUK'},
]

class NewsService:
    def __init__(self):
        self._news = []
        self._fetch_live_news()

    def _fetch_live_news(self):
        print("📰 Fetching LIVE news from Finnhub and analyzing VADER AI sentiment...")
        raw_news = []
        
        # Finnhub requires a date range for company news. Let's look at the last 3 days.
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d')
        
        if FINNHUB_API_KEY == "YOUR_FINNHUB_API_KEY_HERE" or not FINNHUB_API_KEY:
            print("⚠️ No Finnhub API key provided. Using fallback data.")
        else:
            for ticker in MARKET_LEADERS:
                try:
                    # Call the Finnhub Company News API endpoint
                    url = f"https://finnhub.io/api/v1/company-news?symbol={ticker}&from={start_date}&to={end_date}&token={FINNHUB_API_KEY}"
                    response = requests.get(url)
                    
                    if response.status_code == 200:
                        # Grab the top 5 most recent articles for this company
                        news_items = response.json()[:5] 
                        
                        for item in news_items:
                            headline = item.get('headline', '')
                            if not headline: 
                                continue
                            
                            pub_time = item.get('datetime', time.time())
                            
                            raw_news.append({
                                'headline': headline,
                                'ticker': ticker,
                                'category': SECTOR_MAP.get(ticker, 'General'),
                                'source': item.get('source', 'Financial News'),
                                'timestamp': datetime.fromtimestamp(pub_time).strftime('%Y-%m-%d %H:%M')
                            })
                    elif response.status_code == 429:
                        print("⚠️ Finnhub API rate limit reached.")
                        break # Stop trying if we hit the limit
                except Exception as e:
                    print(f"⚠️ Could not fetch Finnhub news for {ticker}: {e}")
                    pass
        
        # FALLBACK: If Finnhub returned nothing (or no key was provided), use our backup list
        if len(raw_news) == 0:
            print("⚠️ Finnhub returned no news. Using fallback data.")
            for i, item in enumerate(FALLBACK_NEWS):
                raw_news.append({
                    'headline': item['title'],
                    'ticker': item['ticker'],
                    'category': SECTOR_MAP.get(item['ticker'], 'General'),
                    'source': item['publisher'],
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M')
                })

        # Apply AI Sentiment Analysis using VADER NLP
        analyzer = SentimentIntensityAnalyzer()
        for n in raw_news:
            # VADER returns a dictionary. The 'compound' score is between -1.0 and 1.0
            sentiment_dict = analyzer.polarity_scores(n['headline'])
            n['sentiment'] = sentiment_dict['compound']
            
        self._news = self._enrich(raw_news)
        print(f"✅ Loaded and analyzed {len(self._news)} news articles with VADER!")

    def _enrich(self, news_list):
        result = []
        for n in news_list:
            s = n['sentiment']
            
            # Divide into Positive, Negative, Neutral based on VADER AI score
            if s > 0.05:
                label = 'Positive'
            elif s < -0.05:
                label = 'Negative'
            else:
                label = 'Neutral'
            
            result.append({
                **n,
                'sentiment_label': label,
                'sentiment_pct': round(abs(s) * 100, 1),
            })
            
        # Sort by newest first
        result.sort(key=lambda x: x['timestamp'], reverse=True)
        return result

    def get_news(self, ticker=None):
        if ticker:
            filtered = [n for n in self._news if n.get('ticker') == ticker]
            return filtered[:10]
        return self._news[:25] 

    def market_sentiment_summary(self):
        if not self._news:
            return {
                'overall_score': 0, 'market_mood': 'Neutral', 'positive_count': 0,
                'negative_count': 0, 'neutral_count': 0, 'total_articles': 0,
                'category_sentiment': {}, 'fear_greed_index': 50
            }

        sentiments = [n['sentiment'] for n in self._news]
        avg = sum(sentiments) / len(sentiments)
        
        # Adjusting the summary thresholds to match VADER's sensitivity
        positive = sum(1 for s in sentiments if s > 0.05)
        negative = sum(1 for s in sentiments if s < -0.05)
        neutral  = len(sentiments) - positive - negative

        category_sentiment = {}
        for n in self._news:
            cat = n['category']
            if cat not in category_sentiment:
                category_sentiment[cat] = []
            category_sentiment[cat].append(n['sentiment'])
            
        category_avg = {c: round(sum(v)/len(v), 3) for c, v in category_sentiment.items()}

        return {
            'overall_score'     : round(avg, 3),
            'market_mood'       : 'Positive' if avg > 0.05 else ('Negative' if avg < -0.05 else 'Neutral'),
            'positive_count'    : positive,
            'negative_count'    : negative,
            'neutral_count'     : neutral,
            'total_articles'    : len(self._news),
            'category_sentiment': category_avg,
            'fear_greed_index'  : min(100, max(0, int((avg + 1) / 2 * 100))),
        }