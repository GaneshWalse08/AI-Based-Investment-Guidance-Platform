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

    def _generate_market_verdict(self, avg_score, fg_index, category_avg, top_news):
        """Generates a highly detailed, multi-paragraph market commentary based on live news data."""
        if not top_news:
            return "Not enough market data to generate a reliable verdict."

        # 1. Macro Overview
        mood = "bullish" if avg_score > 0.05 else ("bearish" if avg_score < -0.05 else "cautious")
        fg_text = "extreme greed" if fg_index > 75 else ("greed" if fg_index > 55 else ("fear" if fg_index < 45 else ("extreme fear" if fg_index < 25 else "neutrality")))
        
        verdict = f"<strong>🌍 Macro Overview:</strong><br>The broader market sentiment is currently leaning <strong>{mood}</strong>, driven by an aggregate news score of {round(avg_score, 2)}. The Fear & Greed index sits at {fg_index}, indicating a state of market <strong>{fg_text}</strong>. "
        
        if avg_score > 0.1:
            verdict += "Investors are showing aggressive buying interest, largely dismissing macroeconomic headwinds in favor of recent positive catalysts.<br><br>"
        elif avg_score < -0.1:
            verdict += "Investors are in a risk-off defensive posture, reacting heavily to recent negative catalysts and rotating capital into safer assets.<br><br>"
        else:
            verdict += "The market is currently consolidating, waiting for stronger macroeconomic signals before committing to a decisive direction.<br><br>"

        # 2. Sector Analysis
        if category_avg:
            # Sort sectors by sentiment
            sorted_sectors = sorted(category_avg.items(), key=lambda x: x[1], reverse=True)
            top_sector, top_score = sorted_sectors[0]
            bottom_sector, bottom_score = sorted_sectors[-1]

            verdict += f"<strong>📊 Sector Impacts:</strong><br>"
            if top_score > 0.05:
                verdict += f"The <strong>{top_sector}</strong> sector is acting as a major market tailwind. Positive headlines in this space suggest that {top_sector} stocks are likely to see upward momentum and increased volume in the coming days as institutional money rotates here. "
            
            if bottom_score < -0.05 and bottom_sector != top_sector:
                verdict += f"Conversely, the <strong>{bottom_sector}</strong> sector is facing severe headwinds. Negative press in this area indicates potential sell-offs, and investors may want to trim exposure or set tighter stop-losses for {bottom_sector} equities.<br><br>"
            else:
                verdict += "<br><br>"

        # 3. Catalyst & Future Outlook
        most_impactful_headline = max(top_news, key=lambda x: abs(x['sentiment']))
        impact_dir = "positive" if most_impactful_headline['sentiment'] > 0 else "negative"
        
        verdict += f"<strong>🔮 AI Outlook & Catalyst:</strong><br>"
        verdict += f"A key catalyst driving current price action is: <em>'{most_impactful_headline['headline']}'</em> ({most_impactful_headline['source']}). "
        
        if impact_dir == "positive":
            verdict += f"This highly {impact_dir} development is creating a halo effect. If this momentum sustains, we anticipate short-term breakout opportunities, particularly in large-cap equities associated with this news. "
        else:
            verdict += f"This {impact_dir} event is creating systemic drag. Investors should brace for short-term volatility and consider hedging their portfolios until the fallout from this news is fully priced in."

        return verdict


    def market_sentiment_summary(self):
        if not self._news:
            return {
                'overall_score': 0, 'market_mood': 'Neutral', 'positive_count': 0,
                'negative_count': 0, 'neutral_count': 0, 'total_articles': 0,
                'category_sentiment': {}, 'fear_greed_index': 50,
                'market_verdict': 'No news available to analyze.'
            }

        sentiments = [n['sentiment'] for n in self._news]
        avg = sum(sentiments) / len(sentiments)
        
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
        fg_index = min(100, max(0, int((avg + 1) / 2 * 100)))

        # Generate the detailed narrative verdict
        verdict_text = self._generate_market_verdict(avg, fg_index, category_avg, self._news[:10])

        return {
            'overall_score'     : round(avg, 3),
            'market_mood'       : 'Positive' if avg > 0.05 else ('Negative' if avg < -0.05 else 'Neutral'),
            'positive_count'    : positive,
            'negative_count'    : negative,
            'neutral_count'     : neutral,
            'total_articles'    : len(self._news),
            'category_sentiment': category_avg,
            'fear_greed_index'  : fg_index,
            'market_verdict'    : verdict_text # <-- NEW FIELD ADDED
        }