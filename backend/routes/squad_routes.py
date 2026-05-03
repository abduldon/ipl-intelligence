from fastapi import APIRouter, Depends
from backend.auth import get_current_user
from backend.analytics.squad_data import get_team_retention_data, TEAM_RETENTIONS
import pandas as pd
import os

router = APIRouter(prefix="/squad", tags=["Squad"])

AUCTION_CSV = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/raw/auction_market_2026.csv"))

@router.get("/my-team")
async def get_my_team_data(current_user: dict = Depends(get_current_user)):
    team = current_user.get("team")
    if not team:
        return {"error": "No team associated with this account"}
    return get_team_retention_data(team)

@router.get("/auction-pool")
async def get_auction_pool(current_user: dict = Depends(get_current_user)):
    try:
        df = pd.read_csv(AUCTION_CSV)
        df.columns = [c.strip() for c in df.columns]
        df = df.fillna("")
        return df.to_dict(orient="records")
    except Exception as e:
        return {"error": str(e)}

@router.get("/all-retentions")
async def get_all_retentions(current_user: dict = Depends(get_current_user)):
    result = []
    for team, data in TEAM_RETENTIONS.items():
        result.append({
            "team": team,
            "remaining_purse": data["remaining_purse"],
            "retention_cost": data["retention_cost"],
            "players_retained": len(data["retained_players"]),
            "retained_players": data["retained_players"]
        })
    return result