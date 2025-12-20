import sys
import os

# Add current directory to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from db import SessionLocal
import models

def check_student_record():
    db = SessionLocal()
    search_name = "Naga Mohan"
    print(f"--- Searching for Student: '{search_name}' ---")
    
    try:
        # Search for user by name (partial match)
        users = db.query(models.User).filter(models.User.name.ilike(f"%{search_name}%")).all()
        
        if not users:
            print("No users found matching that name.")
            return

        print(f"Found {len(users)} matching user(s):")
        for user in users:
            print(f"\n[User ID: {user.id}]")
            print(f"  Name: {user.name}")
            print(f"  Email: {user.email}")
            print(f"  Role: {user.role}")
            print(f"  Active: {user.is_active}")
            
            if user.role == "Student":
                student_profile = db.query(models.Student).filter(models.Student.user_id == user.id).first()
                if student_profile:
                    print(f"  [Student Profile]:")
                    print(f"    Roll Number: {student_profile.roll_number}")
                    # print(f"    Program: {student_profile.program}") # Field does not exist in model
                    print(f"    Year: {student_profile.year}")
                    print(f"    Semester: {student_profile.current_semester}")
                else:
                    print(f"  [WARNING]: No Student profile found for this user!")
            else:
                print(f"  [Note]: User is not a Student (Role: {user.role})")
                
    except Exception as e:
        print(f"Error checking student: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_student_record()
