from sqlalchemy.orm import Session
from db import SessionLocal, engine
import models
from passlib.context import CryptContext

# --- Compatibility Patch for passlib + bcrypt 4.x ---
import bcrypt
if not hasattr(bcrypt, '__about__'):
    class About:
        __version__ = bcrypt.__version__
    bcrypt.__about__ = About()

# Setup password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

def reset_admin():
    db = SessionLocal()
    try:
        print("Starting Admin Reset Process (Strict Foreign Key Cleanup)...")
        
        # 1. Find all users with role 'Admin'
        admins = db.query(models.User).filter(models.User.role == "Admin").all()
        print(f"Found {len(admins)} existing admins.")
        
        admin_user_ids = [u.id for u in admins]
        
        if admin_user_ids:
            # CLEAN UP FOREIGN KEYS - ADDING EVERYTHING POSSIBLE
            
            # Refresh Tokens
            db.query(models.RefreshToken).filter(models.RefreshToken.user_id.in_(admin_user_ids)).delete(synchronize_session=False)

            # Notifications
            db.query(models.Notification).filter(models.Notification.user_id.in_(admin_user_ids)).delete(synchronize_session=False)

            # Exams (Created By) - Set to NULL instead of deleting exams (exams might be important)
            # However, standard exam deletion might be cleaner for a "clean slate" admin, but let's try updating created_by to NULL first.
            # If created_by is NOT NULLABLE, we must delete.
            # Checking models.py: created_by = Column(Integer, ForeignKey("users.id")) which defaults to nullable=True usually unless specified nullable=False.
            # Let's try update to None.
            db.query(models.Exams).filter(models.Exams.created_by.in_(admin_user_ids)).update({models.Exams.created_by: None}, synchronize_session=False)
            
            # Event Documents (reviewed_by)
            db.query(models.EventDocument).filter(models.EventDocument.reviewed_by.in_(admin_user_ids)).update({models.EventDocument.reviewed_by: None}, synchronize_session=False)
            
            # Club Events (created_by) - In case admins created events?
            db.query(models.ClubEvent).filter(models.ClubEvent.created_by.in_(admin_user_ids)).update({models.ClubEvent.created_by: None}, synchronize_session=False)
            
            # Audit Logs (actor_id)
            db.query(models.AuditLog).filter(models.AuditLog.actor_id.in_(admin_user_ids)).delete(synchronize_session=False)
            
            # MindMaps
            db.query(models.MindMap).filter(models.MindMap.user_id.in_(admin_user_ids)).delete(synchronize_session=False)
            
            # Admin Profile
            db.query(models.Admin).filter(models.Admin.user_id.in_(admin_user_ids)).delete(synchronize_session=False)

            # Club Coordinator Profile (Just in case)
            db.query(models.ClubCoordinator).filter(models.ClubCoordinator.user_id.in_(admin_user_ids)).delete(synchronize_session=False)
            
            # Course Import Jobs (uploaded_by)
            db.query(models.CourseImportJob).filter(models.CourseImportJob.uploaded_by.in_(admin_user_ids)).delete(synchronize_session=False)
           
            
            db.commit() # Commit intermediate deletions
            
            # NOW DELETE USERS
            print("Deleting user records...")
            deleted_users = db.query(models.User).filter(models.User.id.in_(admin_user_ids)).delete(synchronize_session=False)
            print(f"Deleted {deleted_users} admin user accounts.")
            
        db.commit()
        
        # 2. Recreate Super Admin
        target_email = "admin@academix.ai"
        target_password = "hackathon2025"
        
        # Double check collision
        existing = db.query(models.User).filter(models.User.email == target_email).first()
        if existing:
            # Force purge existing if it wasn't an 'Admin' role before
            db.query(models.RefreshToken).filter(models.RefreshToken.user_id == existing.id).delete()
            db.query(models.Notification).filter(models.Notification.user_id == existing.id).delete()
            # Disable FK checks for this specific delete if needed? No, unsafe. 
            # Re-run cleanups for this specific ID if needed.
            db.delete(existing)
            db.commit()

        print(f"Creating new Super Admin: {target_email}")
        
        new_admin_user = models.User(
            email=target_email,
            hashed_password=get_password_hash(target_password),
            name="Super Admin",
            role="Admin",
            is_active=True
        )
        db.add(new_admin_user)
        db.commit()
        db.refresh(new_admin_user)
        
        new_admin_profile = models.Admin(
            user_id=new_admin_user.id,
            department="Administration",
            phone_number="000-000-0000"
        )
        db.add(new_admin_profile)
        db.commit()
        
        print("SUCCESS: Single Admin Account Restored.")
        print(f"Email: {target_email}")
        print(f"Password: {target_password}")
        
    except Exception as e:
        print(f"ERROR: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    reset_admin()
