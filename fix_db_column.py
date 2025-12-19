from sqlalchemy import text
from db import engine

def fix_schema():
    print("Checking database schema...")
    with engine.connect() as connection:
        try:
            # Check if column exists
            # This is a bit rough, but 'ADD COLUMN IF NOT EXISTS' is MariaDB 10.2+ or MySQL 8.0.29+ (sometimes)
            # Safe way: try to add, ignore error if duplicate column code 1060
            
            print("Attempting to add 'enrolled_at' column to 'course_enrollments'...")
            connection.execute(text("ALTER TABLE course_enrollments ADD COLUMN enrolled_at DATETIME;"))
            connection.commit()
            print("Column 'enrolled_at' added successfully.")
        except Exception as e:
            if "Duplicate column name" in str(e) or "1060" in str(e):
                 print("Column 'enrolled_at' already exists. Skipping.")
            else:
                print(f"Error adding column: {e}")
                # It might fail if table doesn't exist, which is fine, models creation will handle it? 
                # But we know table exists from the user error.

if __name__ == "__main__":
    fix_schema()
