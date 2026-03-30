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
@app.route('/api/portfolio/optimize_saved', methods=['POST'])
def optimize_saved_portfolio():
    data = request.json
    holdings = data.get('holdings', [])
    goal = data.get('goal', 'sharpe')
    
    if len(holdings) < 2:
        return jsonify({'success': False, 'message': 'You need at least 2 assets in a portfolio to optimize it.'})
        
    # 1. Analyze current portfolio to get exact current weights
    current_analysis = portfolio_svc.analyze_portfolio(holdings)
    tickers = [item['ticker'] for item in current_analysis.get('assets', [])]
    
    if len(tickers) < 2:
        return jsonify({'success': False, 'message': 'Not enough valid assets with historical data to run optimization.'})
    
    # 2. Run the math optimizer with a Safety Net
    try:
        optimal_result = optimization_svc.optimize(tickers, goal)
        
        # If the math engine returns an internal error, catch it here
        if 'error' in optimal_result:
            return jsonify({'success': False, 'message': f"Math Engine: {optimal_result['error']}"})
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Optimization crashed: {str(e)}'})
        
    # 3. Compare and generate detailed AI verdict
    comparison = []
    verdict_lines = []
    
    # Safely extract the optimal allocations
    allocations = optimal_result.get('allocation', [])
    opt_map = {a['ticker']: a['weight'] for a in allocations}
    
    for asset in current_analysis['assets']:
        ticker = asset['ticker']
        curr_weight = asset['weight']
        opt_weight = opt_map.get(ticker, 0.0)
        diff = opt_weight - curr_weight
        
        action = "HOLD"
        if diff > 3.0: 
            action = "BUY"
            verdict_lines.append(f"<li style='margin-bottom:0.5rem;'><strong>{ticker} (BUY):</strong> Increase your holding by <strong>{diff:.1f}%</strong>. The AI identifies this as mathematically essential to improve your risk-to-reward ratio.</li>")
        elif diff < -3.0: 
            if opt_weight <= 0.5:
                action = "REMOVE"
                verdict_lines.append(f"<li style='margin-bottom:0.5rem; color:#991b1b;'><strong>{ticker} (REMOVE):</strong> Liquidate entirely. The algorithm calculated that this asset drags down your portfolio's efficiency in the current market.</li>")
            else:
                action = "SELL"
                verdict_lines.append(f"<li style='margin-bottom:0.5rem;'><strong>{ticker} (SELL):</strong> Trim your position by <strong>{abs(diff):.1f}%</strong>. Reducing exposure here minimizes unnecessary volatility.</li>")
        else:
            verdict_lines.append(f"<li style='margin-bottom:0.5rem; color:#166534;'><strong>{ticker} (HOLD):</strong> Keep current allocation. It is already perfectly balanced.</li>")
            
        comparison.append({
            'ticker': ticker,
            'current_weight': curr_weight,
            'optimal_weight': opt_weight,
            'action': action
        })
        
    goal_text = "Maximize Sharpe Ratio (Best Risk/Reward)" if goal == "sharpe" else "Minimize Volatility (Safest)" if goal == "min_vol" else "Maximize Return (Most Aggressive)"
    verdict_html = f"To reach your goal to <strong>{goal_text}</strong>, the AI has calculated the mathematical ideal weights for your current assets. Here is what you need to do:<br><br><ul style='margin-left:1.5rem; margin-top:0.5rem;'>{''.join(verdict_lines)}</ul>"
    
    return jsonify({
        'success': True,
        'current_return': current_analysis['expected_return'],
        'optimal_result': optimal_result,
        'comparison': comparison,
        'verdict': verdict_html
    })


