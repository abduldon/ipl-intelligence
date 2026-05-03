from fastapi import APIRouter
from backend.analytics.team_stats import (
    get_all_teams, get_team_squad, get_team_performance,
    get_team_vs_team, get_team_batting_summary
)

router = APIRouter(prefix="/teams", tags=["Teams"])

@router.get("/")
def all_teams():
    return get_all_teams()

@router.get("/{team}/squad")
def team_squad(team: str, season: int = None):
    return get_team_squad(team, season)

@router.get("/{team}/performance")
def team_performance(team: str, season: int = None):
    return get_team_performance(team, season)

@router.get("/{team}/batting-summary")
def team_batting_summary(team: str, season: int = None):
    return get_team_batting_summary(team, season)

@router.get("/h2h/{team1}/vs/{team2}")
def head_to_head(team1: str, team2: str):
    return get_team_vs_team(team1, team2)