from sqlalchemy.orm import Session
from db import SessionLocal
import models
import json
from datetime import datetime, timedelta

def create_test_exam():
    db = SessionLocal()
    try:
        print("--- STARTING EXAM CREATION TEST ---")
        
        # 1. Get a Course
        course = db.query(models.Course).first()
        if not course:
            print("Error: No courses found.")
            return

        # 2. Key Data
        exam_title = "Finals: Advanced AI Systems"
        exam_date = datetime.now() + timedelta(days=7)
        
        # 3. Create Exam
        new_exam = models.Exams(
            title=exam_title,
            exam_type="Semester End",
            course_id=course.id,
            exam_date=exam_date,
            start_time=exam_date, # simplified
            duration_minutes=180,
            status="Scheduled"
        )
        db.add(new_exam)
        db.commit()
        db.refresh(new_exam)
        print(f"Created Exam: {new_exam.title} (ID: {new_exam.id})")

        # 4. Notify Seating Managers (Simulating the Router Logic)
        seating_managers = db.query(models.User).filter(models.User.role == "Seating Manager").all()
        count = 0
        for sm in seating_managers:
            notif = models.Notification(
                user_id=sm.id,
                type="alert", 
                title="New Exam Scheduled",
                body=f"Exam '{new_exam.title}' for {course.name} has been scheduled.",
                notification_metadata=json.dumps({"exam_id": new_exam.id, "course_id": course.id}),
                is_read=False,
                created_at=datetime.utcnow()
            )
            db.add(notif)
            count += 1
        
        db.commit()
        print(f"Sent notifications to {count} Seating Managers.")
        print("--- SUCCESS ---")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_test_exam()
