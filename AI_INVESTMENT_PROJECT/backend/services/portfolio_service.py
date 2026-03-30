"""
Model Portfolio Analyzer
Calculates weighted historical returns, values, and ESG scores for a theoretical basket of stocks.
"""

class PortfolioService:
    def __init__(self, data_svc, esg_svc, metrics_svc):
        self._ds = data_svc
        self._esg = esg_svc
        self._metrics = metrics_svc
        self.USD_TO_INR = 83.50

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