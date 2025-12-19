from sqlalchemy.orm import Session
from db import SessionLocal
import models
from passlib.context import CryptContext

# Setup password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

def reset_seating_manager():
    db = SessionLocal()
    try:
        print("Starting Seating Manager Reset Process...")
        
        # 1. Find all users with role 'Seating Manager'
        managers = db.query(models.User).filter(models.User.role == "Seating Manager").all()
        print(f"Found {len(managers)} existing Seating Managers.")
        
        manager_ids = [u.id for u in managers]
        
        if manager_ids:
            # CLEAN UP DEPENDENCIES
            
            # Refresh Tokens
            db.query(models.RefreshToken).filter(models.RefreshToken.user_id.in_(manager_ids)).delete(synchronize_session=False)

            # Notifications
            db.query(models.Notification).filter(models.Notification.user_id.in_(manager_ids)).delete(synchronize_session=False)

            # Audit Logs (actor_id)
            db.query(models.AuditLog).filter(models.AuditLog.actor_id.in_(manager_ids)).delete(synchronize_session=False)
            
            # Reset nullable Foreign Keys to avoid data loss on core tables
            # Exams (created_by)
            db.query(models.Exams).filter(models.Exams.created_by.in_(manager_ids)).update({models.Exams.created_by: None}, synchronize_session=False)
            
            # Note: Seating Managers don't have a separate profile table like 'Admin' or 'Student' in the current schema.
            # They are just Users with role="Seating Manager".
            
            db.commit() # Commit intermediate cleanups
            
            # DELETE USERS
            print("Deleting user records...")
            deleted_users = db.query(models.User).filter(models.User.id.in_(manager_ids)).delete(synchronize_session=False)
            print(f"Deleted {deleted_users} seating manager accounts.")
            
        db.commit()
        
        # 2. Recreate Single Seating Manager
        target_email = "seating_manager@academix.ai"
        target_password = "hackathon2025"
        
        # Check for collision (if user exists but had different role)
        existing = db.query(models.User).filter(models.User.email == target_email).first()
        if existing:
            print(f"User {target_email} already exists. deleting...")
            # Cleanup again for this specific ID
            db.query(models.RefreshToken).filter(models.RefreshToken.user_id == existing.id).delete()
            db.query(models.Notification).filter(models.Notification.user_id == existing.id).delete()
            db.delete(existing)
            db.commit()

        print(f"Creating new Seating Manager: {target_email}")
        
        new_manager = models.User(
            email=target_email,
            hashed_password=get_password_hash(target_password),
            name="Head Seating Manager",
            role="Seating Manager",
            is_active=True
        )
        db.add(new_manager)
        db.commit()
        db.refresh(new_manager)
        
        print("SUCCESS: Single Seating Manager Account Restored.")
        print(f"Email: {target_email}")
        print(f"Password: {target_password}")
        
    except Exception as e:
        print(f"ERROR: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    reset_seating_manager()
