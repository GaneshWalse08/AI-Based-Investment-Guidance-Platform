"""
Personalization Engine
Upgraded: Acts as a Robo-Advisor by analyzing Duration, Budget (in INR), Risk, Size, Sectors, and ESG.
Allows Fractional Shares and uses live-market risk thresholds.
"""

class PersonalizationService:
    def __init__(self, ranking_svc, data_svc):
        self._rs = ranking_svc
        self._ds = data_svc

    def get_personalized(self, prefs):
        duration   = prefs.get('duration', '1-3 years')
        budget_inr = float(prefs.get('budget', 100000)) # User inputs budget in Rupees
        risk       = prefs.get('risk_tolerance', 'moderate')
        cap_size   = prefs.get('cap_size', 'all')
        sectors    = prefs.get('sectors', [])
        esg_prio   = prefs.get('esg_priority', 'medium')

        esg_weight_map = {'very_high': 0.7, 'high': 0.5, 'medium': 0.3, 'low': 0.1}
        esg_weight     = esg_weight_map.get(esg_prio, 0.4)

        # UPDATED: Increased risk limits to account for live stock market volatility
        vol_base = {'low': 25, 'moderate': 40, 'high': 65}.get(risk, 40)
        if duration == '5+ years': vol_base += 10 
        elif duration == '< 1 year': vol_base -= 5  
        max_vol = vol_base

        all_ranked = self._rs.compute_rankings(esg_weight=esg_weight)
        
        # --- CURRENCY EXCHANGE (Approx 1 USD = 83.5 INR) ---
        USD_TO_INR = 83.50
        budget_usd = budget_inr / USD_TO_INR
        
        filtered = []
        for r in all_ranked:
            ticker = r['ticker']
            stock_detail = self._ds.get_stock(ticker)
            if not stock_detail: continue
                
            mcap = stock_detail.get('market_cap', 50) 
            price_usd = stock_detail.get('price', 100)
            
            # Convert the US stock price to Indian Rupees for the user
            price_inr = round(price_usd * USD_TO_INR, 2)

            # Apply Filters
            if cap_size == 'large' and mcap < 100: continue
            if cap_size == 'mid' and (mcap < 10 or mcap >= 100): continue
            if cap_size == 'small' and mcap >= 10: continue
            if r['volatility'] > max_vol: continue
            if sectors and len(sectors) > 0 and sectors[0] != '':
                if r['sector'] not in sectors: continue

            # Suggest allocating 10% of the total budget to this specific stock
            suggested_allocation_usd = budget_usd * 0.10
            
            # UPDATED: Allow Fractional Shares (rounded to 3 decimal places)
            suggested_shares = round(suggested_allocation_usd / price_usd, 3) if price_usd > 0 else 0

            # As long as they get SOME fraction of a share, we recommend it
            if suggested_shares <= 0: continue

            r['price_inr'] = price_inr
            r['market_cap'] = mcap
            r['suggested_shares'] = suggested_shares
            
            filtered.append(r)

        return {
            'recommendations'  : filtered[:10],
            'applied_filters'  : {
                'risk_tolerance'     : risk,
                'max_volatility'     : max_vol,
                'sectors'            : sectors,
                'esg_weight'         : esg_weight,
                'investment_duration': duration,
                'cap_size'           : cap_size,
                'budget_inr'         : budget_inr
            },
            'total_candidates' : len(all_ranked),
            'filtered_count'   : len(filtered),
        }