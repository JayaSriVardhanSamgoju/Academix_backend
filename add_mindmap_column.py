from db import engine, SessionLocal
from sqlalchemy import text

def add_column():
    print("Attempting to add 'mindmap_id' column to 'courses' table...")
    try:
        with engine.connect() as connection:
            # Check if column exists (optional, or just catch error)
            # MySQL syntax
            sql = text("ALTER TABLE courses ADD COLUMN mindmap_id INT DEFAULT NULL;")
            connection.execute(sql)
            connection.commit() # Important for some DB drivers
            print("SUCCESS: Column 'mindmap_id' added.")
    except Exception as e:
        print(f"Error (might already exist): {e}")

if __name__ == "__main__":
    add_column()
