from app.core.database import Base
from sqlalchemy import Column, Integer, String
class User(Base):
    __tablename__ = "users"
    user_id = Column(Integer, primary_key=True, index=True,autoincrement=True)
    username = Column(String, unique=True, index=True, nullable=False)
    first_name = Column(String, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    auth_provider = Column(String(20), default="google")
    profile_bg = Column(String(500), nullable=True)

