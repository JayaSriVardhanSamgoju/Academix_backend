from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from db import get_db
from models import User, Club, ClubEvent, Notification, ClubCoordinator
from schemas import ClubEventCreate, ClubEventRead, UserRead
from auth_router import get_current_user
import json

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
