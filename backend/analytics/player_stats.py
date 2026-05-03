import sqlite3
import os
import pandas as pd

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/ipl.db"))

def get_db():
    return sqlite3.connect(DB_PATH)

def get_batting_stats(player_name: str = None, season: int = None):
    conn = get_db()
    where_clauses = ["(extras_type != 'wides' OR extras_type IS NULL)"]
    params = []
    if player_name:
        where_clauses.append("batter = ?")
        params.append(player_name)
    if season:
        where_clauses.append("match_id IN (SELECT id FROM matches WHERE season = ?)")
        params.append(season)
    where = " AND ".join(where_clauses)
    query = f"""
        SELECT batter,
            COUNT(DISTINCT match_id) as matches,
            SUM(batsman_runs) as runs,
            COUNT(*) as balls_faced,
            SUM(CASE WHEN batsman_runs = 4 THEN 1 ELSE 0 END) as fours,
            SUM(CASE WHEN batsman_runs = 6 THEN 1 ELSE 0 END) as sixes,
            ROUND(SUM(batsman_runs)*100.0/NULLIF(COUNT(*),0),2) as strike_rate,
            ROUND(SUM(batsman_runs)*1.0/NULLIF(COUNT(DISTINCT match_id),0),2) as avg_per_match
        FROM deliveries WHERE {where}
        GROUP BY batter ORDER BY runs DESC
    """
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    df = df.fillna(0)
    return df.to_dict(orient="records")

def get_bowling_stats(player_name: str = None, season: int = None):
    conn = get_db()
    where_clauses = ["1=1"]
    params = []
    if player_name:
        where_clauses.append("bowler = ?")
        params.append(player_name)
    if season:
        where_clauses.append("match_id IN (SELECT id FROM matches WHERE season = ?)")
        params.append(season)
    where = " AND ".join(where_clauses)
    query = f"""
        SELECT bowler,
            COUNT(DISTINCT match_id) as matches,
            COUNT(CASE WHEN extras_type NOT IN ('wides','noballs') OR extras_type IS NULL THEN 1 END) as balls_bowled,
            SUM(total_runs) as runs_conceded,
            SUM(CASE WHEN player_dismissed IS NOT NULL AND player_dismissed != ''
                AND dismissal_kind NOT IN ('run out','retired hurt','obstructing the field')
                THEN 1 ELSE 0 END) as wickets,
            ROUND(SUM(total_runs)*6.0/NULLIF(
                COUNT(CASE WHEN extras_type NOT IN ('wides','noballs') OR extras_type IS NULL THEN 1 END),0),2) as economy,
            ROUND(COUNT(CASE WHEN extras_type NOT IN ('wides','noballs') OR extras_type IS NULL THEN 1 END)*1.0/NULLIF(
                SUM(CASE WHEN player_dismissed IS NOT NULL AND player_dismissed != ''
                AND dismissal_kind NOT IN ('run out','retired hurt','obstructing the field')
                THEN 1 ELSE 0 END),0),2) as strike_rate
        FROM deliveries WHERE {where}
        GROUP BY bowler HAVING balls_bowled > 0 ORDER BY wickets DESC
    """
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    df = df.fillna(0)
    return df.to_dict(orient="records")

def get_impact_score(player_name: str):
    conn = get_db()
    bat_q = """
        SELECT COALESCE(SUM(batsman_runs),0) as runs,
            COALESCE(ROUND(SUM(batsman_runs)*100.0/NULLIF(COUNT(*),0),2),0) as sr,
            COUNT(DISTINCT match_id) as matches
        FROM deliveries WHERE batter = ?
        AND (extras_type != 'wides' OR extras_type IS NULL)
    """
    bowl_q = """
        SELECT COALESCE(SUM(CASE WHEN player_dismissed IS NOT NULL AND player_dismissed != ''
                AND dismissal_kind NOT IN ('run out','retired hurt','obstructing the field')
                THEN 1 ELSE 0 END),0) as wickets,
            COALESCE(ROUND(SUM(total_runs)*6.0/NULLIF(COUNT(*),0),2),12) as economy,
            COUNT(DISTINCT match_id) as matches
        FROM deliveries WHERE bowler = ?
        AND (extras_type NOT IN ('wides','noballs') OR extras_type IS NULL)
    """
    bat = pd.read_sql_query(bat_q, conn, params=[player_name]).iloc[0]
    bowl = pd.read_sql_query(bowl_q, conn, params=[player_name]).iloc[0]
    conn.close()
    runs = float(bat["runs"]) if bat["runs"] else 0.0
    sr = float(bat["sr"]) if bat["sr"] else 0.0
    wickets = float(bowl["wickets"]) if bowl["wickets"] else 0.0
    economy = float(bowl["economy"]) if bowl["economy"] else 12.0
    bat_score = (runs / 50) + (sr / 100)
    bowl_score = (wickets * 2) + max(0, (12 - economy))
    impact = round((bat_score * 0.6) + (bowl_score * 0.4), 2)
    return {
        "player": player_name, "impact_score": impact,
        "batting_score": round(bat_score, 2), "bowling_score": round(bowl_score, 2),
        "runs": int(runs), "strike_rate": sr, "wickets": int(wickets), "economy": economy
    }

