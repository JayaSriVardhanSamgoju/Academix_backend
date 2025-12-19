from sqlalchemy.orm import Session
from db import SessionLocal
import models
from utils.seating_algorithm import allocate_seating, generate_adjacency_matrix
import json

def debug_alloc():
    db = SessionLocal()
    try:
        print("--- DEBUGGING SEAT ALLOCATION ---")
        
        # 1. Check Exams and Student Counts
        exams = db.query(models.Exams).all()
        print(f"Found {len(exams)} exams.")
        
        target_exam = None
        for exam in exams:
            count = db.query(models.ExamStudent).filter(models.ExamStudent.exam_id == exam.id).count()
            print(f"Exam ID {exam.id}: {exam.title} (Course: {exam.course_id}) -> {count} Students")
            if count > 0:
                target_exam = exam
        
        if not target_exam:
            print("ERROR: No exams have students registered!")
            return

        print(f"\n--- TESTING ALLOCATION FOR EXAM {target_exam.id} ---")
        
        # 2. Mock Data for Allocation
        students = db.query(models.ExamStudent).filter(models.ExamStudent.exam_id == target_exam.id).limit(10).all()
        student_data = {
            str(s.student.id): {
                "id": str(s.student.id),
                "roll": s.student.roll_number,
                "subject": "DEBUG_SUB",
                "section": "A"
            } for s in students
        }
        
        # Fetch a room
        room = db.query(models.Room).first()
        if not room:
            print("ERROR: No rooms found!")
            return
            
        seats = db.query(models.RoomSeat).filter(models.RoomSeat.room_id == room.id).limit(20).all()
        room_data = {
            "room_id": str(room.id),
            "seats": [str(s.id) for s in seats],
            "adjacency_matrix": generate_adjacency_matrix(seats)
        }
        
        print(f"Testing with {len(student_data)} students and Room {room.name} ({len(seats)} seats)")
        
        # 3. Call Algorithm
        try:
            result = allocate_seating(room_data, student_data, str(target_exam.id), "MID")
            print("Algorithm Result:", min(200, len(str(result))), "chars...")
            print(json.dumps(result, indent=2))
        except Exception as e:
            print(f"CRASH IN ALGORITHM: {e}")
            import traceback
            traceback.print_exc()

    except Exception as e:
        print(f"Global Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    debug_alloc()
