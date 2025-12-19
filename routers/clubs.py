from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from db import get_db
from models import User, Club, ClubEvent, Notification, ClubCoordinator
from schemas import ClubEventCreate, ClubEventRead, UserRead
from auth_router import get_current_user
import json
import requests

router = APIRouter()

@router.get("/clubs/my-club")
def get_my_club(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Precise lookup using coordinator_id
    club = db.query(Club).filter(Club.coordinator_id == current_user.id).first()
    
    if not club:
        # Fallback for older data issues: try name match
        club = db.query(Club).filter(Club.faculty_coordinator == current_user.name).first()

    if not club:
        raise HTTPException(status_code=404, detail="No club assigned to this coordinator")
    
    return {
        "id": club.id, 
        "name": club.name, 
        "category": club.category,
        "facultyCoordinator": club.faculty_coordinator,
        "facultyContact": club.faculty_contact,
        "activeMembers": club.active_members,
    }

@router.get("/clubs/coordinator/profile")
def get_coordinator_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    profile = db.query(ClubCoordinator).filter(ClubCoordinator.user_id == current_user.id).first()
    if not profile:
         raise HTTPException(status_code=404, detail="Profile not found")
    
    return {
        "department": profile.department,
        "designation": profile.designation,
        "joinedAt": profile.joined_at
    }

@router.post("/clubs/events", response_model=ClubEventRead)
def create_event_proposal(
    event_data: ClubEventCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Resolve Club ID (Assumed from context or passed, but better to infer from user)
    # Re-using the logic to find the club
    club = db.query(Club).filter(Club.faculty_coordinator == current_user.name).first()
    if not club:
        club = db.query(Club).first() # Fallback
        if not club:
             # AUTO-FIX: Create a default club if database is empty to allow the flow to proceed
             print("DEBUG: No clubs found. Creating default 'Tech Club' for demo.")
             club = Club(
                 name="Tech Club",
                 category="Technical",
                 faculty_coordinator=current_user.name # Assign current user as coordinator
             )
             db.add(club)
             db.commit()
             db.refresh(club)

    new_event = ClubEvent(
        club_id=club.id,
        title=event_data.title,
        description=event_data.description,
        start_datetime=event_data.start_datetime,
        end_datetime=event_data.end_datetime,
        venues=event_data.venues,
        attendees=event_data.attendees,
        created_by=current_user.id,
        status="Submitted" 
    )
    
    db.add(new_event)
    db.commit()
    db.refresh(new_event)

    # --- NOTIFICATION GENERATION ---
    # 1. Notify Admin
    # 1. Notify ALL Admins
    admin_users = db.query(User).filter(User.role == "Admin").all()
    for admin_user in admin_users:
        admin_notif = Notification(
            user_id=admin_user.id,
            type="approval_request",
            title="New Event Proposal",
            body=f"Club '{club.name}' has submitted event '{new_event.title}' for approval.",
            notification_metadata=json.dumps({"event_id": new_event.id, "club_id": club.id}),
            is_read=False
        )
        db.add(admin_notif)

    # 2. Notify Coordinator (Confirmation)
    coord_notif = Notification(
        user_id=current_user.id,
        type="info",
        title="Proposal Submitted",
        body=f"Your event '{new_event.title}' has been submitted successfully.",
        notification_metadata=json.dumps({"event_id": new_event.id}),
        is_read=False
    )
    db.add(coord_notif)
    db.commit()
    # -------------------------------
    return new_event

@router.get("/clubs/events", response_model=List[ClubEventRead])
def get_club_events(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Get events for the user's club
    club = db.query(Club).filter(Club.faculty_coordinator == current_user.name).first()
    if not club:
        club = db.query(Club).first()

    if not club:
        return []

    return db.query(ClubEvent).filter(ClubEvent.club_id == club.id).order_by(ClubEvent.created_at.desc()).all()

@router.post("/clubs/events/{event_id}/register")
def register_for_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Register for an event."""
    from models import EventRegistration, Student
    
    event = db.query(ClubEvent).filter(ClubEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    student = db.query(Student).filter(Student.user_id == current_user.id).first()
    if not student:
        raise HTTPException(status_code=403, detail="Only students can register for events")
    
    # Check if already registered
    existing = db.query(EventRegistration).filter(
        EventRegistration.event_id == event_id,
        EventRegistration.student_id == student.id
    ).first()
    
    if existing:
        return {"message": "Already registered"}
    
    new_reg = EventRegistration(
        event_id=event_id,
        student_id=student.id
    )
    db.add(new_reg)
    db.commit()
    
    return {"message": "Successfully registered for " + event.title}

@router.put("/clubs/events/{event_id}", response_model=ClubEventRead)
def update_event(
    event_id: int,
    event_update: ClubEventCreate,
    background_tasks: BackgroundTasks,
    notify: bool = False,
    update_type: str = "RESCHEDULED", # RESCHEDULED or CANCELLED
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update event details (Rescheduling, Venue Change, etc.)
    Only the Faculty Coordinator of the club can update.
    """
    event = db.query(ClubEvent).filter(ClubEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    # Verify Ownership
    club = db.query(Club).filter(Club.id == event.club_id).first()
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")
        
    if club.coordinator_id != current_user.id and club.faculty_coordinator != current_user.name:
        raise HTTPException(status_code=403, detail="Not authorized to edit this event")

    # Capture changes for notification details
    changes = []
    if event.start_datetime != event_update.start_datetime:
        changes.append(f"Date/Time changed to {event_update.start_datetime.strftime('%Y-%m-%d %H:%M')}")
    if event.venues != event_update.venues:
        changes.append(f"Venue changed to {event_update.venues}")
    
    details_str = ". ".join(changes) if changes else "General update to event details."

    # Update Fields
    event.title = event_update.title
    event.description = event_update.description
    event.start_datetime = event_update.start_datetime
    event.end_datetime = event_update.end_datetime
    event.venues = event_update.venues
    event.attendees = event_update.attendees
    
    if update_type == "CANCELLED":
        event.status = "Cancelled"
    
    db.commit()
    db.refresh(event)
    
    # --- ORCHESTRATION: Send Notifications ---
    if notify:
        from models import EventRegistration
        # Fetch participants
        registrations = db.query(EventRegistration).filter(EventRegistration.event_id == event.id).all()
        recipient_emails = [reg.student.user.email for reg in registrations if reg.student and reg.student.user]
        
        if recipient_emails:
            # Trigger Communication Service
            background_tasks.add_task(
                trigger_event_notification,
                event.title,
                update_type,
                details_str,
                recipient_emails
            )
    
    return event

def trigger_event_notification(event_name: str, update_type: str, details: str, recipients: List[str]):
    """Calls the Communication Service."""
    #COMM_SERVICE_URL = "http://127.0.0.1:8001/api/v1/notify/event-update"
    COMM_SERVICE_URL = "https://mail-service-flax.vercel.app/api/v1/notify/event-update"
    payload = {
        "event_name": event_name,
        "update_type": update_type,
        "details": details,
        "recipient_list": recipients
    }
    try:
        response = requests.post(COMM_SERVICE_URL, json=payload, timeout=5)
        print(f"DEBUG: Notification service response: {response.status_code}")
    except Exception as e:
        print(f"ERROR: Failed to trigger notification service: {e}")
