
import jwt
from app.core.config import app_config
from app.models.User import User 
from fastapi import Request, HTTPException
from dataclasses import dataclass
from app.helpers.users import validate_token
@dataclass
class CurrentUser:
    id: str
    email: str
    role: str

def get_current_user(request: Request) -> CurrentUser:
    token = request.cookies.get("session_token")
    payload = validate_token(token).get('payload',None)
    if not payload:
        raise HTTPException(status_code=403, detail="Invalid token or unauthorised")
    print(f"{payload = }")
    return CurrentUser(
        id=payload["user_id"],
        email=payload.get("email"),
        role=payload.get("role", "user"),
    )

def get_optinal_current_user(request: Request):
    token = request.cookies.get("session_token")
    if not token:
        return None
    payload = validate_token(token).get('payload',None)
    if not payload:
        return None
    print(f"{payload = }")
    return CurrentUser(
        id=payload["user_id"],
        email=payload.get("email"),
        role=payload.get("role", "user"),
    )