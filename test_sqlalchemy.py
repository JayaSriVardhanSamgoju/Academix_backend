from sqlalchemy import create_engine, text
from config import SQLALCHEMY_DATABASE_URL

print(f"Connecting to: {SQLALCHEMY_DATABASE_URL}")

try:
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        print(f"Result: {result.scalar()}")
        print("SQLAlchemy connection successful!")
except Exception as e:
    print(f"SQLAlchemy failed: {e}")
