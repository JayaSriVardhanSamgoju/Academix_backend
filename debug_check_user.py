from sqlalchemy.orm import Session
from sqlalchemy import create_engine
import sys
import os

import models
import config
import auth_router as auth

# Setup direct connection
engine = create_engine(config.SQLALCHEMY_DATABASE_URL)
session = Session(bind=engine)

def check_user(email):
    print(f"Checking for user: {email}")
    user = session.query(models.User).filter(models.User.email == email).first()
    
    if user:
        print(f"✅ User FOUND: ID={user.id}, Role={user.role}")
        print(f"   Hashed Password: {user.hashed_password[:20]}...")
        
        # Test password
        is_valid = auth.verify_password("password123", user.hashed_password)
        if is_valid:
             print("✅ Password 'password123' works correctly!")
        else:
             print("❌ Password 'password123' matches FAILED. The hash might be from an old algorithm or the password is different.")
    else:
        print("❌ User NOT FOUND.")
        print("   Likely reason: The database has not been seeded.")
        print("   Recommended Action: Run 'python seed_students_list.py' to populate the database.")

if __name__ == "__main__":
    check_user("22r21a6701@student.academix.ai")
