"""
Portfolio Optimization Service
Mean-Variance Optimization (Markowitz) implemented with SciPy.
Goals: maximize Sharpe / minimize volatility / maximize ESG-adjusted return.
"""
import math, random
import numpy as np
from scipy.optimize import minimize

random.seed(7)

class OptimizationService:
    def __init__(self, data_svc):
        self._ds = data_svc

    def _get_returns_matrix(self, tickers):
        """Build (days x n_assets) matrix of daily returns."""
        all_returns = [self._ds.get_returns(t) for t in tickers]
        min_len = min(len(r) for r in all_returns)
        return np.array([r[:min_len] for r in all_returns])  # shape (n, days)

    def _portfolio_stats(self, weights, returns_matrix):
        w    = np.array(weights)
        mean_ret = returns_matrix.mean(axis=1)         # (n,)
        cov      = np.cov(returns_matrix)               # (n,n)
        port_ret = float(w @ mean_ret) * 252 * 100
        port_vol = float(np.sqrt(w @ cov @ w)) * math.sqrt(252) * 100
        sharpe   = (port_ret - 5) / port_vol if port_vol > 0 else 0
        return port_ret, port_vol, sharpe

    def optimize(self, tickers, goal='sharpe'):
        if len(tickers) < 2:
            return {'error': 'Need at least 2 tickers'}

        returns_matrix = self._get_returns_matrix(tickers)
        n = len(tickers)
        x0 = np.array([1/n] * n)
        bounds = [(0.02, 0.6)] * n                      # min 2%, max 60% per asset
        constraints = [{'type': 'eq', 'fun': lambda w: np.sum(w) - 1}]

        if goal == 'sharpe':
            def neg_sharpe(w):
                _, vol, sharpe = self._portfolio_stats(w, returns_matrix)
                return -sharpe
            result = minimize(neg_sharpe, x0, method='SLSQP',
                              bounds=bounds, constraints=constraints)
        elif goal == 'min_vol':
            def portfolio_vol(w):
                _, vol, _ = self._portfolio_stats(w, returns_matrix)
                return vol
            result = minimize(portfolio_vol, x0, method='SLSQP',
                              bounds=bounds, constraints=constraints)
        else:
            def neg_ret(w):
                ret, _, _ = self._portfolio_stats(w, returns_matrix)
                return -ret
            result = minimize(neg_ret, x0, method='SLSQP',
                              bounds=bounds, constraints=constraints)

        opt_weights = result.x
        port_ret, port_vol, sharpe = self._portfolio_stats(opt_weights, returns_matrix)

        allocation = [
            {'ticker': t, 'weight': round(float(w) * 100, 2)}
            for t, w in zip(tickers, opt_weights)
        ]
        allocation.sort(key=lambda x: x['weight'], reverse=True)

        return {
            'goal'          : goal,
            'allocation'    : allocation,
            'expected_return': round(port_ret, 2),
            'expected_vol'  : round(port_vol, 2),
            'sharpe_ratio'  : round(sharpe, 3),
            'success'       : bool(result.success),
        }

    def efficient_frontier(self, tickers, n_points=20):
        if len(tickers) < 2:
            return {'error': 'Need at least 2 tickers'}

        returns_matrix = self._get_returns_matrix(tickers)
        n   = len(tickers)
        bounds = [(0.02, 0.6)] * n
        constraints = [{'type': 'eq', 'fun': lambda w: np.sum(w) - 1}]

        all_rets, all_vols = [], []
        for t in tickers:
            m = self._ds.get_returns(t)
            ann_ret = np.mean(m) * 252 * 100
            ann_vol = np.std(m) * math.sqrt(252) * 100
            all_rets.append(ann_ret)
            all_vols.append(ann_vol)

        target_rets = np.linspace(min(all_rets), max(all_rets), n_points)
        frontier_points = []

        for target in target_rets:
            cons = constraints + [
                {'type': 'eq', 'fun': lambda w, r=target: self._portfolio_stats(w, returns_matrix)[0] - r}
            ]
            try:
                res = minimize(
                    lambda w: self._portfolio_stats(w, returns_matrix)[1],
                    np.array([1/n]*n), method='SLSQP',
                    bounds=bounds, constraints=cons
                )
                if res.success:
                    _, vol, sharpe = self._portfolio_stats(res.x, returns_matrix)
                    frontier_points.append({
                        'return': round(float(target), 2),
                        'vol'   : round(vol, 2),
                        'sharpe': round(sharpe, 3),
                    })
            except Exception:
                pass

        return {
            'frontier': frontier_points,
            'individual_stocks': [
                {'ticker': t, 'return': round(r, 2), 'vol': round(v, 2)}
                for t, r, v in zip(tickers, all_rets, all_vols)
            ],
        }
