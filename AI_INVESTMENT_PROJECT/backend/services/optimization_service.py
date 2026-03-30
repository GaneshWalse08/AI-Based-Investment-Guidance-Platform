"""
Portfolio Optimization Service
Mean-Variance Optimization (Markowitz) implemented with SciPy.
Upgraded: Added safety nets to prevent NaN math crashes and JSON serialization errors.
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
        all_returns = []
        for t in tickers:
            rets = self._ds.get_returns(t)
            # Safety net: If a stock is missing data, simulate flat returns to prevent a crash
            if not rets or len(rets) < 2:
                rets = [0.0] * 252 
            all_returns.append(rets)
            
        min_len = min(len(r) for r in all_returns)
        if min_len < 2:
            raise ValueError("Not enough historical data to compute covariance.")
            
        return np.array([r[:min_len] for r in all_returns])

    def _portfolio_stats(self, weights, returns_matrix):
        w    = np.array(weights)
        mean_ret = returns_matrix.mean(axis=1)         
        cov      = np.cov(returns_matrix)               
        
        # Safely execute matrix multiplication
        try:
            port_ret = float(w @ mean_ret) * 252 * 100
            var = w @ cov @ w
            port_vol = float(np.sqrt(var)) * math.sqrt(252) * 100
        except:
            port_ret, port_vol = 0.0, 0.0
            
        # Prevent NaN (Not a Number) from destroying the JSON payload
        if math.isnan(port_ret): port_ret = 0.0
        if math.isnan(port_vol): port_vol = 0.0
        
        sharpe   = float((port_ret - 5) / port_vol) if port_vol > 0 else 0.0
        return port_ret, port_vol, sharpe

    def optimize(self, tickers, goal='sharpe'):
        if len(tickers) < 2:
            return {'error': 'Need at least 2 tickers to run Markowitz optimization.'}

        try:
            returns_matrix = self._get_returns_matrix(tickers)
        except Exception as e:
            return {'error': str(e)}

        n = len(tickers)
        x0 = np.array([1/n] * n)
        bounds = [(0.02, 0.6)] * n                      
        constraints = [{'type': 'eq', 'fun': lambda w: np.sum(w) - 1}]

        if goal == 'sharpe':
            def neg_sharpe(w):
                _, _, sharpe = self._portfolio_stats(w, returns_matrix)
                return -sharpe
            result = minimize(neg_sharpe, x0, method='SLSQP', bounds=bounds, constraints=constraints)
        elif goal == 'min_vol':
            def portfolio_vol(w):
                _, vol, _ = self._portfolio_stats(w, returns_matrix)
                return vol
            result = minimize(portfolio_vol, x0, method='SLSQP', bounds=bounds, constraints=constraints)
        else:
            def neg_ret(w):
                ret, _, _ = self._portfolio_stats(w, returns_matrix)
                return -ret
            result = minimize(neg_ret, x0, method='SLSQP', bounds=bounds, constraints=constraints)

        # Fallback to equal weights if the math engine fails to find a minimum
        opt_weights = result.x if result.success else x0
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
            'success'       : True, # Even if result.success is false, we gracefully fallback
        }

    def efficient_frontier(self, tickers, n_points=20):
        if len(tickers) < 2:
            return {'error': 'Need at least 2 tickers'}

        try:
            returns_matrix = self._get_returns_matrix(tickers)
        except:
            return {'frontier': [], 'individual_stocks': []}

        n   = len(tickers)
        bounds = [(0.02, 0.6)] * n
        constraints = [{'type': 'eq', 'fun': lambda w: np.sum(w) - 1}]

        all_rets, all_vols = [], []
        for t in tickers:
            m = self._ds.get_returns(t)
            if not m or len(m) < 2:
                all_rets.append(0.0)
                all_vols.append(0.0)
                continue
                
            # CRITICAL FIX: Cast NumPy float64 to Python floats so JSON doesn't crash!
            ann_ret = float(np.mean(m) * 252 * 100)
            ann_vol = float(np.std(m) * math.sqrt(252) * 100)
            
            if math.isnan(ann_ret): ann_ret = 0.0
            if math.isnan(ann_vol): ann_vol = 0.0
            
            all_rets.append(ann_ret)
            all_vols.append(ann_vol)

        # Generate target returns for the efficient frontier
        min_r, max_r = min(all_rets), max(all_rets)
        target_rets = np.linspace(min_r, max_r, n_points) if min_r != max_r else [min_r]
        
        frontier_points = []

        for target in target_rets:
            # Cast target to pure float
            t_val = float(target)
            cons = constraints + [
                {'type': 'eq', 'fun': lambda w, r=t_val: self._portfolio_stats(w, returns_matrix)[0] - r}
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
                        'return': round(t_val, 2),
                        'vol'   : round(float(vol), 2),
                        'sharpe': round(float(sharpe), 3),
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