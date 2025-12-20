import sys
import os

# Add current directory to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from db import SessionLocal, engine
import models
from auth_router import get_password_hash

# Ensure tables exist (helpful if remote DB is empty)
models.Base.metadata.create_all(bind=engine)

def seed_remote_faculty():
    db = SessionLocal()
    try:
        print("--- Seeding User to CURRENT Database (Remote) ---")
        
        email = "check.faculty@academix.com"
        password = "password123"
        
        # Check if user exists
        existing_user = db.query(models.User).filter(models.User.email == email).first()
        if existing_user:
            print(f"User {email} already exists in this database. Updating password...")
            existing_user.hashed_password = get_password_hash(password)
            db.commit()
            print("Password updated.")
            
            # Check/Update Faculty profile
            fac = db.query(models.Faculty).filter(models.Faculty.user_id == existing_user.id).first()
            if not fac:
                print("Adding missing Faculty profile...")
                new_faculty = models.Faculty(
                    user_id=existing_user.id,
                    faculty_type="NON_TEACHING", 
                    department="Administration",
                    designation="Quality Checker"
                )
                db.add(new_faculty)
                db.commit()
            else:
                print(f"Faculty profile exists: {fac.faculty_type}")
                
            return

        # Create User
        new_user = models.User(
            email=email,
            hashed_password=get_password_hash(password),
            name="Check Faculty",
            phone="9876543210",
            role="Faculty",
            is_active=True
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        # Create Faculty Profile
        new_faculty = models.Faculty(
            user_id=new_user.id,
            faculty_type="NON_TEACHING", 
            department="Administration",
            designation="Quality Checker"
        )
        db.add(new_faculty)
        db.commit()
        
        print(f"SUCCESS: Created Test Faculty {email} in the Remote Database.")

    except Exception as e:
        print(f"Error seeding remote faculty: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_remote_faculty()
