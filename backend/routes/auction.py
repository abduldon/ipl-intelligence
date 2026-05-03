from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional
from backend.analytics.auction_engine import get_player_valuation, analyze_squad, IPL_PURSE

router = APIRouter(prefix="/auction", tags=["Auction"])

class PlayerPurchase(BaseModel):
    player: str
    role: str
    price_paid: float
    impact_score: Optional[float] = 0
    max_bid_cr: Optional[float] = 0
    is_pacer: Optional[bool] = False
    is_spinner: Optional[bool] = False

class SquadAnalysisRequest(BaseModel):
    players: List[PlayerPurchase]

@router.get("/valuations")
def player_valuations(min_matches: int = 10, season: int = None):
    return get_player_valuation(min_matches, season)

@router.get("/purse")
def get_purse():
    return {"total_purse_cr": IPL_PURSE, "currency": "INR Crores"}

@router.post("/analyze-squad")
def analyze_squad_endpoint(request: SquadAnalysisRequest):
    players = [p.dict() for p in request.players]
    return analyze_squad(players)