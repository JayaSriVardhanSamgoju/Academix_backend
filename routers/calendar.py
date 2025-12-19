from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List
from datetime import timedelta
from db import get_db
import models
import auth_router

router = APIRouter(prefix="/calendar", tags=["Calendar"])

@router.get("/student", response_model=List[dict])
def get_student_calendar(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_router.get_current_active_user)
):
    """
    Get aggregated calendar events for a student:
    1. Upcoming Exams
    2. Approved Club Events
    """
    # Verify Student
    student = db.query(models.Student).filter(models.Student.user_id == current_user.id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")

    events = []

    # 1. Fetch Exams
    # Get exams the student is registered for
    exam_students = db.query(models.ExamStudent).options(
        joinedload(models.ExamStudent.exam).joinedload(models.Exams.course)
    ).filter(models.ExamStudent.student_id == student.id).all()

    for es in exam_students:
        exam = es.exam
        if not exam: continue
        
        # Check if seat is allocated for room info
        allocation = db.query(models.SeatAllocation).options(joinedload(models.SeatAllocation.room)).filter(
            models.SeatAllocation.exam_id == exam.id,
            models.SeatAllocation.student_id == student.id
        ).first()

        room_name = allocation.room.name if allocation and allocation.room else "To be announced"
        seat_info = str(allocation.seat.seat_label) if allocation and allocation.seat else None

        events.append({
            "id": f"exam_{exam.id}",
            "type": "exam",
            "title": f"{exam.course.title} Exam", # e.g. "Data Structures Exam"
            "course": exam.course.name,
            "course_code": exam.course.code,
            "date": exam.exam_date.strftime("%Y-%m-%d"),
            "start": exam.start_time.strftime("%I:%M %p"),
            "end": (exam.start_time + timedelta(minutes=exam.duration_minutes)).strftime("%I:%M %p"),
            "duration": f"{exam.duration_minutes} mins",
            "venue": room_name,
            "room": room_name,
            "seat": seat_info,
            "color": "#06b6d4", # Cyan
            "description": f"Exam for {exam.course.name}"
        })

    # 2. Fetch Club Events (Approved/Submitted)
    # For now showing ALL events. In real app, maybe filter by interest?
    # Assuming 'Submitted' is visible or we should filter by 'Approved' if that status exists.
    # The models show default 'draft', creates as 'Submitted'. Let's show all non-draft for now or just 'Submitted'.
    # Actually, let's show all events that are created.
    club_events = db.query(models.ClubEvent).options(joinedload(models.ClubEvent.club)).all()

    for event in club_events:
        # Skip drafts if needed, but for demo let's show them
        if event.status == 'draft': continue

        events.append({
            "id": f"event_{event.id}",
            "type": "event",
            "title": event.title,
            "club": event.club.name if event.club else "Club Event",
            "date": event.start_datetime.strftime("%Y-%m-%d") if event.start_datetime else "",
            "start": event.start_datetime.strftime("%I:%M %p") if event.start_datetime else "",
            "end": event.end_datetime.strftime("%I:%M %p") if event.end_datetime else "",
            "venue": event.venues,
            "color": "#a855f7", # Purple
            "description": event.description or "No description provided."
        })

    return events
