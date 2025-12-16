from sqlalchemy.orm import Session
from db import SessionLocal
import models
import auth_router

def reset_password(email, new_password):
    db = SessionLocal()
    try:
        user = db.query(models.User).filter(models.User.email == email).first()
        if not user:
            print(f"User {email} not found!")
            return

        print(f"Resetting password for {user.name} ({user.email})...")
        hashed_pw = auth_router.get_password_hash(new_password)
        user.hashed_password = hashed_pw
        db.commit()
        print(f"Password reset to '{new_password}' successfully.")
        
        # Verify immediately
        if auth_router.verify_password(new_password, user.hashed_password):
            print("Verification check passed.")
        else:
             print("Verification check FAILED immediately.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    reset_password("22r21a6703@student.academix.ai", "password123")
