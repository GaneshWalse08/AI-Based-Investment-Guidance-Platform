# ESGVision — AI-Powered ESG-Aware Sustainable Investment Decision Support System

## 🌿 Project Overview

A full-stack, modular, AI-driven investment decision support platform integrating:
- **Financial Analytics** (returns, volatility, Sharpe ratio, beta, max drawdown)
- **ESG Scoring Engine** (AAA–B ratings, sector comparisons, financial correlations)
- **Personalized Rankings** (filtered by risk, budget, sector, ESG priority)
- **Portfolio Simulation** (weighted metrics, benchmark comparison)
- **Mean-Variance Optimization** (Markowitz: max Sharpe / min vol / max return)
- **Efficient Frontier** visualization
- **News Sentiment Analysis** (Fear & Greed index, category sentiment)
- **KMeans Investor Clustering** (Sustainable Guardian / Balanced / Aggressive personas)
- **KMeans Stock Clustering** (grouped by financial + ESG characteristics)
- **Research Analytics** (ESG-financial correlation matrices, sector heatmaps)

---

## 🛠️ Technology Stack

| Layer      | Technology                                      |
|------------|-------------------------------------------------|
| Backend    | Python 3, Flask, Pandas, NumPy, SciPy, Scikit-learn |
| Frontend   | HTML5, CSS3, Vanilla JS, Chart.js 4.x           |
| AI/ML      | KMeans Clustering, Mean-Variance Optimization   |
| Data       | Realistic simulated OHLCV + ESG (swap for yfinance in production) |

---

## 📁 Folder Structure

```
AI_INVESTMENT_PROJECT/
├── backend/
│   ├── app.py                        ← Flask REST API (14 endpoints)
│   └── services/
│       ├── auth_service.py           ← User management
│       ├── data_service.py           ← Market data engine (GBM simulation)
│       ├── metrics_service.py        ← Financial metrics (Sharpe, volatility)
│       ├── esg_service.py            ← ESG scoring + correlation
│       ├── ranking_service.py        ← Combined ESG-financial ranking
│       ├── personalization_service.py← Preference-based filtering
│       ├── portfolio_service.py      ← Portfolio simulation
│       ├── optimization_service.py   ← Markowitz optimization
│       ├── clustering_service.py     ← KMeans clustering
│       └── news_service.py           ← News + sentiment analysis
├── frontend/
│   ├── index.html                    ← Landing + Auth page
│   └── dashboard.html                ← Full dashboard (7 modules)
└── README.md
```

---

## 🚀 Quick Start

### 1. Install dependencies
```bash
pip install flask pandas numpy scikit-learn scipy
```

### 2. Start the backend
```bash
cd AI_INVESTMENT_PROJECT/backend
python app.py
```
Server runs at: `http://localhost:5000`

### 3. Open the frontend
Open `frontend/index.html` in a browser **or** navigate to `http://localhost:5000`

### 4. Demo login
- **Username:** `demo_investor`
- **Password:** `demo1234`

---

## 📡 API Endpoints

| Method | Endpoint                         | Description                          |
|--------|----------------------------------|--------------------------------------|
| POST   | `/api/auth/register`             | User registration                    |
| POST   | `/api/auth/login`                | User login                           |
| GET    | `/api/stocks`                    | All stock prices & changes           |
| GET    | `/api/stocks/<ticker>`           | Stock detail + metrics + ESG         |
| GET    | `/api/esg/rankings`              | ESG ranked list (filter by sector)   |
| GET    | `/api/esg/correlation`           | ESG vs financial correlations        |
| GET    | `/api/rankings`                  | ESG-weighted financial rankings      |
| POST   | `/api/rankings/personalized`     | User preference-filtered rankings    |
| POST   | `/api/portfolio/simulate`        | Portfolio simulation                 |
| POST   | `/api/portfolio/optimize`        | Markowitz optimization               |
| POST   | `/api/portfolio/efficient_frontier` | Efficient frontier points         |
| GET    | `/api/news`                      | Market news + sentiment              |
| GET    | `/api/news/sentiment`            | Market sentiment summary             |
| GET    | `/api/clustering/investors`      | Investor behavioral clustering       |
| GET    | `/api/clustering/stocks`         | Stock characteristic clustering      |
| GET    | `/api/research/sector_heatmap`   | Sector ESG + financial heatmap       |
| GET    | `/api/dashboard/summary`         | Combined dashboard data              |

---

## 🔬 AI Modules

### 1. Financial Scoring Engine
- Normalized min-max scoring across: return, inverse-volatility, Sharpe ratio
- Combined with ESG weight (configurable 0–80%)
- Output: Invest / Hold / Avoid with natural language explanation

### 2. ESG Intelligence Engine
- Environmental (35%) + Social (35%) + Governance (30%) weighted composite
- Ratings: AAA, AA, A, BBB, BB, B
- Pearson correlation vs financial performance metrics

### 3. Personalization Engine
- Filters by: risk tolerance → volatility threshold mapping
- Adjusts ESG weight by user ESG priority level
- Sector whitelist filtering

### 4. Portfolio Optimizer (Markowitz)
- SciPy `minimize` with SLSQP solver
- Constraints: weights sum to 1, each asset 2%–60%
- Goals: maximize Sharpe / minimize volatility / maximize return
- Efficient frontier: 20-point curve across return range

### 5. KMeans Clustering
- **Investors**: features = [risk, ESG priority, duration, budget scale, n_sectors]
- **Stocks**: features = [return, volatility, Sharpe, ESG total, ESG environment]
- StandardScaler normalization before clustering
- Personas: Sustainable Guardian / Balanced Growth Seeker / Aggressive Alpha Hunter

---

## 📊 Stocks Covered (26 stocks, 8 sectors)

| Sector          | Tickers                     |
|-----------------|----------------------------|
| Technology      | AAPL, MSFT, GOOGL, NVDA, META |
| Healthcare      | JNJ, UNH, PFE, ABBV        |
| Clean Energy    | NEE, ENPH, FSLR, RUN       |
| Finance         | JPM, BAC, GS, BLK          |
| Consumer Staples| PG, KO, WMT                |
| Utilities       | DUK, SO                    |
| Energy          | XOM, CVX                   |
| Industrial      | CAT, HON                   |

---

## 🔄 Production Upgrades (Research Extension)

Replace `DataService._build_histories()` with:
```python
import yfinance as yf
data = yf.download(ticker, period='1y')
```

Replace `NewsService` with:
```python
import requests
response = requests.get(f'https://newsapi.org/v2/everything?q={ticker}&apiKey=...')
```

Add SHAP/LIME explainability:
```python
import shap
explainer = shap.TreeExplainer(model)
shap_values = explainer.shap_values(X)
```

---

## 📝 Academic Notes

- **Not a trading/brokerage platform** — decision support only
- Simulated data uses Geometric Brownian Motion with stock-specific beta values
- ESG scores modeled on real-world MSCI ESG ratings
- Portfolio optimization follows Markowitz (1952) mean-variance framework
- Clustering uses standardized feature vectors with k=3 (investors) and k=4 (stocks)
