import models, schemas
import auth_router
import requests
import config
from fastapi import APIRouter, Depends, HTTPException, status, Body, BackgroundTasks
from sqlalchemy.orm import Session, joinedload
from typing import List, Annotated
from datetime import datetime
from db import SessionLocal

router = APIRouter(prefix="/exams", tags=["exams"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# POST /exams - Create a new exam
@router.post("/", status_code=201)
def create_exam(
    exam_in: schemas.ExamCreate,
    db: Session = Depends(get_db)
):
    # Parse date and time
    try:
        exam_date_dt = datetime.strptime(exam_in.exam_date, "%Y-%m-%d")
        start_time_dt = datetime.strptime(exam_in.start_time, "%H:%M")
        # Combine date and time for exam_date and start_time
        exam_date_full = datetime.combine(exam_date_dt.date(), start_time_dt.time())
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid date/time format: {e}")

    exam = models.Exams(
        title=exam_in.title,
        exam_type=exam_in.exam_type,
        course_id=exam_in.course_id,
        exam_date=exam_date_full,
        start_time=exam_date_full,
        duration_minutes=exam_in.duration_minutes,
        status=exam_in.status,
        faculty_id=exam_in.faculty_id
    )
    db.add(exam)
    db.commit()
    db.refresh(exam)

    # --- NOTIFY SEATING MANAGERS ---
    # Notify ALL Seating Managers about the new exam
    import json
    seating_managers = db.query(models.User).filter(models.User.role == "Seating Manager").all()
    for sm in seating_managers:
        notif = models.Notification(
            user_id=sm.id,
            type="alert", # Using 'alert' to make it prominent for the Seating Manager
            title="New Exam Scheduled",
            body=f"Exam '{exam.title}' for course ID {exam.course_id} has been scheduled for {exam.exam_date}.",
            notification_metadata=json.dumps({"exam_id": exam.id, "course_id": exam.course_id}),
            is_read=False
        )
        db.add(notif)
    db.commit()
    # -------------------------------

    db.commit()
    # -------------------------------

    # --- AUTO-ENROLL STUDENTS ---
    # Fetch all students currently enrolled in the course and add them to this exam
    enrolled_students = db.query(models.CourseEnrollment).filter(
        models.CourseEnrollment.course_id == exam_in.course_id,
        models.CourseEnrollment.enrollment_status == "active"
    ).all()

    for enrollment in enrolled_students:
        exam_student = models.ExamStudent(
            exam_id=exam.id,
            student_id=enrollment.student_id
        )
        db.add(exam_student)
    db.commit()
    # ----------------------------

    return {"id": exam.id, "message": "Exam created successfully"}



# GET /exams - List all exams (for admin or demo)
@router.get("/", response_model=List[schemas.ExamRead])
def get_exams(db: Session = Depends(get_db)):
    exams = db.query(models.Exams)\
        .options(joinedload(models.Exams.course), 
                 joinedload(models.Exams.faculty).joinedload(models.Faculty.user))\
        .all()
    result = []
    for exam in exams:
        # Map to frontend fields
        result.append(schemas.ExamRead(
            id=exam.id,
            title=exam.title or exam.exam_type,
            courseCode=exam.course.code if exam.course else "",
            date=exam.exam_date,
            start_time=exam.start_time,
            duration=exam.duration_minutes,
            enrolled=db.query(models.ExamStudent).filter_by(exam_id=exam.id).count(),
            seatsAssigned=db.query(models.SeatAllocation).filter_by(exam_id=exam.id).count() > 0,
            status=exam.status,
            faculty_id=exam.faculty_id,
            faculty=exam.faculty
        ))
    return result



@router.get("/course/{course_id}", response_model=List[schemas.ExamRead])
def get_course_exams(course_id: int, db: Session = Depends(get_db)):
    exams = db.query(models.Exams)\
        .options(joinedload(models.Exams.course), 
                 joinedload(models.Exams.faculty).joinedload(models.Faculty.user))\
        .filter(models.Exams.course_id == course_id)\
        .all()
    result = []
    for exam in exams:
        result.append(schemas.ExamRead(
            id=exam.id,
            title=exam.title or exam.exam_type,
            courseCode=exam.course.code if exam.course else "",
            date=exam.exam_date,
            start_time=exam.start_time,
            duration=exam.duration_minutes,
            enrolled=db.query(models.ExamStudent).filter_by(exam_id=exam.id).count(),
            seatsAssigned=db.query(models.SeatAllocation).filter_by(exam_id=exam.id).count() > 0,
            status=exam.status,
            faculty_id=exam.faculty_id,
            faculty=exam.faculty
        ))
    return result

@router.get("/{exam_id}/students", response_model=List[schemas.StudentRead])
def get_exam_students(exam_id: int, db: Session = Depends(get_db)):
    exam_students = db.query(models.ExamStudent).filter(models.ExamStudent.exam_id == exam_id).all()
    return [es.student for es in exam_students]

@router.post("/{exam_id}/release-hall-tickets")
def release_hall_tickets(
    exam_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_router.get_current_active_user) # Assuming admin check later
):
    exam = db.query(models.Exams).filter(models.Exams.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    
    # Check if allocations exist
    alloc_count = db.query(models.SeatAllocation).filter(models.SeatAllocation.exam_id == exam_id).count()
    if alloc_count == 0:
        raise HTTPException(status_code=400, detail="Cannot release hall tickets. No seats allocated yet.")

    exam.status = "HALL_TICKETS_RELEASED"
    db.commit()
    return {"message": "Hall tickets released successfully", "count": alloc_count}

@router.post("/{exam_id}/release-results")
def release_results(
    exam_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_router.get_current_active_user)
):
    """Marks an exam as results released and notifies students."""
    exam = db.query(models.Exams).filter(models.Exams.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    
    exam.status = "RESULTS_RELEASED"
    db.commit()

    # Trigger Notifications
    def notify_results(exam_obj):
        try:
            # Fetch all students in this exam
            students = db.query(models.User).join(models.Student).join(models.ExamStudent).filter(
                models.ExamStudent.exam_id == exam_obj.id
            ).all()
            
            student_list = [{"email": s.email, "id": str(s.id)} for s in students if s.email]
            
            if student_list:
                payload = {
                    "exam_name": exam_obj.title or exam_obj.exam_type,
                    "student_list": student_list
                }
                requests.post(f"{config.MAIL_SERVICE_URL}/api/v1/notify/results-release", json=payload, timeout=10)
        except Exception as e:
            print(f"Results release notification error: {e}")

    background_tasks.add_task(notify_results, exam)
    return {"message": "Results released successfully"}

@router.get("/student/me")
def get_student_upcoming_exams(
    current_user: models.User = Depends(auth_router.get_current_active_user),
    db: Session = Depends(get_db)
):
    # Find student profile
    student = db.query(models.Student).filter(models.Student.user_id == current_user.id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")

    enrolled_courses = db.query(models.CourseEnrollment.course_id).filter(models.CourseEnrollment.student_id == student.id).all()
    course_ids = [ec.course_id for ec in enrolled_courses]
    
    exams = db.query(models.Exams).options(joinedload(models.Exams.course)).filter(models.Exams.course_id.in_(course_ids)).all()
    
    result = []
    for exam in exams:
        # Check for seat allocation
        allocation = db.query(models.SeatAllocation).options(joinedload(models.SeatAllocation.room)).filter(
            models.SeatAllocation.exam_id == exam.id,
            models.SeatAllocation.student_id == student.id
        ).first()

        room_name = allocation.room.name if allocation and allocation.room else None
        seat_label = allocation.seat.seat_label if allocation and allocation.seat else None
        # Fallback if seat relationship not loaded but seat_id exists? 
        # Actually allocations.py uses seat_label. 
        # Let's ensure we fetch seat too if needed, or just room name is enough for "Room" column.
        # Frontend shows "Room {exam.room}".
        
        result.append({
            "id": exam.id,
            "title": exam.title,
            "exam_type": exam.exam_type,
            "exam_date": exam.exam_date,
            "start_time": exam.start_time,
            "duration_minutes": exam.duration_minutes,
            "status": exam.status,
            "room": room_name,   # Added
            "seat": seat_label,  # Added (if needed)
            "course": {
                "title": exam.course.title if exam.course else "Unknown Course",
                "code": exam.course.code if exam.course else "",
                "name": exam.course.name if exam.course else ""
            } if exam.course else None
        })

    return result
