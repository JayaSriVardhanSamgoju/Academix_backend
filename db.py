from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base

from config import SQLALCHEMY_DATABASE_URL
from typing import Generator

# The 'pymysql' driver is commonly used fo  r MySQL with SQLAlchemy
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    pool_pre_ping=True
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all SQLAlchemy models
Base = declarative_base()

def get_db() -> Generator[Session, None, None]:
    """
    Dependency function to get a database session and ensure it is closed afterwards.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()