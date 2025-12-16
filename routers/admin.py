from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Annotated

from db import get_db
import models
from models import ClubEvent, Club
import auth_router
from datetime import datetime
import json
from pydantic import BaseModel
from models import ClubEvent, Club, Notification, Exams

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
    
    # Proper query for pending approvals
    pending_approvals = db.query(models.ClubEvent).filter(
        models.ClubEvent.status == "Submitted"
    ).count()
    
    return {
        "totalStudents": total_students,
        "totalExams": total_exams,
        "roomsAvailable": total_rooms,
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
