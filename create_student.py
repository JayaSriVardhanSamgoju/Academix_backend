from db import SessionLocal
import models

db = SessionLocal()
user = db.query(models.User).filter(models.User.email == 'nagamohan765@gmail.com').first()

if user:
    # Check if student already exists
    existing_student = db.query(models.Student).filter(models.Student.user_id == user.id).first()
    if existing_student:
        print(f'Student already exists: {existing_student.roll_number}')
    else:
        student = models.Student(
            user_id=user.id,
            roll_number='21CS001',
            program='B.Tech CSE',
            year=3
        )
        db.add(student)
        db.commit()
        print(f'Student created with roll number: {student.roll_number}')
else:
    print('User not found')

db.close()
