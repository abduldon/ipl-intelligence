import sqlite3
import os
import pandas as pd

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/ipl.db"))

def get_db():
    return sqlite3.connect(DB_PATH)

IPL_PURSE = 120  # crores (2025 auction standard)

ROLE_KEYWORDS = {
    "opener": ["RG Sharma", "V Kohli", "DA Warner", "KL Rahul", "RD Gaikwad", "Shubman Gill",
               "PP Shaw", "M Vijay", "G Gambhir", "V Sehwag", "AC Gilchrist", "ML Hayden"],
    "finisher": ["MS Dhoni", "KA Pollard", "HH Pandya", "RA Jadeja", "AT Rayudu", "DJ Bravo",
                 "N Pooran", "SV Samson", "KD Karthik", "AB de Villiers"],
    "pacer": ["JJ Bumrah", "B Kumar", "Mohammed Shami", "UT Yadav", "A Nehra", "Z Khan",
              "Sandeep Sharma", "T Natarajan", "Mohammed Siraj", "Arshdeep Singh"],
    "spinner": ["YS Chahal", "R Ashwin", "Harbhajan Singh", "SP Narine", "Imran Tahir",
                "K Gowtham", "Washington Sundar", "Kuldeep Yadav", "A Mishra"],
    "allrounder": ["HH Pandya", "RA Jadeja", "KH Pandya", "DJ Bravo", "KA Pollard",
                   "BCJ Cutting", "Washington Sundar", "Shahbaz Ahmed"],
}

SQUAD_REQUIREMENTS = {
    "openers": 2, "middle_order": 3, "finishers": 2,
    "pacers": 3, "spinners": 2, "allrounders": 2,
    "overseas_max": 4, "total_players": 25
}

def get_player_valuation(min_matches: int = 10, season: int = None):
    conn = get_db()
    season_filter = f"AND match_id IN (SELECT id FROM matches WHERE season = {season})" if season else ""

    bat_q = f"""
        SELECT batter as player,
            COUNT(DISTINCT match_id) as matches,
            SUM(batsman_runs) as runs,
            ROUND(SUM(batsman_runs)*100.0/NULLIF(COUNT(*),0),2) as strike_rate,
            ROUND(SUM(batsman_runs)*1.0/NULLIF(COUNT(DISTINCT match_id),0),2) as avg_per_match,
            SUM(CASE WHEN batsman_runs=6 THEN 1 ELSE 0 END) as sixes,
            SUM(CASE WHEN batsman_runs=4 THEN 1 ELSE 0 END) as fours
        FROM deliveries
        WHERE (extras_type != 'wides' OR extras_type IS NULL)
        {season_filter}
        GROUP BY batter
        HAVING matches >= {min_matches}
    """

    bowl_q = f"""
        SELECT bowler as player,
            COUNT(DISTINCT match_id) as matches_bowl,
            SUM(CASE WHEN player_dismissed IS NOT NULL AND player_dismissed != ''
                AND dismissal_kind NOT IN ('run out','retired hurt','obstructing the field')
                THEN 1 ELSE 0 END) as wickets,
            ROUND(SUM(total_runs)*6.0/NULLIF(
                COUNT(CASE WHEN extras_type NOT IN ('wides','noballs') OR extras_type IS NULL THEN 1 END),0),2) as economy
        FROM deliveries
        WHERE (extras_type NOT IN ('wides','noballs') OR extras_type IS NULL)
        {season_filter}
        GROUP BY bowler
        HAVING matches_bowl >= 5
    """

    bat_df = pd.read_sql_query(bat_q, conn).fillna(0)
    bowl_df = pd.read_sql_query(bowl_q, conn).fillna(0)
    conn.close()

    merged = pd.merge(bat_df, bowl_df, on="player", how="outer").fillna(0)

    results = []
    for _, row in merged.iterrows():
        runs = float(row.get("runs", 0))
        sr = float(row.get("strike_rate", 0))
        avg = float(row.get("avg_per_match", 0))
        wickets = float(row.get("wickets", 0))
        economy = float(row.get("economy", 12))
        matches = max(float(row.get("matches", 0)), float(row.get("matches_bowl", 0)))

        # Batting score (0-100)
        bat_score = min(100, (runs / 50) + (sr / 100) + (avg / 2))

        # Bowling score (0-100)
        eco_score = max(0, (12 - economy) * 3) if economy > 0 else 0
        bowl_score = min(100, (wickets * 1.5) + eco_score)

        # Impact score
        impact = round((bat_score * 0.6) + (bowl_score * 0.4), 2)

        # Valuation in crores
        base_val = 0.5  # minimum 50 lakh
        bat_val = (runs / 1000) * 3 + (sr / 200) * 2
        bowl_val = (wickets / 50) * 3 + eco_score / 20
        experience_bonus = min(2, matches / 50)
        total_val = round(base_val + bat_val + bowl_val + experience_bonus, 2)

        # Min and max bid
        min_bid = round(max(0.2, total_val * 0.6), 2)
        max_bid = round(total_val * 1.4, 2)

        # Determine role
        player = row["player"]
        role = "Batter"
        if wickets > 30 and runs < 500:
            role = "Bowler"
        elif wickets > 15 and runs > 500:
            role = "All-Rounder"
        elif runs > 200 and wickets > 5:
            role = "All-Rounder"

        results.append({
            "player": player,
            "matches": int(matches),
            "runs": int(runs),
            "strike_rate": sr,
            "avg_per_match": avg,
            "wickets": int(wickets),
            "economy": economy if economy > 0 else None,
            "bat_score": round(bat_score, 2),
            "bowl_score": round(bowl_score, 2),
            "impact_score": impact,
            "estimated_value_cr": total_val,
            "min_bid_cr": min_bid,
            "max_bid_cr": max_bid,
            "role": role
        })

    results.sort(key=lambda x: x["impact_score"], reverse=True)
    return results


