"""
Financial Metrics Service
Computes returns, volatility, Sharpe ratio, and correlation matrices.
"""
import math, statistics
import numpy as np

RISK_FREE_RATE = 0.05  # 5% annual


class MetricsService:
    def __init__(self, data_service):
        self._ds = data_service
        self._cache = {}
        self._compute_all()

    def _compute_all(self):
        for ticker in self._ds.tickers:
            self._cache[ticker] = self._compute(ticker)

    def _compute(self, ticker):
        returns = self._ds.get_returns(ticker)
        if len(returns) < 30:
            return {}

        hist   = self._ds.get_price_history(ticker)
        prices = hist['prices']

        # Returns
        ret_6m  = (prices[-1] - prices[-126]) / prices[-126] if len(prices) >= 126 else 0
        ret_1y  = (prices[-1] - prices[0])    / prices[0]
        ret_ytd = ret_1y  # simplified

        # Volatility (annualised std of daily returns)
        daily_vol  = statistics.stdev(returns)
        annual_vol = daily_vol * math.sqrt(252)

        # Sharpe ratio
        daily_rf   = RISK_FREE_RATE / 252
        excess     = [r - daily_rf for r in returns]
        sharpe     = (statistics.mean(excess) / statistics.stdev(excess)) * math.sqrt(252) if statistics.stdev(excess) > 0 else 0

        # Beta (vs synthetic market)
        market_r = 0.0003  # assumed market daily return
        cov      = statistics.mean([(r - statistics.mean(returns)) * (market_r - market_r) for r in returns])
        beta     = round(self._ds.stocks.get(ticker, {}).get('beta', 1.0), 2)

        return {
            'ticker'      : ticker,
            'return_6m'   : round(ret_6m   * 100, 2),
            'return_1y'   : round(ret_1y   * 100, 2),
            'return_ytd'  : round(ret_ytd  * 100, 2),
            'volatility'  : round(annual_vol * 100, 2),
            'daily_vol'   : round(daily_vol  * 100, 4),
            'sharpe'      : round(sharpe, 3),
            'beta'        : beta,
            'max_drawdown': round(self._max_drawdown(prices) * 100, 2),
        }

    def _max_drawdown(self, prices):
        peak = prices[0]
        max_dd = 0
        for p in prices:
            if p > peak:
                peak = p
            dd = (peak - p) / peak
            if dd > max_dd:
                max_dd = dd
        return max_dd

    def get_metrics(self, ticker):
        return self._cache.get(ticker, {})

    def get_all_metrics(self):
        return self._cache

    def correlation_matrix(self):
        tickers = self._ds.tickers
        matrix  = {}
        returns_map = {t: self._ds.get_returns(t) for t in tickers}
        min_len = min(len(v) for v in returns_map.values())
        for t1 in tickers:
            matrix[t1] = {}
            r1 = returns_map[t1][:min_len]
            for t2 in tickers:
                r2 = returns_map[t2][:min_len]
                # Pearson correlation
                n  = len(r1)
                m1, m2 = sum(r1)/n, sum(r2)/n
                num = sum((a - m1)*(b - m2) for a, b in zip(r1, r2))
                d1  = math.sqrt(sum((a - m1)**2 for a in r1))
                d2  = math.sqrt(sum((b - m2)**2 for b in r2))
                corr = round(num / (d1 * d2), 3) if d1 * d2 > 0 else 0
                matrix[t1][t2] = corr
        return {'matrix': matrix, 'tickers': tickers}
