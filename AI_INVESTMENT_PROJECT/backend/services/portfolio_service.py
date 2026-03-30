"""
Portfolio Simulation Engine
Computes combined portfolio metrics for a basket of stocks.
"""
import math, statistics

class PortfolioService:
    def __init__(self, metrics_svc, esg_svc):
        self._ms  = metrics_svc
        self._esg = esg_svc

    def simulate(self, tickers, weights=None):
        if not tickers:
            return {'error': 'No tickers provided'}

        # Equal weights if not specified
        if weights is None:
            weights = [1 / len(tickers)] * len(tickers)
        else:
            total = sum(weights)
            weights = [w / total for w in weights]

        metrics_list = []
        esg_list     = []
        for t in tickers:
            m = self._ms.get_metrics(t)
            e = self._esg.get_esg(t)
            if m:
                metrics_list.append(m)
                esg_list.append(e)

        if not metrics_list:
            return {'error': 'No valid metrics found'}

        # Weighted portfolio return
        port_return = sum(w * m.get('return_1y', 0)
                          for w, m in zip(weights, metrics_list))

        # Simplified portfolio volatility (ignores cross-correlations for demo)
        port_vol = math.sqrt(sum((w * m.get('volatility', 0) / 100)**2
                                 for w, m in zip(weights, metrics_list))) * 100

        # Weighted ESG score
        esg_scores = [e.get('total', 50) for e in esg_list]
        port_esg   = sum(w * s for w, s in zip(weights, esg_scores))

        # Sharpe
        rf = 5.0  # 5% annual
        port_sharpe = (port_return - rf) / port_vol if port_vol > 0 else 0

        # Benchmark comparison (S&P 500 proxy)
        sp500_return = 12.5
        sp500_vol    = 15.2

        composition = []
        for i, (t, w) in enumerate(zip(tickers, weights)):
            m = metrics_list[i] if i < len(metrics_list) else {}
            e = esg_list[i]     if i < len(esg_list)     else {}
            composition.append({
                'ticker'    : t,
                'weight'    : round(w * 100, 2),
                'return_1y' : m.get('return_1y', 0),
                'volatility': m.get('volatility', 0),
                'sharpe'    : m.get('sharpe', 0),
                'esg_total' : e.get('total', 0),
                'esg_rating': e.get('rating', 'N/A'),
            })

        return {
            'composition'      : composition,
            'portfolio_return' : round(port_return, 2),
            'portfolio_vol'    : round(port_vol, 2),
            'portfolio_esg'    : round(port_esg, 1),
            'portfolio_sharpe' : round(port_sharpe, 3),
            'vs_benchmark'     : {
                'return_alpha'  : round(port_return - sp500_return, 2),
                'vol_diff'      : round(port_vol    - sp500_vol, 2),
                'sp500_return'  : sp500_return,
                'sp500_vol'     : sp500_vol,
            },
            'diversification_score': round(100 * (1 - max(weights)), 1),
        }