def analyze_squad(players: list):
    """
    Given a list of purchased players with their roles and prices,
    return squad analysis: gaps, budget health, best XI, warnings
    """
    total_spent = sum(p.get("price_paid", 0) for p in players)
    remaining = IPL_PURSE - total_spent

    batters = [p for p in players if p.get("role") in ["Batter", "All-Rounder"]]
    bowlers = [p for p in players if p.get("role") in ["Bowler", "All-Rounder"]]
    pacers = [p for p in players if "Pacer" in p.get("role", "") or p.get("is_pacer", False)]
    spinners = [p for p in players if "Spinner" in p.get("role", "") or p.get("is_spinner", False)]

    warnings = []
    gaps = []

    # Budget warnings
    if remaining < 10:
        warnings.append("🚨 Critical: Less than ₹10 Cr remaining — very limited flexibility")
    elif remaining < 20:
        warnings.append("⚠️ Budget tight: Less than ₹20 Cr remaining")

    if len(players) > 0:
        avg_spend = total_spent / len(players)
        for p in players:
            if p.get("price_paid", 0) > p.get("max_bid_cr", 999) * 1.2:
                warnings.append(f"💸 Overpaid: {p['player']} bought at ₹{p['price_paid']}Cr (suggested max ₹{p.get('max_bid_cr','?')}Cr)")

    # Squad gap detection
    if len(batters) < 4:
        gaps.append(f"🏏 Need more batters (have {len(batters)}, need at least 4)")
    if len(bowlers) < 4:
        gaps.append(f"🎯 Need more bowlers (have {len(bowlers)}, need at least 4)")
    if len(players) < 11:
        gaps.append(f"👥 Need {11 - len(players)} more players for a full XI")

    # Best XI suggestion (top 11 by impact)
    sorted_players = sorted(players, key=lambda x: x.get("impact_score", 0), reverse=True)
    best_xi = sorted_players[:11]

    return {
        "total_players": len(players),
        "total_spent_cr": round(total_spent, 2),
        "remaining_purse_cr": round(remaining, 2),
        "purse_used_pct": round(total_spent / IPL_PURSE * 100, 1),
        "warnings": warnings,
        "squad_gaps": gaps,
        "best_xi": best_xi,
        "batters_count": len(batters),
        "bowlers_count": len(bowlers),
    }