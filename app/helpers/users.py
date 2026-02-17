import jwt
from datetime import datetime, timedelta , timezone
from app.core.config import app_config
from fastapi import  HTTPException
from sqlalchemy.orm import Session
from app.models.User import User
from app.services.db import db_session
from app.models.User import User
def validate_token(token,db=None):
    try:
        payload=jwt.decode(
            token,
           app_config.SECRET_KEY,
            algorithms=["HS256"]
        )
        if db:
            user=db.query(User).filter(User.user_id == payload.get("user_id")).first()
            print(user)
            if user:
                payload.update({
                    "user_id": user.user_id,
                    "email": user.email,
                    "name": user.first_name,
                    "profile_bg": user.profile_bg,
                })
    except jwt.ExpiredSignatureError:
        return {"token_valid": False,"msg":"Token Expired"}
    except jwt.InvalidTokenError:
        return {"token_valid": False,"msg":"Invalid Token"}
    except Exception as e:
        return {"token_valid": False,"msg":str(e)}
    return {"token_valid":True,"payload":payload}

def create_jwt(user):
    now = datetime.now(timezone.utc)
    payload = {
        "user_id": user.user_id,
        "email": user.email,
        "exp":int((now + timedelta(minutes=2000)).timestamp()), # milliseconds
        "created_at": int(now.timestamp() * 1000)
    }
    token = jwt.encode(payload,app_config.SECRET_KEY, algorithm="HS256")
    return token


def get_or_create(db:db_session,email,name,picture,auth_provider,create=True):
    payload={
        "email":email,
        "username":email,
        "first_name": name,
        "profile_bg":picture,
        "auth_provider":auth_provider,
    }
    user = db.upsert_record(User,payload,conflict_columns=['username'],to_commit=True)
    return user