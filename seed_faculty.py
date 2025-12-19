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

def seed_faculty():
    db = SessionLocal()
    try:
        print("Seeding Faculty Users...")
        
        faculty_data = [
            {"name": "Prof. Albus Dumbledore", "email": "albus@hogwarts.edu", "type": "TEACHING", "dept": "CSE", "desig": "Professor"},
            {"name": "Prof. Severus Snape", "email": "severus@hogwarts.edu", "type": "TEACHING", "dept": "CSE", "desig": "Assistant Professor"},
            {"name": "Mr. Argus Filch", "email": "argus@hogwarts.edu", "type": "NON_TEACHING", "dept": "Admin", "desig": "Caretaker"},
            {"name": "Madam Pince", "email": "pince@hogwarts.edu", "type": "NON_TEACHING", "dept": "Library", "desig": "Librarian"}
        ]

        count = 0
        for data in faculty_data:
            # Check if user exists
            existing_user = db.query(models.User).filter(models.User.email == data["email"]).first()
            if existing_user:
                print(f"User {data['email']} already exists. Skipping.")
                continue

            # Create User
            new_user = models.User(
                email=data["email"],
                hashed_password=get_password_hash("password123"),
                name=data["name"],
                role="Faculty", # Generic role, specifics in Faculty table
                is_active=True
            )
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            
            # Create Faculty Profile
            new_faculty = models.Faculty(
                user_id=new_user.id,
                faculty_type=data["type"],
                department=data["dept"],
                designation=data["desig"]
            )
            db.add(new_faculty)
            db.commit()
            
            print(f"Created Faculty: {data['name']} ({data['type']})")
            count += 1

        print(f"Successfully seeded {count} faculty members.")

    except Exception as e:
        print(f"Error seeding faculty: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_faculty()
