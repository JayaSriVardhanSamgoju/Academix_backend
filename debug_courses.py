from sqlalchemy.orm import Session
from db import SessionLocal
import models
import schemas
from fastapi.encoders import jsonable_encoder

def debug_enrollments():
    db = SessionLocal()
    try:
        print("--- DEBUGGING STUDENT ENROLLMENTS ---")
        
        # Validate ALL courses
        courses = db.query(models.Course).all()
        print(f"Validating {len(courses)} courses...")
        
        for c in courses:
            try:
                mapped = {
                    "id": c.id,
                    "code": c.code,
                    "title": c.name,
                    "branch_id": c.branch_id,
                    "semester": c.semester,
                    "year_level": c.year_level or 1,
                    "credits": c.credits,
                    "is_active": c.is_active,
                    "enrolled_count": c.enrolled_count or 0,
                    "description": c.description,
                    "branch": None # Explicitly testing None for branch
                }
                # Try validation
                validated = schemas.CourseRead(**mapped)
                # print(f"  [OK] {c.code}") 
            except Exception as e:
                print(f"  [FAIL] Course {c.id} ({c.code}): {e}")
                
        print("Done validating all courses.")

    except Exception as e:
        print(f"Global Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    debug_enrollments()
