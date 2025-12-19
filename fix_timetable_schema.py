from sqlalchemy import create_engine, text
from config import SQLALCHEMY_DATABASE_URL

def fix_timetable_schema():
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    with engine.connect() as conn:
        print("Checking/Adding columns to timetable_entries...")
        try:
            # Check if columns exist by attempting to select them (quickest way in SQL without complex introspection)
            conn.execute(text("SELECT room, class_type FROM timetable_entries LIMIT 1"))
            print("Columns already exist.")
        except Exception:
            print("Adding columns room and class_type...")
            try:
                # Add room column
                conn.execute(text("ALTER TABLE timetable_entries ADD COLUMN room VARCHAR(50)"))
                print("Added 'room' column.")
            except Exception as e:
                print(f"Room column might already exist or error: {e}")
                
            try:
                # Add class_type column
                conn.execute(text("ALTER TABLE timetable_entries ADD COLUMN class_type VARCHAR(20) DEFAULT 'Lecture'"))
                print("Added 'class_type' column.")
            except Exception as e:
                print(f"class_type column might already exist or error: {e}")
            
            conn.commit()
            print("Schema updated successfully.")

if __name__ == "__main__":
    fix_timetable_schema()
