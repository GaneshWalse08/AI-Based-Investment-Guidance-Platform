"""
Market Data Engine
Upgraded: Now tracks 150+ live companies across all major sectors.
"""
import yfinance as yf
import pandas as pd
import warnings

warnings.filterwarnings("ignore", category=FutureWarning)

# 150+ Major Companies Categorized by Sector
STOCKS = {
    # Technology (30)
    'AAPL': {'name': 'Apple Inc.', 'sector': 'Technology'}, 'MSFT': {'name': 'Microsoft Corp.', 'sector': 'Technology'},
    'GOOGL': {'name': 'Alphabet Inc.', 'sector': 'Technology'}, 'NVDA': {'name': 'NVIDIA Corp.', 'sector': 'Technology'},
    'META': {'name': 'Meta Platforms', 'sector': 'Technology'}, 'AMZN': {'name': 'Amazon.com', 'sector': 'Technology'},
    'TSLA': {'name': 'Tesla Inc.', 'sector': 'Technology'}, 'AMD': {'name': 'Advanced Micro Devices', 'sector': 'Technology'},
    'INTC': {'name': 'Intel Corp.', 'sector': 'Technology'}, 'CRM': {'name': 'Salesforce', 'sector': 'Technology'},
    'NFLX': {'name': 'Netflix Inc.', 'sector': 'Technology'}, 'ADBE': {'name': 'Adobe Inc.', 'sector': 'Technology'},
    'CSCO': {'name': 'Cisco Systems', 'sector': 'Technology'}, 'ORCL': {'name': 'Oracle Corp.', 'sector': 'Technology'},
    'TXN': {'name': 'Texas Instruments', 'sector': 'Technology'}, 'AVGO': {'name': 'Broadcom Inc.', 'sector': 'Technology'},
    'QCOM': {'name': 'Qualcomm Inc.', 'sector': 'Technology'}, 'IBM': {'name': 'IBM Corp.', 'sector': 'Technology'},
    'NOW': {'name': 'ServiceNow', 'sector': 'Technology'}, 'INTU': {'name': 'Intuit Inc.', 'sector': 'Technology'},
    'UBER': {'name': 'Uber Technologies', 'sector': 'Technology'}, 'ABNB': {'name': 'Airbnb Inc.', 'sector': 'Technology'},
    'SQ': {'name': 'Block Inc.', 'sector': 'Technology'}, 'SHOP': {'name': 'Shopify Inc.', 'sector': 'Technology'},
    'SNOW': {'name': 'Snowflake Inc.', 'sector': 'Technology'}, 'PLTR': {'name': 'Palantir Tech', 'sector': 'Technology'},
    'ROKU': {'name': 'Roku Inc.', 'sector': 'Technology'}, 'ZM': {'name': 'Zoom Video', 'sector': 'Technology'},
    'TWLO': {'name': 'Twilio Inc.', 'sector': 'Technology'}, 'DOCU': {'name': 'DocuSign', 'sector': 'Technology'},

    # Healthcare (25)
    'JNJ': {'name': 'Johnson & Johnson', 'sector': 'Healthcare'}, 'UNH': {'name': 'UnitedHealth', 'sector': 'Healthcare'},
    'PFE': {'name': 'Pfizer Inc.', 'sector': 'Healthcare'}, 'ABBV': {'name': 'AbbVie Inc.', 'sector': 'Healthcare'},
    'LLY': {'name': 'Eli Lilly', 'sector': 'Healthcare'}, 'MRK': {'name': 'Merck & Co.', 'sector': 'Healthcare'},
    'TMO': {'name': 'Thermo Fisher', 'sector': 'Healthcare'}, 'DHR': {'name': 'Danaher Corp.', 'sector': 'Healthcare'},
    'ABT': {'name': 'Abbott Labs', 'sector': 'Healthcare'}, 'BMY': {'name': 'Bristol-Myers', 'sector': 'Healthcare'},
    'AMGN': {'name': 'Amgen Inc.', 'sector': 'Healthcare'}, 'CVS': {'name': 'CVS Health', 'sector': 'Healthcare'},
    'SYK': {'name': 'Stryker Corp.', 'sector': 'Healthcare'}, 'ELV': {'name': 'Elevance Health', 'sector': 'Healthcare'},
    'CI': {'name': 'Cigna Group', 'sector': 'Healthcare'}, 'VRTX': {'name': 'Vertex Pharma', 'sector': 'Healthcare'},
    'REGN': {'name': 'Regeneron Pharma', 'sector': 'Healthcare'}, 'ZTS': {'name': 'Zoetis Inc.', 'sector': 'Healthcare'},
    'BSX': {'name': 'Boston Scientific', 'sector': 'Healthcare'}, 'BDX': {'name': 'Becton Dickinson', 'sector': 'Healthcare'},
    'HUM': {'name': 'Humana Inc.', 'sector': 'Healthcare'}, 'MCK': {'name': 'McKesson Corp.', 'sector': 'Healthcare'},
    'ILMN': {'name': 'Illumina Inc.', 'sector': 'Healthcare'}, 'IDXX': {'name': 'IDEXX Labs', 'sector': 'Healthcare'},
    'BIIB': {'name': 'Biogen Inc.', 'sector': 'Healthcare'},

    # Clean Energy (20)
    'NEE': {'name': 'NextEra Energy', 'sector': 'Clean Energy'}, 'ENPH': {'name': 'Enphase Energy', 'sector': 'Clean Energy'},
    'FSLR': {'name': 'First Solar', 'sector': 'Clean Energy'}, 'RUN': {'name': 'Sunrun Inc.', 'sector': 'Clean Energy'},
    'PLUG': {'name': 'Plug Power', 'sector': 'Clean Energy'}, 'SEDG': {'name': 'SolarEdge', 'sector': 'Clean Energy'},
    'BE': {'name': 'Bloom Energy', 'sector': 'Clean Energy'}, 'BLDP': {'name': 'Ballard Power', 'sector': 'Clean Energy'},
    'SPWR': {'name': 'SunPower Corp.', 'sector': 'Clean Energy'}, 'NOVA': {'name': 'Sunnova Energy', 'sector': 'Clean Energy'},
    'HASI': {'name': 'Hannon Armstrong', 'sector': 'Clean Energy'}, 'CWEN': {'name': 'Clearway Energy', 'sector': 'Clean Energy'},
    'BEP': {'name': 'Brookfield Renewable', 'sector': 'Clean Energy'}, 'NEP': {'name': 'NextEra Partners', 'sector': 'Clean Energy'},
    'AY': {'name': 'Atlantica Yield', 'sector': 'Clean Energy'}, 'VWDRY': {'name': 'Vestas Wind Systems', 'sector': 'Clean Energy'},
    'DQ': {'name': 'Daqo New Energy', 'sector': 'Clean Energy'}, 'JKS': {'name': 'JinkoSolar', 'sector': 'Clean Energy'},
    'CSIQ': {'name': 'Canadian Solar', 'sector': 'Clean Energy'}, 'FCEL': {'name': 'FuelCell Energy', 'sector': 'Clean Energy'},

    # Finance (25)
    'JPM': {'name': 'JPMorgan Chase', 'sector': 'Finance'}, 'BAC': {'name': 'Bank of America', 'sector': 'Finance'},
    'GS': {'name': 'Goldman Sachs', 'sector': 'Finance'}, 'BLK': {'name': 'BlackRock Inc.', 'sector': 'Finance'},
    'V': {'name': 'Visa Inc.', 'sector': 'Finance'}, 'MA': {'name': 'Mastercard', 'sector': 'Finance'},
    'MS': {'name': 'Morgan Stanley', 'sector': 'Finance'}, 'WFC': {'name': 'Wells Fargo', 'sector': 'Finance'},
    'C': {'name': 'Citigroup Inc.', 'sector': 'Finance'}, 'AXP': {'name': 'American Express', 'sector': 'Finance'},
    'SCHW': {'name': 'Charles Schwab', 'sector': 'Finance'}, 'SPGI': {'name': 'S&P Global', 'sector': 'Finance'},
    'PYPL': {'name': 'PayPal Holdings', 'sector': 'Finance'}, 'CME': {'name': 'CME Group', 'sector': 'Finance'},
    'CB': {'name': 'Chubb Limited', 'sector': 'Finance'}, 'MMC': {'name': 'Marsh & McLennan', 'sector': 'Finance'},
    'PNC': {'name': 'PNC Financial', 'sector': 'Finance'}, 'USB': {'name': 'US Bancorp', 'sector': 'Finance'},
    'TFC': {'name': 'Truist Financial', 'sector': 'Finance'}, 'COF': {'name': 'Capital One', 'sector': 'Finance'},
    'BK': {'name': 'Bank of New York', 'sector': 'Finance'}, 'STT': {'name': 'State Street', 'sector': 'Finance'},
    'AIG': {'name': 'American International Group', 'sector': 'Finance'}, 'MET': {'name': 'MetLife', 'sector': 'Finance'},
    'PRU': {'name': 'Prudential Financial', 'sector': 'Finance'},

    # Consumer Staples (18)
    'PG': {'name': 'Procter & Gamble', 'sector': 'Consumer Staples'}, 'KO': {'name': 'Coca-Cola', 'sector': 'Consumer Staples'},
    'WMT': {'name': 'Walmart Inc.', 'sector': 'Consumer Staples'}, 'PEP': {'name': 'PepsiCo', 'sector': 'Consumer Staples'},
    'COST': {'name': 'Costco Wholesale', 'sector': 'Consumer Staples'}, 'MCD': {'name': 'McDonald\'s', 'sector': 'Consumer Staples'},
    'NKE': {'name': 'Nike Inc.', 'sector': 'Consumer Staples'}, 'SBUX': {'name': 'Starbucks', 'sector': 'Consumer Staples'},
    'TGT': {'name': 'Target Corp.', 'sector': 'Consumer Staples'}, 'MDLZ': {'name': 'Mondelez', 'sector': 'Consumer Staples'},
    'PM': {'name': 'Philip Morris', 'sector': 'Consumer Staples'}, 'MO': {'name': 'Altria Group', 'sector': 'Consumer Staples'},
    'CL': {'name': 'Colgate-Palmolive', 'sector': 'Consumer Staples'}, 'KMB': {'name': 'Kimberly-Clark', 'sector': 'Consumer Staples'},
    'GIS': {'name': 'General Mills', 'sector': 'Consumer Staples'}, 'HSY': {'name': 'Hershey Co.', 'sector': 'Consumer Staples'},
    'K': {'name': 'Kellanova', 'sector': 'Consumer Staples'}, 'CPB': {'name': 'Campbell Soup', 'sector': 'Consumer Staples'},

    # Utilities (18)
    'DUK': {'name': 'Duke Energy', 'sector': 'Utilities'}, 'SO': {'name': 'Southern Co.', 'sector': 'Utilities'},
    'EXC': {'name': 'Exelon Corp.', 'sector': 'Utilities'}, 'AEP': {'name': 'Ameren Corp.', 'sector': 'Utilities'},
    'SRE': {'name': 'Sempra Energy', 'sector': 'Utilities'}, 'D': {'name': 'Dominion Energy', 'sector': 'Utilities'},
    'XEL': {'name': 'Xcel Energy', 'sector': 'Utilities'}, 'ED': {'name': 'Con Edison', 'sector': 'Utilities'},
    'PEG': {'name': 'Public Service Ent.', 'sector': 'Utilities'}, 'WEC': {'name': 'WEC Energy', 'sector': 'Utilities'},
    'AWK': {'name': 'American Water', 'sector': 'Utilities'}, 'ES': {'name': 'Eversource Energy', 'sector': 'Utilities'},
    'ETR': {'name': 'Entergy Corp.', 'sector': 'Utilities'}, 'FE': {'name': 'FirstEnergy', 'sector': 'Utilities'},
    'PPL': {'name': 'PPL Corp.', 'sector': 'Utilities'}, 'CMS': {'name': 'CMS Energy', 'sector': 'Utilities'},
    'LNT': {'name': 'Alliant Energy', 'sector': 'Utilities'}, 'ATO': {'name': 'Atmos Energy', 'sector': 'Utilities'},

    # Energy (18)
    'XOM': {'name': 'ExxonMobil', 'sector': 'Energy'}, 'CVX': {'name': 'Chevron', 'sector': 'Energy'},
    'COP': {'name': 'ConocoPhillips', 'sector': 'Energy'}, 'EOG': {'name': 'EOG Resources', 'sector': 'Energy'},
    'SLB': {'name': 'Schlumberger', 'sector': 'Energy'}, 'MPC': {'name': 'Marathon Petro', 'sector': 'Energy'},
    'PSX': {'name': 'Phillips 66', 'sector': 'Energy'}, 'VLO': {'name': 'Valero Energy', 'sector': 'Energy'},
    'OXY': {'name': 'Occidental Petro', 'sector': 'Energy'}, 'PXD': {'name': 'Pioneer Natural', 'sector': 'Energy'},
    'HES': {'name': 'Hess Corp.', 'sector': 'Energy'}, 'BKR': {'name': 'Baker Hughes', 'sector': 'Energy'},
    'HAL': {'name': 'Halliburton', 'sector': 'Energy'}, 'DVN': {'name': 'Devon Energy', 'sector': 'Energy'},
    'FANG': {'name': 'Diamondback Energy', 'sector': 'Energy'}, 'WMB': {'name': 'Williams Cos.', 'sector': 'Energy'},
    'KMI': {'name': 'Kinder Morgan', 'sector': 'Energy'}, 'OKE': {'name': 'ONEOK Inc.', 'sector': 'Energy'}
}

