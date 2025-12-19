import sys
import os

# Add current directory to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from db import SessionLocal
import models
import schemas
from fastapi.encoders import jsonable_encoder

def debug_faculty():
    db = SessionLocal()
    try:
        print("Debugging Faculty Data...")
        
        # 1. Check User
        email = "albus@hogwarts.edu"
        user = db.query(models.User).filter(models.User.email == email).first()
        if not user:
            print(f"User {email} NOT FOUND.")
            return
        
        print(f"User {email} Found. ID: {user.id}, Role: {user.role}")
        
        # 2. Check Faculty Profile
        faculty = db.query(models.Faculty).filter(models.Faculty.user_id == user.id).first()
        if not faculty:
            print(f"Faculty profile for {email} NOT FOUND.")
            return
            
        print(f"Faculty Profile Found. ID: {faculty.id}, Type: {faculty.faculty_type}")
        
        # 3. Test Serialization
        print("Testing Pydantic Serialization...")
        try:
            # Mock the schema
            schema_obj = schemas.FacultyRead.model_validate(faculty)
            print("Serialization SUCCESS:")
            print(schema_obj.model_dump_json(indent=2))
        except Exception as e:
            print(f"Serialization FAILED: {e}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    debug_faculty()
