from sqlalchemy.orm import Session
from db import SessionLocal
import models
from sqlalchemy import func

def fix_counts():
    db = SessionLocal()
    try:
        print("--- SYNCING ENROLLMENT COUNTS ---")
        courses = db.query(models.Course).all()
        
        for course in courses:
            real_count = db.query(models.CourseEnrollment).filter(models.CourseEnrollment.course_id == course.id).count()
            if course.enrolled_count != real_count:
                print(f"Updating {course.code}: {course.enrolled_count} -> {real_count}")
                course.enrolled_count = real_count
        
        db.commit()
        print("--- SUCCESS: All enrollment counts synced ---")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    fix_counts()
