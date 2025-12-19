from sqlalchemy import create_engine, text
from config import SQLALCHEMY_DATABASE_URL

engine = create_engine(SQLALCHEMY_DATABASE_URL)

with engine.connect() as conn:
    # Add phone column to users table
    try:
        conn.execute(text("ALTER TABLE users ADD COLUMN phone VARCHAR(15)"))
        conn.commit()
        print("Successfully added phone column to users table")
    except Exception as e:
        print(f"Error: {e}")
        print("Phone column might already exist")
