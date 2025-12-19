from sqlalchemy.orm import Session
from db import SessionLocal
import models

def find_literary_coordinator():
    db = SessionLocal()
    try:
        club = db.query(models.Club).filter(models.Club.name.like("%Literary%")).first()
        if club:
            coordinator = db.query(models.User).filter(models.User.id == club.coordinator_id).first()
            print(f"Club: {club.name}")
            print(f"Coordinator Name: {coordinator.name}")
            print(f"Coordinator Email: {coordinator.email}")
            print(f"Password: password123 (Default)")
        else:
            print("Literary Club not found.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    find_literary_coordinator()
