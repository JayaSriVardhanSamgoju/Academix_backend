import sys
import os
import random

# Add current directory to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from db import SessionLocal, engine
import models

def seed_timetable():
    # Make sure tables exist
    models.Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        print("Seeding Timetable...")
        
        # 1. Get Faculty (Albus)
        faculty = db.query(models.Faculty).filter(models.Faculty.user_id == 242).first() # Albus ID from debug
        if not faculty:
            print("Faculty 'Albus' not found. Run seed_faculty.py first.")
            # fallback
            faculty = db.query(models.Faculty).first()
            if not faculty: return

        # 2. Get some courses
        courses = db.query(models.Course).all()
        if not courses:
            print("No courses found.")
            return

        # 3. Get a branch (or create dummy logic)
        branch = db.query(models.Branch).first()
        branch_id = branch.id if branch else None

        # 4. Clear existing entries for this faculty
        # Check if table has data first? No just delete
        try:
            db.query(models.TimeTableEntry).filter(models.TimeTableEntry.faculty_id == faculty.id).delete()
            db.commit()
        except Exception as e:
            print(f"Error clearing old entries (table might not exist yet?): {e}")

        # 5. Create Schedule
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        periods = [1, 2, 3, 4, 5, 6]
        
        times = {
            1: ("09:30", "10:30"),
            2: ("10:30", "11:30"),
            3: ("11:30", "12:30"),
            4: ("01:30", "02:30"),
            5: ("02:30", "03:30"),
            6: ("03:30", "04:30"),
        }

        count = 0
        for day in days:
            # Randomly assign 3-4 classes per day
            assigned_periods = sorted(random.sample(periods, k=random.randint(3, 5)))
            
            for p in assigned_periods:
                course = random.choice(courses)
                entry = models.TimeTableEntry(
                    day_of_week=day,
                    period_number=p,
                    start_time=times[p][0],
                    end_time=times[p][1],
                    faculty_id=faculty.id,
                    course_id=course.id,
                    branch_id=branch_id,
                    semester=course.semester,
                    academic_year=2024,
                    room=f"{random.choice(['A','B','C','LAB'])}-{random.randint(101, 505)}",
                    class_type=random.choice(["Lecture", "Lecture", "Lab"]) # Weight towards Lecture
                )
                db.add(entry)
                count += 1
        
        db.commit()
        print(f"Successfully seeded {count} timetable entries for Faculty ID {faculty.id}")

    except Exception as e:
        print(f"Error seeding timetable: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    seed_timetable()
