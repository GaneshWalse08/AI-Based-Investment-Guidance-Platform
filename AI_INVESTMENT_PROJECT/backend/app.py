"""
AI-Powered ESG-Aware Sustainable Investment Decision Support System
Main Flask Application Entry Point
"""
from flask import Flask, request, jsonify, session
from flask import send_from_directory
import os, sys
from services.ml_service import MLService
sys.path.insert(0, os.path.dirname(__file__))

from services.auth_service import AuthService
from services.data_service import DataService
from services.metrics_service import MetricsService
from services.ranking_service import RankingService
from services.esg_service import ESGService
from services.personalization_service import PersonalizationService
from services.portfolio_service import PortfolioService
from services.optimization_service import OptimizationService
from services.clustering_service import ClusteringService
from services.news_service import NewsService
from services.chatbot_service import ChatbotService


app = Flask(__name__, static_folder='../frontend', static_url_path='')
app.secret_key = 'esg_invest_secret_2024'

# ── Initialize Services ──────────────────────────────────────────────────────
auth_svc          = AuthService()
data_svc          = DataService()
metrics_svc       = MetricsService(data_svc)
esg_svc           = ESGService()
ranking_svc       = RankingService(metrics_svc, esg_svc)
personal_svc      = PersonalizationService(ranking_svc, data_svc)
portfolio_svc     = PortfolioService(data_svc, esg_svc, metrics_svc)
optimization_svc  = OptimizationService(data_svc)
clustering_svc    = ClusteringService()
news_svc          = NewsService()
chatbot_svc       = ChatbotService()
ml_svc            = MLService(data_svc)

# ── CORS helper ───────────────────────────────────────────────────────────────
@app.after_request
def add_cors(response):
    response.headers['Access-Control-Allow-Origin']  = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
    response.headers['Access-Control-Allow-Methods'] = 'GET,POST,PUT,DELETE,OPTIONS'
    return response

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    frontend_dir = os.path.join(os.path.dirname(__file__), '..', 'frontend')
    if path and os.path.exists(os.path.join(frontend_dir, path)):
        return send_from_directory(frontend_dir, path)
    return send_from_directory(frontend_dir, 'index.html')

# ════════════════════════════════════════════════════════════════════════════
# AUTH ENDPOINTS
# ════════════════════════════════════════════════════════════════════════════
@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.json
    result = auth_svc.register(
        data.get('username'), data.get('email'),
        data.get('password'), data.get('preferences', {})
    )
    return jsonify(result)

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    result = auth_svc.login(data.get('username'), data.get('password'))
    if result['success']:
        session['user_id'] = result['user']['id']
    return jsonify(result)

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out'})

@app.route('/api/auth/profile', methods=['GET'])
def get_profile():
    user_id = request.args.get('user_id')
    return jsonify(auth_svc.get_profile(user_id))

@app.route('/api/auth/profile', methods=['PUT'])
def update_profile():
    data = request.json
    return jsonify(auth_svc.update_profile(data.get('user_id'), data.get('preferences', {})))

# ════════════════════════════════════════════════════════════════════════════
# MARKET DATA ENDPOINTS
# ════════════════════════════════════════════════════════════════════════════
@app.route('/api/stocks', methods=['GET'])
def get_all_stocks():
    return jsonify(data_svc.get_all_stocks())

@app.route('/api/stocks/<ticker>', methods=['GET'])
def get_stock_detail(ticker):
    stock   = data_svc.get_stock(ticker)
    metrics = metrics_svc.get_metrics(ticker)
    esg     = esg_svc.get_esg(ticker)
    return jsonify({'stock': stock, 'metrics': metrics, 'esg': esg})

@app.route('/api/stocks/<ticker>/history', methods=['GET'])
def get_stock_history(ticker):
    return jsonify(data_svc.get_price_history(ticker))

# ════════════════════════════════════════════════════════════════════════════
# ESG ENDPOINTS
# ════════════════════════════════════════════════════════════════════════════
@app.route('/api/esg/rankings', methods=['GET'])
def esg_rankings():
    sector = request.args.get('sector', 'all')
    return jsonify(esg_svc.get_rankings(sector))

@app.route('/api/esg/correlation', methods=['GET'])
def esg_correlation():
    return jsonify(esg_svc.get_esg_financial_correlation(metrics_svc))

@app.route('/api/esg/sectors', methods=['GET'])
def esg_sectors():
    return jsonify(esg_svc.get_sector_summary())

# ════════════════════════════════════════════════════════════════════════════
# RANKING ENDPOINTS
# ════════════════════════════════════════════════════════════════════════════
@app.route('/api/rankings', methods=['GET'])
def get_rankings():
    esg_weight = float(request.args.get('esg_weight', 0.4))
    sector     = request.args.get('sector', 'all')
    return jsonify(ranking_svc.compute_rankings(esg_weight=esg_weight, sector=sector))

@app.route('/api/rankings/personalized', methods=['POST'])
def personalized_rankings():
    prefs = request.json
    return jsonify(personal_svc.get_personalized(prefs))

