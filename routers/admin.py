from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session, joinedload
from typing import Annotated

from db import get_db
import models
from models import ClubEvent, Club
import auth_router
from datetime import datetime
import json
from pydantic import BaseModel
from models import ClubEvent, Club, Notification, Exams
import requests

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/dashboard/stats")
def get_dashboard_stats(
    current_user: Annotated[models.User, Depends(auth_router.get_current_active_user)],
    db: Session = Depends(get_db)
):
    """Get admin dashboard statistics"""
    # TODO: Add role check to ensure user is admin
    
    today = datetime.now()
    total_students = db.query(models.Student).count()
    total_exams = db.query(models.Exams).count()
    total_rooms = db.query(models.Room).count()
    total_faculty = db.query(models.Faculty).count()
    
    # Proper query for pending approvals
    pending_approvals = db.query(models.ClubEvent).filter(
        models.ClubEvent.status == "Submitted"
    ).count()
    
    return {
        "totalStudents": total_students,
        "totalExams": total_exams,
        "roomsAvailable": total_rooms,
        "totalFaculty": total_faculty,
        "pendingApprovals": pending_approvals
    }


@router.get("/exams/upcoming")
def get_upcoming_exams(
    current_user: Annotated[models.User, Depends(auth_router.get_current_active_user)],
    db: Session = Depends(get_db)
):
    """Get upcoming exams for admin dashboard"""
    # TODO: Add role check to ensure user is admin
    # TODO: Filter by future dates and add proper formatting
    
    exams = db.query(models.Exams).limit(10).all()
    
    return [{
        "id": exam.id,
        "course": exam.course.title if exam.course else "Unknown Course",
        "date": exam.exam_date.strftime("%b %d, %Y") if exam.exam_date else "TBA",
        "time": exam.start_time.strftime("%I:%M %p") if exam.start_time else "TBA",
        "status": "Published"  # TODO: Add status field to Exam model
    } for exam in exams]


@router.get("/audit-logs/recent")
def get_recent_activities(
    current_user: Annotated[models.User, Depends(auth_router.get_current_active_user)],
    db: Session = Depends(get_db)
):
    """Get recent audit logs/activities"""
    # TODO: Add role check to ensure user is admin
    # TODO: Query actual audit_logs table
    
    # Placeholder until audit logs are properly implemented
    return []


@router.get("/events/pending")
def get_pending_events(
    current_user: Annotated[models.User, Depends(auth_router.get_current_active_user)],
    db: Session = Depends(get_db)
):
    """Get events pending approval"""
    # TODO: Add role check to ensure user is admin
    
    events = db.query(ClubEvent).filter(ClubEvent.status == "Submitted").order_by(ClubEvent.created_at.asc()).all()
    
    result = []
    for event in events:
        club = db.query(Club).filter(Club.id == event.club_id).first()
        result.append({
            "id": event.id,
            "eventName": event.title,
            "clubName": club.name if club else "Unknown Club",
            "status": event.status,
            "submittedAt": event.created_at # Add if model has it
        })
    return result

@router.get("/events")
def get_all_events(
    current_user: Annotated[models.User, Depends(auth_router.get_current_active_user)],
    db: Session = Depends(get_db)
):
    """Get all events (history) for admin"""
    # TODO: Add role check
    
    events = db.query(ClubEvent).order_by(ClubEvent.created_at.desc()).all()
    
    result = []
    for event in events:
        club = db.query(Club).filter(Club.id == event.club_id).first()
        result.append({
            "id": event.id,
            "title": event.title, # Frontend uses title
            "eventName": event.title, # Keeping both for compatibility if needed
            "clubName": club.name if club else "Unknown Club",
            "club": club.name if club else "Unknown Club",
            "requestedDate": event.start_datetime.strftime("%Y-%m-%d") if event.start_datetime else "TBA",
            "venue": event.venues or "TBA",
            "status": event.status,
            "submittedAt": event.created_at # Add if model has it
        })
    return result

class EventStatusUpdate(BaseModel):
    status: str

