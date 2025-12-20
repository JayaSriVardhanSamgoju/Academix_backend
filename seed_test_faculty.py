import sys
import os

# Add current directory to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from db import SessionLocal, engine
import models
from auth_router import get_password_hash

# Ensure tables exist
models.Base.metadata.create_all(bind=engine)

def seed_test_faculty():
    db = SessionLocal()
    try:
        print("Seeding Test Faculty User...")
        
        email = "check.faculty@academix.com"
        password = "password123"
        
        # Check if user exists
        existing_user = db.query(models.User).filter(models.User.email == email).first()
        if existing_user:
            print(f"User {email} already exists. Updating password...")
            existing_user.hashed_password = get_password_hash(password)
            db.commit()
            print("Password updated.")
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
        
        # Create Faculty Profile (Teaching by default to test basic access, or Non-Teaching?)
        # User asked for "checking", often implies checking the recent feature (Non-Teaching) via sidebar differentiation
        # But for general checking, maybe Teaching is better?
        # Actually, let's create a NON_TEACHING one since that was the context.
        new_faculty = models.Faculty(
            user_id=new_user.id,
            faculty_type="NON_TEACHING", 
            department="Administration",
            designation="Quality Checker"
        )
        db.add(new_faculty)
        db.commit()
        
        print(f"Created Test Faculty: {new_user.name} ({email}) - NON_TEACHING")

    except Exception as e:
        print(f"Error seeding test faculty: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_test_faculty()
