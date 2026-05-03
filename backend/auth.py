from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import hashlib

SECRET_KEY = "ipl-intelligence-secret-key-2025-abdul"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain: str, hashed: str) -> bool:
    return hashlib.sha256(plain.encode()).hexdigest() == hashed

USERS_DB = {
    "admin":   {"username":"admin",  "full_name":"IPL Admin",               "role":"admin",   "team":None,                          "hashed_password":hash_password("admin123")},
    "csk":     {"username":"csk",    "full_name":"Chennai Super Kings",      "role":"team",    "team":"Chennai Super Kings",         "hashed_password":hash_password("csk2025")},
    "mi":      {"username":"mi",     "full_name":"Mumbai Indians",           "role":"team",    "team":"Mumbai Indians",              "hashed_password":hash_password("mi2025")},
    "rcb":     {"username":"rcb",    "full_name":"Royal Challengers Bangalore","role":"team",  "team":"Royal Challengers Bangalore", "hashed_password":hash_password("rcb2025")},
    "kkr":     {"username":"kkr",    "full_name":"Kolkata Knight Riders",    "role":"team",    "team":"Kolkata Knight Riders",       "hashed_password":hash_password("kkr2025")},
    "dc":      {"username":"dc",     "full_name":"Delhi Capitals",           "role":"team",    "team":"Delhi Capitals",              "hashed_password":hash_password("dc2025")},
    "rr":      {"username":"rr",     "full_name":"Rajasthan Royals",         "role":"team",    "team":"Rajasthan Royals",            "hashed_password":hash_password("rr2025")},
    "srh":     {"username":"srh",    "full_name":"Sunrisers Hyderabad",      "role":"team",    "team":"Sunrisers Hyderabad",         "hashed_password":hash_password("srh2025")},
    "pbks":    {"username":"pbks",   "full_name":"Punjab Kings",             "role":"team",    "team":"Punjab Kings",                "hashed_password":hash_password("pbks2025")},
    "lsg":     {"username":"lsg",    "full_name":"Lucknow Super Giants",     "role":"team",    "team":"Lucknow Super Giants",        "hashed_password":hash_password("lsg2025")},
    "gt":      {"username":"gt",     "full_name":"Gujarat Titans",           "role":"team",    "team":"Gujarat Titans",              "hashed_password":hash_password("gt2025")},
    "analyst": {"username":"analyst","full_name":"IPL Analyst",              "role":"analyst", "team":None,                          "hashed_password":hash_password("analyst123")},
}

def get_user(username: str):
    return USERS_DB.get(username)

def authenticate_user(username: str, password: str):
    user = get_user(username.lower())
    if not user or not verify_password(password, user["hashed_password"]):
        return None
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            return None
        return get_user(username)
    except JWTError:
        return None

async def get_current_user(token: str = Depends(oauth2_scheme)):
    user = decode_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

async def require_admin(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user