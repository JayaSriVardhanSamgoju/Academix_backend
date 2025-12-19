from sqlalchemy import create_engine, text
from db import SQLALCHEMY_DATABASE_URL

def fix_exams_schema():
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    with engine.connect() as conn:
        print("Checking/Adding column faculty_id to exams...")
        try:
            # Check if column exists
            conn.execute(text("SELECT faculty_id FROM exams LIMIT 1"))
            print("Column already exists.")
        except Exception:
            print("Adding column faculty_id...")
            try:
                conn.execute(text("ALTER TABLE exams ADD COLUMN faculty_id INTEGER NULL"))
                print("Added 'faculty_id' column.")
            except Exception as e:
                print(f"Error adding column: {e}")
            
            try:
                # Also add constraint if needed, but NULL is safer for now
                conn.execute(text("ALTER TABLE exams ADD CONSTRAINT fk_exams_faculty FOREIGN KEY (faculty_id) REFERENCES faculty(id)"))
                print("Added foreign key constraint.")
            except Exception as e:
                print(f"Constraint might already exist or error: {e}")
            
            conn.commit()
            print("Schema updated successfully.")

if __name__ == "__main__":
    fix_exams_schema()
