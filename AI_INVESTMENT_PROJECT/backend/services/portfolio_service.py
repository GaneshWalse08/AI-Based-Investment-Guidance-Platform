"""
Model Portfolio Analyzer
Calculates weighted historical returns, values, and ESG scores for a theoretical basket of stocks.
Upgraded: Includes SQLite integration for saving and loading multiple user portfolios.
"""
import sqlite3
import json
import os

# Point to the same database used by auth_service
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'esg_users.db')

class PortfolioService:
    def __init__(self, data_svc, esg_svc, metrics_svc):
        self._ds = data_svc
        self._esg = esg_svc
        self._metrics = metrics_svc
        self.USD_TO_INR = 83.50
        self._init_db() # Initialize the database table when the service starts

    # ── DATABASE METHODS ────────────────────────────────────────────────────────
    def _get_db_connection(self):
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_db_connection() as conn:
            # Table that allows multiple portfolios per user
            conn.execute('''
                CREATE TABLE IF NOT EXISTS saved_portfolios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    portfolio_data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()

    def save_portfolio(self, user_id, name, portfolio_data):
        try:
            with self._get_db_connection() as conn:
                conn.execute('''
                    INSERT INTO saved_portfolios (user_id, name, portfolio_data) 
                    VALUES (?, ?, ?)
                ''', (user_id, name, json.dumps(portfolio_data)))
                conn.commit()
            return {'success': True, 'message': f'Portfolio "{name}" saved successfully!'}
        except Exception as e:
            return {'success': False, 'message': str(e)}

    def get_user_portfolios(self, user_id):
        try:
            with self._get_db_connection() as conn:
                # Fetch ALL portfolios belonging to this user, newest first
                rows = conn.execute(
                    'SELECT id, name, portfolio_data, created_at FROM saved_portfolios WHERE user_id = ? ORDER BY created_at DESC', 
                    (user_id,)
                ).fetchall()
                
                portfolios = []
                for r in rows:
                    portfolios.append({
                        'id': r['id'],
                        'name': r['name'],
                        'data': json.loads(r['portfolio_data']),
                        'date': r['created_at']
                    })
                    
                return {'success': True, 'portfolios': portfolios}
        except Exception as e:
            return {'success': False, 'message': str(e)}

    # ── ANALYTICS METHODS ───────────────────────────────────────────────────────
    def analyze_portfolio(self, holdings):
        # holdings is a list of dicts from the frontend: [{'ticker': 'AAPL', 'shares': 10}]
        if not holdings:
            return {"total_value_inr": 0, "expected_return": 0, "esg_score": 0, "assets": []}

        total_value_usd = 0
        assets = []

        # First pass: Get live prices and calculate total value
        for item in holdings:
            ticker = item['ticker']
            shares = float(item['shares'])
            stock = self._ds.get_stock(ticker)
            if not stock: continue
            
            live_price = stock['price']
            value_usd = live_price * shares
            total_value_usd += value_usd
            
            assets.append({
                'ticker': ticker,
                'name': stock['name'],
                'sector': stock['sector'],
                'shares': shares,
                'price_usd': live_price,
                'value_usd': value_usd
            })

        if total_value_usd == 0:
            return {"total_value_inr": 0, "expected_return": 0, "esg_score": 0, "assets": []}

        # Second pass: Calculate weights, expected return, and ESG
        total_expected_return = 0
        total_esg = 0
        
        for asset in assets:
            weight = asset['value_usd'] / total_value_usd
            asset['weight'] = round(weight * 100, 2)
            
            # Get 1Y Historical Return
            mets = self._metrics.get_metrics(asset['ticker'])
            ret_1y = mets.get('return_1y', 0) if mets else 0
            
            # Get ESG Score
            esg_data = self._esg.get_esg(asset['ticker'])
            esg_tot = esg_data.get('total', 0) if esg_data else 0
            
            asset['return_1y'] = ret_1y
            asset['esg_total'] = esg_tot
            asset['esg_rating'] = esg_data.get('rating', 'N/A') if esg_data else 'N/A'
            asset['value_inr'] = round(asset['value_usd'] * self.USD_TO_INR, 2)
            
            total_expected_return += (ret_1y * weight)
            total_esg += (esg_tot * weight)

        # Return the fully analyzed model portfolio
        return {
            "total_value_inr": round(total_value_usd * self.USD_TO_INR, 2),
            "expected_return": round(total_expected_return, 2),
            "esg_score": round(total_esg, 1),
            "assets": sorted(assets, key=lambda x: x['value_usd'], reverse=True)
        }