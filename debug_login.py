import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from db import SessionLocal
import models
from auth_router import verify_password, get_user_by_email

def debug_login():
    db = SessionLocal()
    email = "check.faculty@academix.com"
    password = "password123"
    
    print(f"Attempting to debug login for: {email}")
    
    user = get_user_by_email(db, email)
    
    if not user:
        print("ERROR: User not found in database!")
        return
        
    print(f"User found: ID={user.id}, Role={user.role}, Active={user.is_active}")
    print(f"Stored Hash: {user.hashed_password}")
    
    is_valid = verify_password(password, user.hashed_password)
    
    if is_valid:
        print("SUCCESS: Password verifies correctly locally.")
    else:
        print("FAILURE: Password verification failed.")

if __name__ == "__main__":
    debug_login()
