"""
Investor & Stock Clustering Service
KMeans clustering of investors by behavioral traits and
stocks by financial/ESG characteristics.
"""
import math, random
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import numpy as np

random.seed(42)

RISK_MAP     = {'low': 0, 'moderate': 1, 'high': 2}
ESG_PRIO_MAP = {'low': 0, 'medium': 1, 'high': 2, 'very_high': 3}
DUR_MAP      = {'< 1 year': 0, '1-3 years': 1, '3-5 years': 2, '5+ years': 3}

CLUSTER_PERSONAS = {
    0: {'name': 'Sustainable Guardian',   'color': '#22c55e',
        'description': 'High ESG priority, low risk, long-term horizon. Values impact over returns.'},
    1: {'name': 'Balanced Growth Seeker', 'color': '#3b82f6',
        'description': 'Moderate risk tolerance, mixed sectors, balanced ESG consideration.'},
    2: {'name': 'Aggressive Alpha Hunter','color': '#ef4444',
        'description': 'High risk appetite, short horizon, performance-first mindset.'},
}


class ClusteringService:
    def cluster_investors(self, users):
        if len(users) < 3:
            return {'error': 'Need at least 3 users to cluster'}

        features = []
        valid_users = []
        for u in users:
            p = u.get('preferences', {})
            try:
                f = [
                    RISK_MAP.get(p.get('risk_tolerance', 'moderate'), 1),
                    ESG_PRIO_MAP.get(p.get('esg_priority', 'medium'), 1),
                    DUR_MAP.get(p.get('duration', '1-3 years'), 1),
                    p.get('budget', 10000) / 10000,
                    len(p.get('sectors', [])),
                ]
                features.append(f)
                valid_users.append(u)
            except Exception:
                pass

        if len(features) < 3:
            return {'clusters': [], 'personas': CLUSTER_PERSONAS}

        X = StandardScaler().fit_transform(features)
        k = min(3, len(features))
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = km.fit_predict(X)

        clustered = []
        cluster_counts = {i: 0 for i in range(k)}
        for u, label in zip(valid_users, labels):
            cluster_counts[int(label)] += 1
            clustered.append({
                'user_id'    : u['id'],
                'username'   : u['username'],
                'cluster'    : int(label),
                'persona'    : CLUSTER_PERSONAS.get(int(label), {}).get('name', f'Group {label}'),
            })

        return {
            'assignments'  : clustered,
            'cluster_sizes': cluster_counts,
            'personas'     : CLUSTER_PERSONAS,
            'n_clusters'   : k,
            'feature_names': ['risk_tolerance','esg_priority','duration','budget_scale','n_sectors'],
        }

    def cluster_stocks(self, metrics_svc, esg_svc):
        tickers = list(metrics_svc.get_all_metrics().keys())
        features, valid_tickers = [], []

        for t in tickers:
            m = metrics_svc.get_metrics(t)
            e = esg_svc.get_esg(t)
            if m and e:
                features.append([
                    m.get('return_1y', 0),
                    m.get('volatility', 0),
                    m.get('sharpe', 0),
                    e.get('total', 50),
                    e.get('env', 50),
                ])
                valid_tickers.append(t)

        if not features:
            return {'error': 'No features computed'}

        X = StandardScaler().fit_transform(features)
        k = 4
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = km.fit_predict(X)

        STOCK_CLUSTER_NAMES = {
            0: 'High-Growth / High-Risk',
            1: 'Sustainable Value',
            2: 'Stable Dividend Play',
            3: 'ESG Leaders',
        }

        result = []
        for t, label in zip(valid_tickers, labels):
            m = metrics_svc.get_metrics(t)
            e = esg_svc.get_esg(t)
            result.append({
                'ticker'    : t,
                'cluster'   : int(label),
                'cluster_name': STOCK_CLUSTER_NAMES.get(int(label), f'Group {label}'),
                'return_1y' : m.get('return_1y', 0),
                'volatility': m.get('volatility', 0),
                'esg_total' : e.get('total', 0),
                'sector'    : e.get('sector', 'Unknown'),
            })

        return {
            'stocks'        : result,
            'cluster_names' : STOCK_CLUSTER_NAMES,
            'n_clusters'    : k,
        }