class DataService:
    def __init__(self):
        self._histories = {}
        self._build_histories()

    def _build_histories(self):
        print(f"📥 Fetching LIVE market data from Yahoo Finance for {len(STOCKS)} companies...")
        tickers = list(STOCKS.keys())
        
        # Download in chunks if needed, but 150 usually works in one fast batch
        data = yf.download(" ".join(tickers), period="1y", progress=False)
        
        for ticker in tickers:
            try:
                df = pd.DataFrame({
                    'Close': data['Close'][ticker],
                    'Open': data['Open'][ticker],
                    'High': data['High'][ticker],
                    'Low': data['Low'][ticker],
                    'Volume': data['Volume'][ticker]
                }).dropna()
                
                if df.empty: continue
                
                self._histories[ticker] = {
                    'dates': df.index.strftime('%Y-%m-%d').tolist(),
                    'prices': df['Close'].tolist(),
                    'open': df['Open'].tolist(),
                    'high': df['High'].tolist(),
                    'low': df['Low'].tolist(),
                    'volume': df['Volume'].tolist()
                }
            except Exception:
                pass
        print(f"✅ Live data loaded successfully for {len(self._histories)} companies!")

    def get_all_stocks(self):
        result = []
        for ticker, info in STOCKS.items():
            if ticker not in self._histories: continue
            hist = self._histories[ticker]
            if len(hist['prices']) < 2: continue
            
            price, prev = hist['prices'][-1], hist['prices'][-2]
            result.append({
                'ticker' : ticker, 'name': info['name'], 'sector': info['sector'],
                'price'  : round(price, 2), 'change' : round(price - prev, 2),
                'change_pct': round((price - prev) / prev * 100, 2),
            })
        return result

    def get_stock(self, ticker):
        if ticker not in STOCKS or ticker not in self._histories: return None
        info, hist = STOCKS[ticker], self._histories[ticker]
        price, prev = hist['prices'][-1], hist['prices'][-2]
        market_cap_estimate = round(price * 1.5, 2) 

        return {
            'ticker'    : ticker, 'name': info['name'], 'sector': info['sector'],
            'price'     : round(price, 2), 'change': round(price - prev, 2),
            'change_pct': round((price - prev) / prev * 100, 2),
            'open'      : round(hist['open'][-1], 2), 'high': round(hist['high'][-1], 2),
            'low'       : round(hist['low'][-1], 2), 'volume': int(hist['volume'][-1]),
            'market_cap': market_cap_estimate, 
        }

    def get_price_history(self, ticker):
        if ticker not in self._histories: return {'dates': [], 'prices': []}
        return {'dates': self._histories[ticker]['dates'], 'prices': [round(p, 2) for p in self._histories[ticker]['prices']]}

    def get_returns(self, ticker):
        hist = self._histories.get(ticker, {})
        p = hist.get('prices', [])
        return [round((p[i] - p[i-1]) / p[i-1], 6) for i in range(1, len(p))] if len(p) >= 2 else []

    def market_overview(self):
        all_s = self.get_all_stocks()
        if not all_s: return {}
        gainers = sorted(all_s, key=lambda x: x['change_pct'], reverse=True)[:3]
        losers  = sorted(all_s, key=lambda x: x['change_pct'])[:3]
        avg_chg = sum(s['change_pct'] for s in all_s) / len(all_s)
        return {
            'total_stocks': len(all_s), 'avg_market_change': round(avg_chg, 2),
            'market_mood': 'Positive' if avg_chg > 0 else 'Negative',
            'gainers': gainers, 'losers': losers, 'sectors': list({s['sector'] for s in all_s}),
        }

    @property
    def tickers(self): return [t for t in STOCKS.keys() if t in self._histories]

    @property
    def stocks(self): return STOCKS