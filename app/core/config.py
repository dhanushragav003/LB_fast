from dotenv import load_dotenv
import os
from pydantic_settings import BaseSettings , SettingsConfigDict
from typing import List

load_dotenv()   # loads .env into os.environ

SECRET_KEY = os.getenv("SECRET_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL")
ENV = os.getenv("ENV")

class settings(BaseSettings):
    SECRET_KEY :str
    DATABASE_URL:str
    GOOGLE_CLIENT_ID :str
    YOUTUBE_API_KEY :str
    OLLAMA_API_KEY : str
    GEMINI_API_KEY :str
    GEMINI_MODEL :str
    ENV:str
    QSTASH_TOKEN:str
    QSTASH_CURRENT_SIGNING_KEY:str
    QSTASH_NEXT_SIGNING_KEY:str
    EMAIL_FROM:str
    SMTP_USER:str
    SMTP_PASSWORD:str
    SMTP_HOST:str
    SMTP_PORT:str
    RESEND_API_KEY:str
    ALLOWED_ORIGINS:List[str]= ["http://localhost:5173"]
    MAX_RETRY:int
    model_config=SettingsConfigDict(
        env_file='.env',
        extra="allow"
    )


app_config=settings()