@router.get("/events/{event_id}")
def get_event_details(
    event_id: int,
    current_user: Annotated[models.User, Depends(auth_router.get_current_active_user)],
    db: Session = Depends(get_db)
):
    """Get event details by ID"""
    # TODO: Add admin role check
    
    event = db.query(ClubEvent).filter(ClubEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
        
    # Enrich with club name
    club = db.query(Club).filter(Club.id == event.club_id).first()
    
    # Return a dict mixed with event attributes (simplest way without new schema)
    event_dict = event.__dict__
    if "_sa_instance_state" in event_dict:
        del event_dict["_sa_instance_state"]
        
    event_dict["club_name"] = club.name if club else "Unknown Club"
    return event_dict

@router.put("/events/{event_id}/status")
def update_event_status(
    event_id: int,
    status_data: EventStatusUpdate,
    current_user: Annotated[models.User, Depends(auth_router.get_current_active_user)],
    db: Session = Depends(get_db)
):
    """Update event status (Approved/Rejected)"""
    # TODO: Add admin role check
    
    event = db.query(ClubEvent).filter(ClubEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
        
    new_status = status_data.status
    if new_status not in ["Approved", "Rejected"]:
        raise HTTPException(status_code=400, detail="Invalid status")
        
    event.status = new_status
    
    # notify coordinator
    notif = Notification(
        user_id=event.created_by,
        type="approval" if new_status == "Approved" else "info",
        title=f"Event {new_status}",
        body=f"Your event '{event.title}' has been {new_status.lower()}.",
        notification_metadata=json.dumps({"event_id": event.id}),
        is_read=False
    )
    db.add(notif)
    
    db.commit()
    return {"message": "Status updated"}

@router.get("/calendar/events")
def get_all_calendar_events(
    current_user: Annotated[models.User, Depends(auth_router.get_current_active_user)],
    db: Session = Depends(get_db)
):
    """Get all events and exams for the admin calendar"""
    # TODO: Add admin role check
    
    # 1. Get all Club Events
    club_events = db.query(ClubEvent).all()
    
    # 2. Get all Exams
    exams = db.query(Exams).all()
    
    calendar_data = []
    
    # Process Club Events
    for event in club_events:
        calendar_data.append({
            "id": f"event-{event.id}",
            "title": event.title,
            "start": event.start_datetime,
            "end": event.end_datetime,
            "type": "Club Event",
            "status": event.status,
            "details": event.description
        })
        
    # Process Exams
    for exam in exams:
        calendar_data.append({
            "id": f"exam-{exam.id}",
            "title": f"Exam: {exam.course.code if exam.course else 'Unknown'}",
            "start": exam.start_time,
            "end": exam.start_time, # Exams might just have start time for now
            "type": "Exam",
            "status": exam.status,
            "details": f"Duration: {exam.duration_minutes} mins"
        })
        
    return calendar_data

class AssignCourseRequest(BaseModel):
    faculty_id: int
    course_id: int

@router.post("/faculty/assign-course")
def assign_course_to_faculty(
    req: AssignCourseRequest,
    background_tasks: BackgroundTasks,
    current_user: Annotated[models.User, Depends(auth_router.get_current_active_user)],
    db: Session = Depends(get_db)
):
    """Assign a course to a teaching faculty member."""
    # TODO: Add proper admin role check
    
    # Check faculty type
    faculty = db.query(models.Faculty).filter(models.Faculty.id == req.faculty_id).first()
    if not faculty:
        raise HTTPException(status_code=404, detail="Faculty not found")
        
    if faculty.faculty_type != "TEACHING":
        raise HTTPException(status_code=400, detail="Cannot assign course to non-teaching faculty")
        
    # Check if assignment already exists
    existing = db.query(models.FacultyCourseAssignment).filter(
        models.FacultyCourseAssignment.faculty_id == req.faculty_id,
        models.FacultyCourseAssignment.course_id == req.course_id
    ).first()
    
    if existing:
        return {"message": "Course already assigned to this faculty"}
        
    # Create assignment
    assign = models.FacultyCourseAssignment(
        faculty_id=req.faculty_id,
        course_id=req.course_id
    )
    db.add(assign)
    db.commit()

    # --- Trigger Notification ---
    def send_assignment_notification(fac_id, fac_email, fac_name, sub_name, students):
        try:
            notify_payload = {
                "faculty_id": str(fac_id),
                "faculty_email": fac_email,
                "faculty_name": fac_name or "Faculty Member",
                "subject_name": sub_name,
                "students": students # List of {name, email, roll_number}
            }
            # requests.post("http://127.0.0.1:8001/api/v1/notify/faculty-assignment", json=notify_payload, timeout=5)
            requests.post("https://mail-service-flax.vercel.app/api/v1/notify/faculty-assignment", json=notify_payload, timeout=5)
        except Exception as e:
            print(f"Notification Service error: {e}")

    course = db.query(models.Course).filter(models.Course.id == req.course_id).first()
    if course and faculty.user:
        # Fetch enrolled students' details
        students_info = [
            {
                "name": enrollment.student.user.name, 
                "email": enrollment.student.user.email,
                "roll_number": enrollment.student.roll_number
            }
            for enrollment in db.query(models.CourseEnrollment)
                .options(joinedload(models.CourseEnrollment.student).joinedload(models.Student.user))
                .filter(models.CourseEnrollment.course_id == req.course_id)
                .all()
            if enrollment.student and enrollment.student.user
        ]

        print(f"DEBUG: Found {len(students_info)} students for course {req.course_id}: {[s['name'] for s in students_info]}")

        background_tasks.add_task(
            send_assignment_notification, 
            faculty.id, 
            faculty.user.email, 
            faculty.user.name, 
            course.title,
            students_info
        )

    return {"message": "Course assigned successfully"}

@router.post("/faculty/unassign-course")
def unassign_course_from_faculty(
    req: AssignCourseRequest,
    current_user: Annotated[models.User, Depends(auth_router.get_current_active_user)], # TODO: Admin check
    db: Session = Depends(get_db)
):
    """Remove a course assignment from a faculty member."""
    assignment = db.query(models.FacultyCourseAssignment).filter(
        models.FacultyCourseAssignment.faculty_id == req.faculty_id,
        models.FacultyCourseAssignment.course_id == req.course_id
    ).first()
    
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
        
    db.delete(assignment)
    db.commit()
    
    return {"message": "Course unassigned successfully"}
@router.post("/students/{student_id}/reset-password")
def reset_student_password(
    student_id: int,
    req: dict, # Expecting {"password": "new_password"}
    current_user: Annotated[models.User, Depends(auth_router.get_current_active_admin)],
    db: Session = Depends(get_db)
):
    student = db.query(models.Student).filter(models.Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    user = db.query(models.User).filter(models.User.id == student.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Associated user not found")
    
    new_password = req.get("password")
    if not new_password or len(new_password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters long")
    
    user.hashed_password = auth_router.get_password_hash(new_password)
    db.commit()
    
    return {"message": "Password reset successfully"}

@router.get("/reports/academic-risks")
def get_academic_risk_report(
    current_user: Annotated[models.User, Depends(auth_router.get_current_active_user)],
    db: Session = Depends(get_db)
):
    """
    Identify students with backlogs (Marks < 40).
    Returns list of students with their failed subjects.
    """
    # 1. Fetch all failed marks
    failures = db.query(models.StudentMark).options(
        joinedload(models.StudentMark.student).joinedload(models.Student.user),
        joinedload(models.StudentMark.student).joinedload(models.Student.branch),
        joinedload(models.StudentMark.course)
    ).filter(models.StudentMark.marks_obtained < 40).all()

    # 2. Group by Student
    risk_map = {}
    for f in failures:
        sid = f.student_id
        if sid not in risk_map:
            s = f.student
            risk_map[sid] = {
                "student_id": s.id,
                "roll_number": s.roll_number,
                "name": s.user.name if s.user else "Unknown",
                "email": s.user.email if s.user else "",
                "phone": s.user.phone if s.user else "",
                "is_active": s.user.is_active if s.user else False, 
                "program": s.branch.name if s.branch else "Unknown",
                "current_status": s.academic_status,
                "backlog_count": 0,
                "failed_subjects": []
            }
        
        risk_map[sid]["backlog_count"] += 1
        risk_map[sid]["failed_subjects"].append({
            "code": f.course.code if f.course else "???",
            "title": f.course.title if f.course else "Unknown Subject",
            "marks": f.marks_obtained,
            "type": f.exam_type
        })
    
    # Sort by backlog count descending
    return sorted(list(risk_map.values()), key=lambda x: x["backlog_count"], reverse=True)
