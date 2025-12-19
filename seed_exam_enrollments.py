from sqlalchemy.orm import Session
from db import SessionLocal
import models

def seed_exam_enrollments():
    db = SessionLocal()
    try:
        print("--- SYNCING EXAM ENROLLMENTS ---")
        
        # 1. Clear existing exam enrollments (optional, but safe for re-running)
        db.query(models.ExamStudent).delete()
        db.commit()
        print("Cleared old exam enrollments.")

        # 2. Get all Course Enrollments
        course_enrollments = db.query(models.CourseEnrollment).all()
        
        count = 0
        for ce in course_enrollments:
            # Find exams for this course
            exams = db.query(models.Exams).filter(models.Exams.course_id == ce.course_id).all()
            for exam in exams:
                # Enroll student in exam
                exam_student = models.ExamStudent(
                    exam_id=exam.id,
                    student_id=ce.student_id
                )
                db.add(exam_student)
                count += 1
        
        db.commit()
        print(f"--- SUCCESS: Created {count} Exam Enrollments ---")
        print("Logic: Students enrolled in Course X are now enrolled in all Exams for Course X.")

    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_exam_enrollments()
