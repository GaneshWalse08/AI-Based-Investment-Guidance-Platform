"""
Machine Learning Price Prediction Engine
Uses Scikit-Learn to train an auto-regressive model on live historical data 
and predict the price trend for the next 30 days.
"""
import numpy as np
from sklearn.linear_model import Ridge
from datetime import datetime, timedelta

class MLService:
    def __init__(self, data_svc):
        self._ds = data_svc

    def predict_price(self, ticker, future_days=30):
        # 1. Get live historical data from our DataService
        hist = self._ds.get_price_history(ticker)
        prices = hist.get('prices', [])
        dates = hist.get('dates', [])
        
        if len(prices) < 60:
            return {'error': 'Not enough data to train the ML model.'}

        # 2. Prepare Data for Machine Learning (Time-Series windowing)
        # We will use the past 10 days to predict the 11th day
        lookback = 10
        X, y = [], []
        for i in range(len(prices) - lookback):
            X.append(prices[i : i + lookback])
            y.append(prices[i + lookback])

        X = np.array(X)
        y = np.array(y)

        # 3. Train the Model (Ridge Regression handles multi-collinearity well)
        model = Ridge(alpha=1.0)
        model.fit(X, y)

        # 4. Predict the Future!
        future_prices = []
        # Start with the most recent 10 days of real prices
        current_input = prices[-lookback:] 
        
        for _ in range(future_days):
            # Predict tomorrow
            pred = model.predict([current_input])[0]
            future_prices.append(round(pred, 2))
            # Shift the window forward (drop oldest, add the new prediction)
            current_input = current_input[1:] + [pred]

        # 5. Generate Future Dates for the Chart
        last_date_str = dates[-1]
        try:
            last_date = datetime.strptime(last_date_str, '%Y-%m-%d')
        except ValueError:
            # Fallback if datetime format is different
            last_date = datetime.strptime(last_date_str[:10], '%Y-%m-%d')
            
        future_dates = [(last_date + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(1, future_days + 1)]

       # 6. Calculate ML Confidence & Trend metrics
        current_price = prices[-1]
        predicted_price = future_prices[-1]
        change_pct = round(((predicted_price - current_price) / current_price) * 100, 2)
        trend = "Positive (Bullish)" if change_pct > 0 else "Negative (Bearish)"

        # --- CURRENCY EXCHANGE ---
        USD_TO_INR = 83.50
        current_price_inr = round(current_price * USD_TO_INR, 2)
        predicted_price_inr = round(predicted_price * USD_TO_INR, 2)

        return {
            'ticker': ticker,
            'historical_dates': dates[-60:],   # Send last 60 days for context
            'historical_prices': prices[-60:], 
            'future_dates': future_dates,
            'future_prices': future_prices,
            'trend': trend,
            'change_pct': change_pct,
            'current_price': current_price,
            'predicted_price': predicted_price,
            'current_price_inr': current_price_inr,       # NEW
            'predicted_price_inr': predicted_price_inr    # NEW
        }