from sqlalchemy.orm import Session
from db import SessionLocal
import models

def diagnose():
    db = SessionLocal()
    try:
        print("\n--- USERS ---")
        users = db.query(models.User).filter(models.User.email.contains("barbara")).all()
        for u in users:
            print(f"ID: {u.id} | Name: {u.name} | Email: {u.email} | Role: {u.role}")

        print("\n--- NOTIFICATIONS ---")
        notifications = db.query(models.Notification).all()
        for n in notifications:
            print(f"ID: {n.id} | UserID: {n.user_id} | Title: {n.title} | Type: {n.type}")

    finally:
        db.close()

if __name__ == "__main__":
    diagnose()
