import sys
import os
from sqlalchemy import text

# Add current directory to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from db import SessionLocal, engine
import models

def check_database():
    print("--- Database Health Check ---")
    try:
        # 1. Test Connection
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            print("[OK] Connection Check: Database is reachable.")

        # 2. Test Session & ORM
        db = SessionLocal()
        try:
            user_count = db.query(models.User).count()
            print(f"[OK] User Table Check: Found {user_count} users.")
            
            faculty_count = db.query(models.Faculty).count()
            print(f"[OK] Faculty Table Check: Found {faculty_count} faculty members.")
            
            # List table names (if supported by the dialect easily, otherwise skip)
            print("[OK] Database appears fully functional.")
            
        except Exception as e:
            print(f"[ERROR] ORM/Query Check Failed: {e}")
        finally:
            db.close()

    except Exception as e:
        print(f"[ERROR] Connection Failed: {e}")
        print("Please check your database server status and credentials in .env")

if __name__ == "__main__":
    check_database()
