import sqlite3
import os
import pandas as pd

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/ipl.db"))

def get_db():
    return sqlite3.connect(DB_PATH)

TEAM_ALIASES = {
    "Delhi Daredevils": "Delhi Capitals",
    "Kings XI Punjab": "Punjab Kings",
    "Royal Challengers Bengaluru": "Royal Challengers Bangalore",
    "Deccan Chargers": "Sunrisers Hyderabad",
    "Pune Warriors": "Rising Pune Supergiant",
    "Rising Pune Supergiants": "Rising Pune Supergiant",
}

ACTIVE_TEAMS = [
    "Mumbai Indians",
    "Chennai Super Kings",
    "Royal Challengers Bangalore",
    "Kolkata Knight Riders",
    "Delhi Capitals",
    "Rajasthan Royals",
    "Sunrisers Hyderabad",
    "Punjab Kings",
    "Lucknow Super Giants",
    "Gujarat Titans",
]

TEAM_SHORT = {
    "Mumbai Indians": "MI",
    "Chennai Super Kings": "CSK",
    "Royal Challengers Bangalore": "RCB",
    "Kolkata Knight Riders": "KKR",
    "Delhi Capitals": "DC",
    "Rajasthan Royals": "RR",
    "Sunrisers Hyderabad": "SRH",
    "Punjab Kings": "PBKS",
    "Lucknow Super Giants": "LSG",
    "Gujarat Titans": "GT",
}

def get_all_teams():
    return ACTIVE_TEAMS

def get_team_squad(team: str, season: int = None):
    conn = get_db()
    aliases = [k for k, v in TEAM_ALIASES.items() if v == team] + [team]
    placeholders = ",".join("?" * len(aliases))
    season_filter = f"AND m.season = {season}" if season else ""

    bat_q = f"""
        SELECT d.batter as player,
            COUNT(DISTINCT d.match_id) as matches,
            SUM(d.batsman_runs) as runs,
            ROUND(SUM(d.batsman_runs)*100.0/NULLIF(COUNT(*),0),2) as strike_rate,
            ROUND(SUM(d.batsman_runs)*1.0/NULLIF(COUNT(DISTINCT d.match_id),0),2) as avg,
            SUM(CASE WHEN d.batsman_runs=6 THEN 1 ELSE 0 END) as sixes
        FROM deliveries d
        JOIN matches m ON d.match_id = m.id
        WHERE d.batting_team IN ({placeholders})
        {season_filter}
        AND (d.extras_type != 'wides' OR d.extras_type IS NULL)
        GROUP BY d.batter
        HAVING matches >= 3
        ORDER BY runs DESC
    """

    bowl_q = f"""
        SELECT d.bowler as player,
            COUNT(DISTINCT d.match_id) as matches,
            SUM(CASE WHEN d.player_dismissed IS NOT NULL AND d.player_dismissed != ''
                AND d.dismissal_kind NOT IN ('run out','retired hurt','obstructing the field')
                THEN 1 ELSE 0 END) as wickets,
            ROUND(SUM(d.total_runs)*6.0/NULLIF(
                COUNT(CASE WHEN d.extras_type NOT IN ('wides','noballs') OR d.extras_type IS NULL THEN 1 END),0),2) as economy,
            COUNT(CASE WHEN d.extras_type NOT IN ('wides','noballs') OR d.extras_type IS NULL THEN 1 END) as balls
        FROM deliveries d
        JOIN matches m ON d.match_id = m.id
        WHERE d.bowling_team IN ({placeholders})
        {season_filter}
        AND (d.extras_type NOT IN ('wides','noballs') OR d.extras_type IS NULL)
        GROUP BY d.bowler
        HAVING matches >= 3
        ORDER BY wickets DESC
    """

    batters = pd.read_sql_query(bat_q, conn, params=aliases).fillna(0)
    bowlers = pd.read_sql_query(bowl_q, conn, params=aliases).fillna(0)
    conn.close()
    return {
        "team": team,
        "season": season,
        "batters": batters.to_dict(orient="records"),
        "bowlers": bowlers.to_dict(orient="records")
    }

def get_team_performance(team: str, season: int = None):
    conn = get_db()
    aliases = [k for k, v in TEAM_ALIASES.items() if v == team] + [team]
    placeholders = ",".join("?" * len(aliases))
    season_filter = f"AND season = {season}" if season else ""

    query = f"""
        SELECT season,
            COUNT(*) as matches,
            SUM(CASE WHEN winner IN ({placeholders}) THEN 1 ELSE 0 END) as wins,
            SUM(CASE WHEN winner NOT IN ({placeholders}) AND winner IS NOT NULL THEN 1 ELSE 0 END) as losses,
            ROUND(SUM(CASE WHEN winner IN ({placeholders}) THEN 1 ELSE 0 END)*100.0/NULLIF(COUNT(*),0),1) as win_pct
        FROM matches
        WHERE (team1 IN ({placeholders}) OR team2 IN ({placeholders}))
        {season_filter}
        GROUP BY season ORDER BY season
    """

    params = aliases * 3 + aliases * 2
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    df = df.fillna(0)
    return df.to_dict(orient="records")

def get_team_vs_team(team1: str, team2: str):
    conn = get_db()
    aliases1 = [k for k, v in TEAM_ALIASES.items() if v == team1] + [team1]
    aliases2 = [k for k, v in TEAM_ALIASES.items() if v == team2] + [team2]
    p1 = ",".join("?" * len(aliases1))
    p2 = ",".join("?" * len(aliases2))

    query = f"""
        SELECT season, date, winner, win_by_runs, win_by_wickets, venue
        FROM matches
        WHERE (team1 IN ({p1}) AND team2 IN ({p2}))
           OR (team1 IN ({p2}) AND team2 IN ({p1}))
        ORDER BY date DESC LIMIT 20
    """

    params = aliases1 + aliases2 + aliases2 + aliases1
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    df = df.fillna(0)

    t1_wins = len(df[df["winner"].isin(aliases1)])
    t2_wins = len(df[df["winner"].isin(aliases2)])

    return {
        "team1": team1,
        "team2": team2,
        "total": len(df),
        "team1_wins": t1_wins,
        "team2_wins": t2_wins,
        "matches": df.to_dict(orient="records")
    }

def get_team_batting_summary(team: str, season: int = None):
    conn = get_db()
    aliases = [k for k, v in TEAM_ALIASES.items() if v == team] + [team]
    placeholders = ",".join("?" * len(aliases))
    season_filter = f"AND m.season = {season}" if season else ""

    query = f"""
        SELECT
            ROUND(AVG(match_runs),1) as avg_score,
            MAX(match_runs) as highest_score,
            MIN(match_runs) as lowest_score,
            COUNT(*) as innings
        FROM (
            SELECT d.match_id, d.inning, SUM(d.total_runs) as match_runs
            FROM deliveries d
            JOIN matches m ON d.match_id = m.id
            WHERE d.batting_team IN ({placeholders}) {season_filter}
            GROUP BY d.match_id, d.inning
        )
    """

    df = pd.read_sql_query(query, conn, params=aliases).fillna(0)
    conn.close()
    return df.to_dict(orient="records")[0]