from sqlalchemy.orm import Session
from db import SessionLocal
import models
import json

def backfill_notifications():
    db = SessionLocal()
    try:
        # Get pending events
        pending_events = db.query(models.ClubEvent).filter(models.ClubEvent.status == "Submitted").all()
        
        # Get admin user
        admin_user = db.query(models.User).filter(models.User.role == "Admin").first()
        if not admin_user:
            print("No admin user found.")
            return

        count = 0
        for event in pending_events:
            # Check if notification already exists
            exists = db.query(models.Notification).filter(
                models.Notification.notification_metadata.contains(json.dumps({"event_id": event.id})),
                models.Notification.type == "approval_request"
            ).first()

            if not exists:
                club = db.query(models.Club).filter(models.Club.id == event.club_id).first()
                club_name = club.name if club else "Unknown Club"
                
                notif = models.Notification(
                    user_id=admin_user.id,
                    type="approval_request",
                    title="New Event Proposal (Backfilled)",
                    body=f"Club '{club_name}' has submitted event '{event.title}' for approval.",
                    notification_metadata=json.dumps({"event_id": event.id}),
                    is_read=False
                )
                db.add(notif)
                count += 1
                print(f"Created notification for event: {event.title}")

        db.commit()
        print(f"Backfilled {count} notifications.")
    
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    backfill_notifications()
