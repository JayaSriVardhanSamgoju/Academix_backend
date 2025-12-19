from db import SessionLocal
import models
from sqlalchemy import func

def check_student(email):
    db = SessionLocal()
    output = []
    try:
        user = db.query(models.User).filter(func.lower(models.User.email) == email.lower()).first()
        if not user:
            output.append(f"User with email {email} not found.")
        else:
            student = db.query(models.Student).filter(models.Student.user_id == user.id).first()
            if not student:
                output.append(f"Student profile for user {user.name} (ID: {user.id}) not found.")
            else:
                output.append(f"--- Student Details for {email} ---")
                output.append(f"Name: {user.name}")
                output.append(f"Roll Number: {student.roll_number}")
                output.append(f"Current Semester: {student.current_semester}")
                output.append(f"Year: {student.year}")
                
                if student.branch:
                    output.append(f"Branch: {student.branch.name} ({student.branch.code})")
                    if student.branch.program:
                        output.append(f"Program: {student.branch.program.name}")
                    else:
                        output.append("Program: None linked to Branch")
                else:
                    output.append("Branch: None")
    
    except Exception as e:
        output.append(f"Error: {e}")
    finally:
        db.close()
    
    with open("backend/student_details_out.txt", "w") as f:
        f.write("\n".join(output))

if __name__ == "__main__":
    check_student("nagamohan765@gmail.com")
