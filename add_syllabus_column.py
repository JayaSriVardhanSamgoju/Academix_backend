from db import engine
from sqlalchemy import text

def add_syllabus_column():
    print("Adding syllabus_text column to courses table...")
    try:
        with engine.connect() as conn:
            # Check if column exists first to avoid error
            # Simple way in MySQL: just try add, ignore if exists or check information_schema (complex).
            # We'll try the ALTER command directly.
            conn.execute(text("ALTER TABLE courses ADD COLUMN syllabus_text TEXT NULL"))
            conn.commit()
        print("Successfully added 'syllabus_text' column.")
    except Exception as e:
        print(f"Error (column might already exist): {e}")

if __name__ == "__main__":
    add_syllabus_column()
