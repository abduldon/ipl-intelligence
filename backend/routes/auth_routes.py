from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from backend.auth import authenticate_user, create_access_token, get_current_user
from datetime import timedelta

router = APIRouter(prefix="/auth", tags=["Auth"])

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    token = create_access_token(
        data={"sub": user["username"]},
        expires_delta=timedelta(minutes=480)
    )
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "username": user["username"],
            "full_name": user["full_name"],
            "role": user["role"],
            "team": user["team"]
        }
    }

@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    return {
        "username": current_user["username"],
        "full_name": current_user["full_name"],
        "role": current_user["role"],
        "team": current_user["team"]
    }

@router.post("/logout")
async def logout():
    return {"message": "Logged out successfully"}