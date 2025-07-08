from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

# Use Rails-style database naming conventions
# Default to development database if no DATABASE_URL is provided
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./team_composer_development.db")

# SQLite engine configuration
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()