from sqlalchemy.orm import Session
from db import SessionLocal
import models

def seed_enrollments():
    db = SessionLocal()
    try:
        print("--- SEEDING COURSE ENROLLMENTS ---")
        
        # 1. Clear existing enrollments to avoid duplicates
        db.query(models.CourseEnrollment).delete()
        db.commit()
        print("Existing enrollments cleared.")

        # 2. Fetch Students and Courses
        students = db.query(models.Student).all()
        courses = db.query(models.Course).all()
        
        if not students:
            print("No students found.")
            return
        if not courses:
            print("No courses found.")
            return

        total_enrollments = 0
        
        # 3. Match Logic
        for student in students:
            # Find courses matching student's Branch and Semester
            relevant_courses = [
                c for c in courses 
                if c.branch_id == student.branch_id and c.semester == student.current_semester
            ]
            
            if not relevant_courses:
                # Use roll_number to avoid potential joining issues if user not loaded immediately
                print(f"Warning: No courses found for Student {student.roll_number} (Branch: {student.branch_id}, Sem: {student.current_semester})")
                continue

            for course in relevant_courses:
                enrollment = models.CourseEnrollment(
                    student_id=student.id,
                    course_id=course.id
                )
                db.add(enrollment)
                total_enrollments += 1
        
        db.commit()
        print(f"--- SUCCESS: Created {total_enrollments} Enrollments ---")
        print("Logic: Students enrolled only in courses matching their Branch & Semester.")

    except Exception as e:
        print(f"Error seeding enrollments: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_enrollments()
