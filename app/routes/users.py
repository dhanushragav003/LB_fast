from fastapi import APIRouter , Depends , Request
from starlette.responses import JSONResponse
from app.helpers.users import validate_token , get_or_create , create_jwt
from app.dependency.database import get_db
from fastapi import Response
from app.core.config import app_config
from app.schemas.user import LoginRequest
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from app.services.db import db_session
import requests
route=APIRouter(
    prefix="/auth",
    tags=['auth']
)

@route.get("/me")
def me(request:Request,db=Depends(get_db)):
    token = request.cookies.get("session_token",None)
    if token is None:
        return JSONResponse({"error": "Token is Missing"}, status_code=400)
    user_details=validate_token(token,db)
   
    if not user_details.get("token_valid",False):
        return JSONResponse({"authenticated": False,"msg":user_details.get("msg","")}, status_code=401)
    return JSONResponse({
        "authenticated": True,
        "user":user_details['payload']
        },
        status_code=200
    )
       
@route.post("/signout")
def signout(response: Response):
    response.delete_cookie(
        key="session_token",
        path="/",           
        samesite="None",    
        secure=True        
    )
    return {"msg": "Signed out successfully","success":True}


@route.post("/user_login")
def user_login(request: LoginRequest,session=Depends(get_db)):
    token = request.id_token
    if token is None:
        return JSONResponse({"error":"Missing Token"},status_code=400)
    try:
        user_info=id_token.verify_oauth2_token(
            token,
            google_requests.Request(),
            app_config.GOOGLE_CLIENT_ID
        )
        email = user_info["email"]
        name = user_info.get("name", "")
        picture = user_info.get("picture", "")
    except Exception as e :
        return JSONResponse({"error":f"[ERROR] {e}"},status_code=400)
    db= db_session(session)
    user=get_or_create(db,email,name,picture,"google")
    jwt_token=create_jwt(user)
    response=JSONResponse(
        {
            "message": "Logged in successfully",
            "user":{
                "user_id": user.user_id,
                "email": user.email,
                "name":user.first_name,
                "profile_bg":  user.profile_bg,
                "is_logged":True
            }
        },status_code=200)
    response.set_cookie(
        "session_token",
        jwt_token,
        httponly=True,
        samesite="None",  
        secure=True,    
        max_age=7 * 24 * 60 * 60,
        path="/",
    )
    return response




