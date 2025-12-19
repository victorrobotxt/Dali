class RiskEngine:
    def calculate_risk_score(self, listing_data: dict, forensics_flags: list) -> dict:
        score = 0
        warnings = []
        
        area = listing_data.get('area', 0)
        listing_type = listing_data.get('type', '')  # e.g., "2-СТАЕН"
        price = listing_data.get('price', 0)
        
        # --- LOGIC FROM BATCH 2 (The "Space Hack") ---
        # If it claims to be a 2-bedroom but is under 55 sqm
        if "2-СТАЕН" in listing_type.upper() and area < 55:
            score += 20
            warnings.append({
                "code": "SUSPICIOUS_AREA", 
                "msg": f"Small area ({area} sqm) for a 2-bedroom. High risk of 'Space Hack' (Converted Studio)."
            })
            # If text confirms it, max out the risk
            if "CONVERSION_RISK" in forensics_flags:
                score += 30
                warnings.append({"code": "CONFIRMED_CONVERSION", "msg": "Seller explicitly admits property is a converted studio (Garsoniera)."});

        # --- LOGIC FROM BATCH 1 (The "Atelier") ---
        if "ATELIER_STATUS" in forensics_flags:
            score += 15
            warnings.append({"code": "LEGAL_STATUS_ATELIER", "msg": "Property is legally an Atelier. Cannot register address easily, higher taxes."})

        # --- LOGIC FROM BATCH 2 (The "Liquidity Trap") ---
        # Check for flags like "LONG_WAIT_COMPLETION_2028"
        future_flags = [f for f in forensics_flags if "LONG_WAIT" in f]
        if future_flags:
            score += 25
            for f in future_flags:
                year = f.split('_')[-1]
                warnings.append({"code": "LIQUIDITY_TRAP", "msg": f"Construction finishes in {year}. Capital locked for years."})

        # --- LOGIC FROM BATCH 1 (VAT Trap) ---
        if "VAT_EXCLUDED" in forensics_flags:
            # Not a 'risk' per se, but a financial shock
            real_price = price * 1.2
            warnings.append({"code": "HIDDEN_COST", "msg": f"Advertised price excludes VAT. Real price is ~{real_price:,.0f} EUR."})
            
        # --- Ground Floor Logic ---
        if "GROUND_FLOOR_RISK" in forensics_flags:
            score += 10
            warnings.append({"code": "GROUND_FLOOR", "msg": "Property is on the ground floor. Security and privacy risks."})

        verdict = "CLEAN"
        if score > 50:
            verdict = "CRITICAL"
        elif score > 20:
            verdict = "WARNING"

        return {
            "risk_score": min(score, 100),
            "verdict": verdict,
            "details": warnings
        }