def get_phase_stats(player_name: str):
    """Powerplay (ov 1-6), Middle (7-15), Death (16-20) batting breakdown"""
    conn = get_db()
    query = """
        SELECT
            CASE WHEN over < 6 THEN 'Powerplay'
                 WHEN over < 15 THEN 'Middle'
                 ELSE 'Death' END as phase,
            SUM(batsman_runs) as runs,
            COUNT(*) as balls,
            ROUND(SUM(batsman_runs)*100.0/NULLIF(COUNT(*),0),2) as strike_rate,
            SUM(CASE WHEN batsman_runs=4 THEN 1 ELSE 0 END) as fours,
            SUM(CASE WHEN batsman_runs=6 THEN 1 ELSE 0 END) as sixes
        FROM deliveries
        WHERE batter = ?
        AND (extras_type != 'wides' OR extras_type IS NULL)
        GROUP BY phase
    """
    df = pd.read_sql_query(query, conn, params=[player_name])
    conn.close()
    df = df.fillna(0)
    return df.to_dict(orient="records")

def get_form_tracker(player_name: str, last_n: int = 10):
    """Last N matches batting performance"""
    conn = get_db()
    query = """
        SELECT d.match_id,
            m.season,
            m.date,
            m.team1,
            m.team2,
            SUM(d.batsman_runs) as runs,
            COUNT(*) as balls,
            ROUND(SUM(d.batsman_runs)*100.0/NULLIF(COUNT(*),0),2) as strike_rate
        FROM deliveries d
        JOIN matches m ON d.match_id = m.id
        WHERE d.batter = ?
        AND (d.extras_type != 'wides' OR d.extras_type IS NULL)
        GROUP BY d.match_id
        ORDER BY m.date DESC
        LIMIT ?
    """
    df = pd.read_sql_query(query, conn, params=[player_name, last_n])
    conn.close()
    df = df.fillna(0)
    # reverse so chart shows oldest to newest
    df = df.iloc[::-1].reset_index(drop=True)
    return df.to_dict(orient="records")

def get_season_trend(player_name: str):
    """Season by season batting stats"""
    conn = get_db()
    query = """
        SELECT m.season,
            COUNT(DISTINCT d.match_id) as matches,
            SUM(d.batsman_runs) as runs,
            ROUND(SUM(d.batsman_runs)*100.0/NULLIF(COUNT(*),0),2) as strike_rate,
            ROUND(SUM(d.batsman_runs)*1.0/NULLIF(COUNT(DISTINCT d.match_id),0),2) as avg
        FROM deliveries d
        JOIN matches m ON d.match_id = m.id
        WHERE d.batter = ?
        AND (d.extras_type != 'wides' OR d.extras_type IS NULL)
        GROUP BY m.season
        ORDER BY m.season ASC
    """
    df = pd.read_sql_query(query, conn, params=[player_name])
    conn.close()
    df = df.fillna(0)
    return df.to_dict(orient="records")

def get_bowling_phase_stats(player_name: str):
    """Phase-wise bowling economy"""
    conn = get_db()
    query = """
        SELECT
            CASE WHEN over < 6 THEN 'Powerplay'
                 WHEN over < 15 THEN 'Middle'
                 ELSE 'Death' END as phase,
            COUNT(CASE WHEN extras_type NOT IN ('wides','noballs') OR extras_type IS NULL THEN 1 END) as balls,
            SUM(total_runs) as runs,
            ROUND(SUM(total_runs)*6.0/NULLIF(
                COUNT(CASE WHEN extras_type NOT IN ('wides','noballs') OR extras_type IS NULL THEN 1 END),0),2) as economy,
            SUM(CASE WHEN player_dismissed IS NOT NULL AND player_dismissed != ''
                AND dismissal_kind NOT IN ('run out','retired hurt','obstructing the field')
                THEN 1 ELSE 0 END) as wickets
        FROM deliveries
        WHERE bowler = ?
        GROUP BY phase
    """
    df = pd.read_sql_query(query, conn, params=[player_name])
    conn.close()
    df = df.fillna(0)
    return df.to_dict(orient="records")