# ════════════════════════════════════════════════════════════════════════════
# PORTFOLIO ENDPOINTS
# ════════════════════════════════════════════════════════════════════════════
@app.route('/api/portfolio/simulate', methods=['POST'])
def simulate_portfolio():
    data    = request.json
    tickers = data.get('tickers', [])
    weights = data.get('weights', None)
    return jsonify(portfolio_svc.simulate(tickers, weights))

@app.route('/api/portfolio/optimize', methods=['POST'])
def optimize_portfolio():
    data    = request.json
    tickers = data.get('tickers', [])
    goal    = data.get('goal', 'sharpe')
    return jsonify(optimization_svc.optimize(tickers, goal))

@app.route('/api/portfolio/efficient_frontier', methods=['POST'])
def efficient_frontier():
    data    = request.json
    tickers = data.get('tickers', [])
    return jsonify(optimization_svc.efficient_frontier(tickers))

# ════════════════════════════════════════════════════════════════════════════
# NEWS ENDPOINTS
# ════════════════════════════════════════════════════════════════════════════
@app.route('/api/news', methods=['GET'])
def get_news():
    ticker = request.args.get('ticker', None)
    return jsonify(news_svc.get_news(ticker))

@app.route('/api/news/sentiment', methods=['GET'])
def market_sentiment():
    return jsonify(news_svc.market_sentiment_summary())

# ════════════════════════════════════════════════════════════════════════════
# CLUSTERING ENDPOINTS
# ════════════════════════════════════════════════════════════════════════════
@app.route('/api/clustering/investors', methods=['GET'])
def cluster_investors():
    return jsonify(clustering_svc.cluster_investors(auth_svc.get_all_users()))

@app.route('/api/clustering/stocks', methods=['GET'])
def cluster_stocks():
    return jsonify(clustering_svc.cluster_stocks(metrics_svc, esg_svc))

# ════════════════════════════════════════════════════════════════════════════
# RESEARCH / ANALYTICS
# ════════════════════════════════════════════════════════════════════════════
@app.route('/api/research/correlation_matrix', methods=['GET'])
def correlation_matrix():
    return jsonify(metrics_svc.correlation_matrix())

@app.route('/api/ml/predict/<ticker>', methods=['GET'])
def predict_stock(ticker):
    days = int(request.args.get('days', 30))
    return jsonify(ml_svc.predict_price(ticker, days))

@app.route('/api/research/sector_heatmap', methods=['GET'])
def sector_heatmap():
    return jsonify(esg_svc.sector_heatmap(metrics_svc))

@app.route('/api/dashboard/summary', methods=['GET'])
def dashboard_summary():
    return jsonify({
        'market_overview'   : data_svc.market_overview(),
        'top_esg'           : esg_svc.get_rankings('all')[:5],
        'top_ranked'        : ranking_svc.compute_rankings()[:5],
        'sentiment'         : news_svc.market_sentiment_summary(),
        'recent_news'       : news_svc.get_news()[:6],
    })

    # ════════════════════════════════════════════════════════════════════════════
# DAILY AUTO UPDATE SCHEDULER
# ════════════════════════════════════════════════════════════════════════════
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
import os

def run_daily_updates():
    print("\n🔄 [AUTO-UPDATE] Running background data refresh...")
    try:
        # 1. Fetch new prices from Yahoo Finance
        data_svc._build_histories()
        
        # 2. Recalculate all financial metrics (Sharpe, Volatility, Returns)
        metrics_svc._compute_all()
        
        # 3. Fetch latest news & run VADER AI sentiment analysis
        news_svc._fetch_live_news()
        
        print("✅ [AUTO-UPDATE] Market data and news refreshed successfully!\n")
    except Exception as e:
        print(f"❌ [AUTO-UPDATE] Error during refresh: {e}\n")

# To prevent the scheduler from running twice when Flask's debug reloader is active
if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
    scheduler = BackgroundScheduler()
    # Runs automatically every 24 hours
    scheduler.add_job(func=run_daily_updates, trigger="interval", hours=24)
    scheduler.start()
    
    # Ensure the scheduler shuts down cleanly when you stop the Flask server
    atexit.register(lambda: scheduler.shutdown())

# Bonus: Manual trigger endpoint so you can test the update instantly!
@app.route('/api/admin/force_update', methods=['POST'])
def force_update():
    run_daily_updates()
    return jsonify({'success': True, 'message': 'System data refreshed successfully!'})

# ════════════════════════════════════════════════════════════════════════════
# CHATBOT ENDPOINT
# ════════════════════════════════════════════════════════════════════════════
@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '')
    if not user_message:
        return jsonify({'reply': 'Please ask a question.'})
        
    reply = chatbot_svc.get_response(user_message)
    return jsonify({'reply': reply})

# ════════════════════════════════════════════════════════════════════════════
# PORTFOLIO BUILDER
# ════════════════════════════════════════════════════════════════════════════
# ════════════════════════════════════════════════════════════════════════════
# MODEL PORTFOLIO ANALYZER
# ════════════════════════════════════════════════════════════════════════════
@app.route('/api/portfolio/analyze', methods=['POST'])
def analyze_portfolio():
    data = request.json
    holdings = data.get('holdings', [])
    return jsonify(portfolio_svc.analyze_portfolio(holdings))

if __name__ == '__main__':
    print("🚀 ESG Investment Platform starting on http://localhost:5000")
    app.run(debug=True, port=5000)
