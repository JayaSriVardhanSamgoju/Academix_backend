import sys
import os

# Add current directory to sys.path so 'import config' works in db.py
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from db import SessionLocal, engine, Base
import models
from auth_router import get_password_hash

# Ensure tables exist (especially the new 'admins' table)   
models.Base.metadata.create_all(bind=engine)

def seed_admins():
    db = SessionLocal()
    try:
        print("Seeding 20 Admin Users...")
        
        real_names = [
            "James Smith", "Maria Garcia", "Robert Johnson", "Lisa Martinez", "Michael Brown",
            "Jennifer Davis", "William Miller", "Elizabeth Wilson", "David Moore", "Linda Taylor",
            "Richard Anderson", "Barbara Thomas", "Joseph Jackson", "Susan White", "Thomas Harris",
            "Margaret Martin", "Charles Thompson", "Jessica Garcia", "Christopher Martinez", "Sarah Robinson"
        ]

        branches = ["Computer Science", "Electrical Engineering", "Mechanical Engineering", "Civil Engineering", "Chemical Engineering", "Aerospace Engineering", "Biomedical Engineering", "Software Engineering", "Data Science", "Information Technology"]
        import random
        
        
        default_department = "" # This will be overwritten in the loop


        count = 0
        for full_name in real_names:
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
                role="Admin",
                is_active=True
            )
            db.add(new_user)
            db.commit()
            db.refresh(new_user)

            # Create Admin profile
            new_admin = models.Admin(
                user_id=new_user.id,
                department=random.choice(branches),
                phone_number=f"555-01{count:02d}" # Dummy phone
            )
            db.add(new_admin)
            db.commit()
            
            print(f"Created Admin: {full_name} ({email})")
            count += 1

        print(f"Successfully seeded {count} new admins.")

    except Exception as e:
        print(f"Error seeding admins: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_admins()
