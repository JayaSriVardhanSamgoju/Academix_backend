import sys
import os

# Add current directory to sys.path so 'import config' works in db.py
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from db import SessionLocal, engine, Base
import models
from auth_router import get_password_hash

# Ensure tables exist
models.Base.metadata.create_all(bind=engine)

def seed_seating_managers():
    db = SessionLocal()
    try:
        print("Seeding 5 Seating Manager Users...")
        
        # 5 distinct names for Seating Managers
        names = [
            "John Doe", "Jane Roe", "Alan Turing", "Grace Hopper", "Ada Lovelace"
        ]

        count = 0
        for full_name in names:
            first_name = full_name.split(" ")[0].lower()
            last_name = full_name.split(" ")[1].lower()
            email = f"{first_name}.{last_name}@academix.ai"
            
            # Check if user already exists
            existing_user = db.query(models.User).filter(models.User.email == email).first()
            if existing_user:
                print(f"User {email} already exists. Skipping.")
                continue

            # Create User
            new_user = models.User(
                email=email,
                hashed_password=get_password_hash("password123"),
                name=full_name,
                role="Seating Manager",
                is_active=True
            )
            db.add(new_user)
            db.commit()
            db.refresh(new_user)

       
            
            print(f"Created Seating Manager: {full_name} ({email})")
            count += 1

        print(f"Successfully seeded {count} new Seating Managers.")

    except Exception as e:
        print(f"Error seeding seating managers: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_seating_managers()
