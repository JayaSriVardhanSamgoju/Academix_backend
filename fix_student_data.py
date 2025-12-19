from db import SessionLocal
import models
from sqlalchemy import func

def fix_student_data(email):
    db = SessionLocal()
    try:
        user = db.query(models.User).filter(func.lower(models.User.email) == email.lower()).first()
        if not user:
            print(f"User {email} not found.")
            return

        student = db.query(models.Student).filter(models.Student.user_id == user.id).first()
        if not student:
            print(f"Student profile not found.")
            return

        print(f"--- Before Update ---")
        print(f"Year: {student.year}")
        print(f"Semester: {student.current_semester}")

        # Fix to Year 1, Sem 1 (M.Tech 1st Year)
        student.year = 1
        student.current_semester = 1
        
        db.commit()
        
        print(f"--- After Update ---")
        print(f"Year: {student.year}")
        print(f"Semester: {student.current_semester}")
        print("Successfully updated student record.")

    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_student_data("nagamohan765@gmail.com")
