from db import SessionLocal
import models
from sqlalchemy import func

def check_student(email):
    db = SessionLocal()
    try:
        user = db.query(models.User).filter(func.lower(models.User.email) == email.lower()).first()
        if not user:
            print(f"User with email {email} not found.")
            return

        student = db.query(models.Student).filter(models.Student.user_id == user.id).first()
        if not student:
            print(f"Student profile for user {user.name} (ID: {user.id}) not found.")
            return

        print(f"--- Student Details for {email} ---")
        print(f"Name: {user.name}")
        print(f"Roll Number: {student.roll_number}")
        print(f"Current Semester: {student.current_semester}")
        print(f"Year: {student.year}")
        
        if student.branch:
            print(f"Branch: {student.branch.name} ({student.branch.code})")
            if student.branch.program:
                print(f"Program: {student.branch.program.name}")
            else:
                print("Program: None linked to Branch")
        else:
            print("Branch: None")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_student("nagamohan765@gmail.com")
