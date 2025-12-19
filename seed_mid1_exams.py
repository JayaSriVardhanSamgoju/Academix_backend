from sqlalchemy.orm import Session
from db import SessionLocal
import models
from datetime import datetime, timedelta
import random

def seed_mid1_exams():
    db = SessionLocal()
    try:
        print("--- RESETTING EXAMS ---")
        # 1. Clear existing exams and related data
        # Note: Order matters due to foreign keys if cascade isn't perfect, but usually clearing Exams is enough if child tables cascade.
        # Clearing Seat Allocations first to be safe
        db.query(models.SeatAllocation).delete()
        db.query(models.ExamStudent).delete()
        db.query(models.Exams).delete()
        db.commit()
        print("Existing exams cleared.")

        print("--- SEEDING MID 1 EXAMS ---")
        # 2. Fetch all courses
        courses = db.query(models.Course).all()
        if not courses:
            print("No courses found. Seed courses first.")
            return

        # 3. Group courses by (branch_id, semester)
        # Key: (branch_id, semester) -> Value: List[Course]
        grouped_courses = {}
        for course in courses:
            key = (course.branch_id, course.semester)
            if key not in grouped_courses:
                grouped_courses[key] = []
            grouped_courses[key].append(course)

        # 4. Schedule Exams
        # Start Date: Next Monday for realism
        start_date_base = datetime.now().replace(hour=10, minute=0, second=0, microsecond=0)
        # Find next Monday
        days_ahead = 0 - start_date_base.weekday() 
        if days_ahead <= 0: 
            days_ahead += 7
        start_date_base += timedelta(days=days_ahead)

        total_exams = 0

        for key, course_list in grouped_courses.items():
            branch_id, semester = key
            
            # For this specific group of students (same branch, same sem),
            # exams must be on consecutive days to avoid overlap.
            day_offset = 0
            
            for course in course_list:
                # Skip if Sunday (weekday 6)
                exam_date = start_date_base + timedelta(days=day_offset)
                if exam_date.weekday() == 6: # Sunday
                    day_offset += 1
                    exam_date = start_date_base + timedelta(days=day_offset)

                exam = models.Exams(
                    title=f"Mid 1: {course.name}",
                    exam_type="Mid 1",
                    course_id=course.id,
                    exam_date=exam_date,
                    start_time=exam_date,
                    duration_minutes=120, # 2 hours for Mid 1
                    status="Scheduled"
                )
                db.add(exam)
                total_exams += 1
                
                # Next course for this group gets the next day
                day_offset += 1
        
        db.commit()
        print(f"--- SUCCESS: Created {total_exams} Mid 1 Exams ---")
        print("Constraint Check: Students of same Branch & Semester have unique exam dates.")

    except Exception as e:
        print(f"Error seeding exams: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_mid1_exams()
