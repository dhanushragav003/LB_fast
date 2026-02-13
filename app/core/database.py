from sqlalchemy.orm import DeclarativeBase , sessionmaker
from sqlalchemy import create_engine
from app.core.config import app_config


engine = create_engine(app_config.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
class Base(DeclarativeBase):
    def to_dict(self):
        return {field.name: getattr(self, field.name) for field in self.__table__.columns}
def get_db():
   db = SessionLocal()
   try:
       yield db
   finally:
       db.close()
