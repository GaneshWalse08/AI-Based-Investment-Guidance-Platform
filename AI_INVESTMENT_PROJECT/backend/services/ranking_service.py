"""
Financial Scoring & Ranking Engine
Combines financial performance with ESG weighting to produce ranked lists.
Classification: Invest / Hold / Avoid
"""

class RankingService:
    def __init__(self, metrics_svc, esg_svc):
        self._ms  = metrics_svc
        self._esg = esg_svc

    def _normalize(self, values):
        """Min-max normalize a list of values to [0, 1]."""
        mn, mx = min(values), max(values)
        if mx == mn:
            return [0.5] * len(values)
        return [(v - mn) / (mx - mn) for v in values]

    def compute_rankings(self, esg_weight=0.4, sector='all'):
        all_metrics = self._ms.get_all_metrics()
        tickers = list(all_metrics.keys())

        if sector != 'all':
            esg_data = self._esg.get_esg
            tickers = [t for t in tickers
                       if self._esg.get_esg(t).get('sector') == sector]

        rows = []
        for t in tickers:
            m = all_metrics[t]
            e = self._esg.get_esg(t)
            if not m or not e:
                continue
            rows.append({
                'ticker'    : t,
                'return_1y' : m.get('return_1y', 0),
                'volatility': m.get('volatility', 0),
                'sharpe'    : m.get('sharpe', 0),
                'esg_total' : e.get('total', 50),
                'esg_rating': e.get('rating', 'N/A'),
                'sector'    : e.get('sector', 'Unknown'),
            })

        if not rows:
            return []

        # Normalize components
        ret_norm  = self._normalize([r['return_1y']  for r in rows])
        # Low volatility is better → invert
        vol_vals  = [r['volatility'] for r in rows]
        vol_norm  = [1 - v for v in self._normalize(vol_vals)]
        shrp_norm = self._normalize([r['sharpe']     for r in rows])
        esg_norm  = self._normalize([r['esg_total']  for r in rows])

        fin_weight = 1 - esg_weight
        results = []
        for i, row in enumerate(rows):
            fin_score  = (ret_norm[i] * 0.4 + vol_norm[i] * 0.3 + shrp_norm[i] * 0.3)
            total_score = fin_score * fin_weight + esg_norm[i] * esg_weight

            if total_score >= 0.65:
                classification = 'Invest'
            elif total_score >= 0.40:
                classification = 'Hold'
            else:
                classification = 'Avoid'

            results.append({
                **row,
                'fin_score'      : round(fin_score * 100, 1),
                'total_score'    : round(total_score * 100, 1),
                'classification' : classification,
                'explanation'    : self._explain(row, fin_score, esg_norm[i], classification),
            })

        results.sort(key=lambda x: x['total_score'], reverse=True)
        for i, r in enumerate(results):
            r['rank'] = i + 1

        return results

    def _explain(self, row, fin_score, esg_norm, cls):
        parts = []
        if row['return_1y'] > 15:
            parts.append(f"strong 1-year return of {row['return_1y']}%")
        elif row['return_1y'] < -5:
            parts.append(f"negative 1-year return of {row['return_1y']}%")

        if row['volatility'] < 20:
            parts.append("low volatility indicating stable price behaviour")
        elif row['volatility'] > 40:
            parts.append("high volatility suggesting elevated risk")

        if row['sharpe'] > 1.5:
            parts.append(f"excellent risk-adjusted return (Sharpe: {row['sharpe']})")
        elif row['sharpe'] < 0.5:
            parts.append(f"poor risk-adjusted return (Sharpe: {row['sharpe']})")

        if esg_norm > 0.7:
            parts.append(f"top-tier ESG profile (score: {row['esg_total']}, rating: {row['esg_rating']})")
        elif esg_norm < 0.3:
            parts.append(f"below-average ESG standing (score: {row['esg_total']}, rating: {row['esg_rating']})")

        summary = ', '.join(parts) if parts else "mixed financial and ESG signals"
        return f"Classified as '{cls}' based on {summary}."
