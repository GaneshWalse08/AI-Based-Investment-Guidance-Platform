"""
Model Portfolio Analyzer
Calculates weighted historical returns, values, and ESG scores for a theoretical basket of stocks.
Upgraded: Now includes SQLite integration for saving/loading user portfolios.
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

    # --- Database Methods ---
    def _get_db_connection(self):
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_db_connection() as conn:
            # Creates a table linking a user's ID to their portfolio JSON data
            conn.execute('''
                CREATE TABLE IF NOT EXISTS portfolios (
                    user_id TEXT PRIMARY KEY,
                    portfolio_data TEXT NOT NULL
                )
            ''')
            conn.commit()

    def save_portfolio(self, user_id, portfolio_data):
        try:
            with self._get_db_connection() as conn:
                # Upsert command: Inserts a new record, or updates it if the user_id already exists
                conn.execute('''
                    INSERT INTO portfolios (user_id, portfolio_data) 
                    VALUES (?, ?)
                    ON CONFLICT(user_id) DO UPDATE SET portfolio_data=excluded.portfolio_data
                ''', (user_id, json.dumps(portfolio_data)))
                conn.commit()
            return {'success': True, 'message': 'Portfolio saved securely to database!'}
        except Exception as e:
            return {'success': False, 'message': str(e)}

    def load_portfolio(self, user_id):
        with self._get_db_connection() as conn:
            row = conn.execute('SELECT portfolio_data FROM portfolios WHERE user_id = ?', (user_id,)).fetchone()
            if row:
                return {'success': True, 'portfolio': json.loads(row['portfolio_data'])}
            return {'success': False, 'message': 'No saved portfolio found.'}

    # --- Analytics Methods (Unchanged) ---
    def analyze_portfolio(self, holdings):
        if not holdings:
            return {"total_value_inr": 0, "expected_return": 0, "esg_score": 0, "assets": []}

        total_value_usd = 0
        assets = []

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

        total_expected_return = 0
        total_esg = 0
        
        for asset in assets:
            weight = asset['value_usd'] / total_value_usd
            asset['weight'] = round(weight * 100, 2)
            
            mets = self._metrics.get_metrics(asset['ticker'])
            ret_1y = mets.get('return_1y', 0) if mets else 0
            
            esg_data = self._esg.get_esg(asset['ticker'])
            esg_tot = esg_data.get('total', 0) if esg_data else 0
            
            asset['return_1y'] = ret_1y
            asset['esg_total'] = esg_tot
            asset['esg_rating'] = esg_data.get('rating', 'N/A') if esg_data else 'N/A'
            asset['value_inr'] = round(asset['value_usd'] * self.USD_TO_INR, 2)
            
            total_expected_return += (ret_1y * weight)
            total_esg += (esg_tot * weight)

        return {
            "total_value_inr": round(total_value_usd * self.USD_TO_INR, 2),
            "expected_return": round(total_expected_return, 2),
            "esg_score": round(total_esg, 1),
            "assets": sorted(assets, key=lambda x: x['value_usd'], reverse=True)
        }