@app.route('/api/portfolio/efficient_frontier', methods=['POST'])
def efficient_frontier():
    data = request.json
    tickers = data.get('tickers', [])
    
    # Wrap this in a try/except so it NEVER crashes the server into an HTML error
    try:
        result = optimization_svc.efficient_frontier(tickers)
        return jsonify(result)
    except Exception as e:
        # Return empty arrays safely if the math engine fails
        return jsonify({'error': str(e), 'frontier': [], 'individual_stocks': []})

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
    # 1. Fetch all stocks (your DataService ALREADY calculates change_pct for us!)
    all_stocks = data_svc.get_all_stocks()
    
    # 2. Sort the stocks based on 'change_pct'
    # Gainers: Highest positive change first
    movers_sorted = sorted(all_stocks, key=lambda x: x.get('change_pct', 0), reverse=True)
    
    # Grab the top 10
    top_gainers = movers_sorted[:10]
    
    # Grab the bottom 10 (Losers) and reverse the list so the most negative is at the top
    top_losers = movers_sorted[-10:]
    top_losers.reverse()

    # 3. Return the payload with the new data
    return jsonify({
        'market_overview'   : data_svc.market_overview(),
        'top_esg'           : esg_svc.get_rankings('all')[:5],
        'top_ranked'        : ranking_svc.compute_rankings()[:5],
        'sentiment'         : news_svc.market_sentiment_summary(),
        'recent_news'       : news_svc.get_news()[:6],
        'top_gainers'       : top_gainers,      
        'top_losers'        : top_losers        
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
# GOAL-BASED INVESTING ENDPOINT
# ════════════════════════════════════════════════════════════════════════════
# ════════════════════════════════════════════════════════════════════════════
# GOAL-BASED INVESTING ENDPOINT
# ════════════════════════════════════════════════════════════════════════════
# ════════════════════════════════════════════════════════════════════════════
# GOAL-BASED INVESTING ENDPOINT
# ════════════════════════════════════════════════════════════════════════════
@app.route('/api/goals/plan', methods=['POST'])
def plan_goal():
    try:
        data = request.json
        goal_type = data.get('goal_type', 'Custom Goal')
        target = float(data.get('target_amount') or 500000)
        years = float(data.get('years') or 3)
        initial = float(data.get('initial_investment') or 0)

        if years <= 0:
            return jsonify({'success': False, 'message': 'Years must be greater than 0.'})

        if years < 3:
            strategy, risk_tolerance = "Conservative (Capital Preservation)", "low"
        elif years <= 7:
            strategy, risk_tolerance = "Balanced Growth", "moderate"
        else:
            strategy, risk_tolerance = "Aggressive Growth (Wealth Accumulation)", "high"

        ranked = ranking_svc.compute_rankings()
        valid = []
        for s in ranked:
            ret = s.get('return_1y')
            if ret is not None and float(ret) > 0:
                valid.append(s)

        if risk_tolerance == "low":
            valid = sorted(valid, key=lambda x: (float(x.get('volatility') or 0), -float(x.get('esg_total') or 0)))
        elif risk_tolerance == "moderate":
            valid = sorted(valid, key=lambda x: -float(x.get('sharpe') or 0))
        else:
            valid = sorted(valid, key=lambda x: -float(x.get('return_1y') or 0))

        selected_stocks = valid[:6]
        
        if not selected_stocks:
            return jsonify({'success': False, 'message': 'Not enough stock data available. Please click "Refresh Market Data" in the sidebar.'})

        if len(selected_stocks) >= 6:
            weights = [30, 25, 15, 10, 10, 10]
        else:
            weights = [100 // len(selected_stocks)] * len(selected_stocks)
            weights[0] += 100 - sum(weights) 
            
        portfolio = []
        raw_expected_return = 0
        
        for i, stock in enumerate(selected_stocks):
            weight = weights[i]
            stock_ret = float(stock.get('return_1y') or 0)
            raw_expected_return += (stock_ret * (weight / 100))
            
            portfolio.append({
                'ticker': stock['ticker'],
                'sector': stock.get('sector', 'Unknown'),
                'weight': weight,
                'return_1y': round(stock_ret, 2),
                'esg_rating': stock.get('esg_rating', 'N/A'),
                'investment_amount': round(initial * (weight / 100), 2)
            })

        if years >= 10:
            expected_port_return = min(raw_expected_return, 15.0)
        elif years >= 5:
            expected_port_return = min(raw_expected_return, 18.0)
        else:
            expected_port_return = raw_expected_return

        # 🚀 NEW REALISTIC VERDICT (No more millions projected)
        verdict = f"To reach your <strong>{goal_type}</strong> goal of ₹{target:,.0f} in {years} years, the AI has built a <strong>{strategy}</strong> portfolio. "
        verdict += f"This selection of {len(selected_stocks)} ESG-compliant stocks focuses on your timeframe and risk profile, targeting an expected annual return of <strong style='color:var(--moss);'>{expected_port_return:.1f}%</strong> based on historical data."

        return jsonify({
            'success': True,
            'expected_return': round(expected_port_return, 2),
            'strategy': strategy,
            'portfolio': portfolio,
            'verdict': verdict,
            'initial_invested': initial
        })
        
    except Exception as e:
        import traceback
        print("GOAL PLAN ERROR:", traceback.format_exc())
        return jsonify({'success': False, 'message': f'Server Math Error: {str(e)}'})
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

@app.route('/api/portfolio/save', methods=['POST'])
def save_user_portfolio():
    data = request.json
    user_id = data.get('user_id')
    name = data.get('name', 'My ESG Portfolio') # Now accepts a name
    portfolio_data = data.get('portfolio', [])
    
    if not user_id:
        return jsonify({'success': False, 'message': 'User ID is required.'})
        
    return jsonify(portfolio_svc.save_portfolio(user_id, name, portfolio_data))

@app.route('/api/portfolio/load', methods=['GET'])
def load_user_portfolio():
    user_id = request.args.get('user_id')
    
    if not user_id:
        return jsonify({'success': False, 'message': 'User ID is required.'})
        
    # Calls the new get_user_portfolios method which returns a list
    return jsonify(portfolio_svc.get_user_portfolios(user_id))

@app.route('/api/admin/seed_users', methods=['GET'])
def seed_users():
    """Generates dummy users so the clustering algorithm has data to work with."""
    dummy_profiles = [
        ("EcoWarrior", "low", "very_high", "5+ years", 50000, ["Clean Energy", "Healthcare"]),
        ("DayTrader", "high", "low", "< 1 year", 150000, ["Technology", "Finance"]),
        ("RetireeBob", "low", "medium", "5+ years", 500000, ["Consumer Staples", "Utilities"]),
        ("TechBro", "high", "low", "1-3 years", 20000, ["Technology"]),
        ("BalancedJane", "moderate", "high", "3-5 years", 75000, ["Clean Energy", "Technology", "Healthcare"])
    ]
    
    count = 0
    for username, risk, esg, dur, budget, sectors in dummy_profiles:
        # Check if user already exists to prevent duplicates
        existing = next((u for u in auth_svc.users.values() if u['username'] == username), None)
        if not existing:
            prefs = {
                'risk_tolerance': risk,
                'esg_priority': esg,
                'duration': dur,
                'budget': budget,
                'sectors': sectors
            }
            # Assuming your auth_svc.register takes these parameters
            auth_svc.register(username, f"{username.lower()}@demo.com", "password123", prefs)
            count += 1
            
    return jsonify({"success": True, "message": f"Successfully added {count} dummy users for clustering."})

if __name__ == '__main__':
    print("🚀 ESG Investment Platform starting on http://localhost:5000")
    app.run(debug=True, port=5000)
