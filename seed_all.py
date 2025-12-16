
from sqlalchemy.orm import Session
from db import SessionLocal, engine
from models import (
    Base, Role, User, Student, Course, CourseEnrollment, Exams, ExamStudent,
    Room, RoomSeat, SeatAllocation, Club, ClubEvent, EventDocument, Notification,
    File, CourseImportJob, MindMap
)
from passlib.context import CryptContext
from datetime import datetime, timedelta
import random

# Database Setup
Base.metadata.create_all(bind=engine)
db = SessionLocal()

# Password Hashing
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
def get_password_hash(password):
    return pwd_context.hash(password)

def seed_data():
    print("WARNING: This will clear all existing data in the database!")
    
    # 1. Clear existing data (Reverse dependency order to avoid FK errors)
    try:
        db.query(MindMap).delete()
        db.query(CourseImportJob).delete()
        db.query(File).delete()
        db.query(Notification).delete()
        db.query(EventDocument).delete()
        db.query(ClubEvent).delete()
        db.query(Club).delete()
        db.query(SeatAllocation).delete()
        db.query(RoomSeat).delete()
        db.query(Room).delete()
        db.query(ExamStudent).delete()
        db.query(Exams).delete()
        db.query(CourseEnrollment).delete()
        db.query(Course).delete()
        db.query(Student).delete()
        db.query(User).delete()
        db.query(Role).delete()
        db.commit()
        print("Cleared existing data.")
    except Exception as e:
        db.rollback()
        print(f"Error clearing data: {e}")
        return

    # 2. Seed Roles
    roles = ["Admin", "Student", "Faculty", "Seating Manager", "Club Coordinator"]
    for r_name in roles:
        role = Role(name=r_name)
        db.add(role)
    db.commit()
    print("Seeded Roles.")

    # 3. Seed Users & Students
    # Admin
    admin_user = User(
        email="admin@academix.ai",
        hashed_password=get_password_hash("admin123"),
        name="Admin User",
        phone="1234567890",
        role="Admin",
        is_active=True
    )
    db.add(admin_user)
    
    # Seating Manager
    manager_user = User(
        email="manager@academix.ai",
        hashed_password=get_password_hash("manager123"),
        name="Seating Manager",
        phone="9876543210",
        role="Seating Manager",
        is_active=True
    )
    db.add(manager_user)

    # Club Coordinator
    coordinator_user = User(
        email="coordinator@academix.ai",
        hashed_password=get_password_hash("coordinator123"),
        name="Club Coordinator",
        phone="9876543211",
        role="Club Coordinator",
        is_active=True
    )
    db.add(coordinator_user)

    # Students
    student_users = []
    for i in range(1, 6):
        s_user = User(
            email=f"student{i}@academix.ai",
            hashed_password=get_password_hash("student123"),
            name=f"Student {i}",
            phone=f"555000000{i}",
            role="Student",
            is_active=True
        )
        db.add(s_user)
        student_users.append(s_user)
    
    db.commit()

    # Create Student profiles
    students = []
    for i, u in enumerate(student_users):
        stu = Student(
            user_id=u.id,
            roll_number=f"21CS00{i+1}",
            program="B.Tech CSE",
            year=3
        )
        db.add(stu)
        students.append(stu)
    
    db.commit()
    print("Seeded Users and Students.")

    # 4. Seed Courses
    courses = [
        Course(code="CS101", name="Intro to CS", title="Introduction to Computer Science", program_id=1, year_level=1, credits=4, description="Basics of programming"),
        Course(code="CS102", name="Data Structures", title="Data Structures and Algorithms", program_id=1, year_level=2, credits=4, description="Arrays, Lists, Trees, Graphs"),
        Course(code="MA101", name="Calculus I", title="Calculus for Engineers", program_id=1, year_level=1, credits=3, description="Limits, Derivatives, Integrals"),
        Course(code="PH101", name="Physics", title="Applied Physics", program_id=1, year_level=1, credits=3, description="Mechanics and Thermodynamics")
    ]
    for c in courses:
        db.add(c)
    db.commit()
    print("Seeded Courses.")

    # 5. Enroll Students
    # Enroll all students in first 2 courses
    

    # 6. Seed Rooms & Seats
    rooms = [
        Room(name="Hall A", building="Main Block", floor="1", capacity=30, layout="rows", accessibleSeats=2, status="active"),
        Room(name="Hall B", building="Main Block", floor="2", capacity=20, layout="rows", accessibleSeats=1, status="active")
    ]
    for r in rooms:
        db.add(r)
    db.commit()

    # Seats for Hall A (5 rows x 6 cols)
    hall_a = rooms[0]
    for row in range(1, 6):
        for col in range(1, 7):
            seat = RoomSeat(
                room_id=hall_a.id,
                seat_label=f"A{row}-{col}",
                row_number=row,
                col_number=col,
                is_accessible=(row==1 and col<=2)
            )
            db.add(seat)
    
    # Seats for Hall B (4 rows x 5 cols)
    hall_b = rooms[1]
    for row in range(1, 5):
        for col in range(1, 6):
            seat = RoomSeat(
                room_id=hall_b.id,
                seat_label=f"B{row}-{col}",
                row_number=row,
                col_number=col,
                is_accessible=(row==1 and col==1)
            )
            db.add(seat)
            
    db.commit()
    print("Seeded Rooms and Seats.")

    # 7. Seed Exams
    exam_date = datetime.now() + timedelta(days=7)
    exams = [
        Exams(
            course_id=courses[0].id, # CS101
            exam_type="MID",
            exam_date=exam_date,
            start_time=exam_date.replace(hour=10, minute=0, second=0),
            duration_minutes=90,
            status="upcoming",
            created_by=admin_user.id
        ),
        Exams(
            course_id=courses[1].id, # CS102
            exam_type="SEM",
            exam_date=exam_date + timedelta(days=2),
            start_time=exam_date.replace(hour=14, minute=0, second=0),
            duration_minutes=180,
            status="upcoming",
            created_by=admin_user.id
        )
    ]
    for e in exams:
        db.add(e)
    db.commit()
    print("Seeded Exams.")

    # 8. Seed Clubs & Events
    clubs = [
        Club(name="Coding Club", category="Technical", faculty_coordinator="Dr. Smith", faculty_contact="EXT123"),
        Club(name="Robotics Club", category="Technical", faculty_coordinator="Dr. Jones", faculty_contact="EXT456")
    ]
    for cl in clubs:
        db.add(cl)
    db.commit()

    event = ClubEvent(
        club_id=clubs[0].id,
        title="Hackathon 2025",
        description="Annual coding hackathon",
        status="approved",
        start_datetime=datetime.now() + timedelta(days=30),
        end_datetime=datetime.now() + timedelta(days=32),
        venues="Auditorium",
        attendees=100,
        created_by=admin_user.id
    )
    db.add(event)
    db.commit()
    print("Seeded Clubs and Events.")

    # 9. Seed Notifications
    notifs = [
        Notification(
            user_id=student_users[0].id,
            type="info",
            title="Welcome",
            body="Welcome to AcademixAI!",
            is_read=False
        ),
        Notification(
            user_id=student_users[0].id,
            type="alert",
            title="Exam Schedule",
            body="Mid exams are approaching.",
            is_read=True
        )
    ]
    for n in notifs:
        db.add(n)
    db.commit()
    print("Seeded Notifications.")

    db.close()
    print("Database seeding completed successfully!")

if __name__ == "__main__":
    seed_data()
