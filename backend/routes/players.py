from fastapi import APIRouter
from backend.analytics.player_stats import (
    get_batting_stats, get_bowling_stats, get_impact_score,
    get_phase_stats, get_form_tracker, get_season_trend, get_bowling_phase_stats
)

router = APIRouter(prefix="/players", tags=["Players"])

@router.get("/batting")
def batting_stats(player: str = None, season: int = None):
    return get_batting_stats(player, season)

@router.get("/bowling")
def bowling_stats(player: str = None, season: int = None):
    return get_bowling_stats(player, season)

@router.get("/impact/{player_name}")
def impact_score(player_name: str):
    return get_impact_score(player_name)

@router.get("/phase/{player_name}")
def phase_stats(player_name: str):
    return get_phase_stats(player_name)

@router.get("/form/{player_name}")
def form_tracker(player_name: str, last_n: int = 10):
    return get_form_tracker(player_name, last_n)

@router.get("/season-trend/{player_name}")
def season_trend(player_name: str):
    return get_season_trend(player_name)

@router.get("/bowling-phase/{player_name}")
def bowling_phase(player_name: str):
    return get_bowling_phase_stats(player_name)

@router.get("/compare")
def compare_players(player1: str, player2: str):
    p1_impact = get_impact_score(player1)
    p2_impact = get_impact_score(player2)
    p1_phase = get_phase_stats(player1)
    p2_phase = get_phase_stats(player2)
    p1_seasons = get_season_trend(player1)
    p2_seasons = get_season_trend(player2)
    p1_bowl_phase = get_bowling_phase_stats(player1)
    p2_bowl_phase = get_bowling_phase_stats(player2)
    return {
        "player1": {
            "name": player1,
            "impact": p1_impact,
            "phases": p1_phase,
            "seasons": p1_seasons,
            "bowl_phases": p1_bowl_phase
        },
        "player2": {
            "name": player2,
            "impact": p2_impact,
            "phases": p2_phase,
            "seasons": p2_seasons,
            "bowl_phases": p2_bowl_phase
        }
    }