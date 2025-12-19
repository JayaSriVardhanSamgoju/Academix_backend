import sys
import os

# Add current directory to sys.path so 'import config' works in db.py
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from db import SessionLocal, engine, Base
import models

def clear_admins():
    db = SessionLocal()
    try:
        print("Clearing Admin Users...")
        
        # Find users with role "Admin"
        admins = db.query(models.User).filter(models.User.role == "Admin").all()
        
        count = 0
        for admin_user in admins:
            # Delete associated Admin profile if it exists (though cascade might handle it, let's be safe/explicit if needed, 
            # or rely on foreign key cascade if configured. Models didn't specify cascade="all,delete", so manual delete of child might be needed 
            # or simple delete of user might fail if FK constraint exists without cascade)
            
            # Let's try deleting the User. If Admin table has ON DELETE CASCADE, it's fine. 
            # If not, we should delete Admin entry first.
            
            # Check for Admin entry
            admin_profile = db.query(models.Admin).filter(models.Admin.user_id == admin_user.id).first()
            if admin_profile:
                db.delete(admin_profile)
                
            db.delete(admin_user)
            count += 1
            
        db.commit()
        print(f"Successfully deleted {count} admin users.")

    except Exception as e:
        print(f"Error clearing admins: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    clear_admins()
