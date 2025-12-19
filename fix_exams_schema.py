
from db import engine
from sqlalchemy import text, inspect

def fix_schema():
    print("Checking exams table schema...")
    try:
        inspector = inspect(engine)
        columns = [c['name'] for c in inspector.get_columns('exams')]
        
        if 'title' not in columns:
            print("Column 'title' missing. Adding it...")
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE exams ADD COLUMN title VARCHAR(150) NULL"))
                conn.commit()
            print("Column 'title' added successfully.")
        else:
            print("Column 'title' already exists.")
            
    except Exception as e:
        print(f"Error checking/fixing schema: {e}")

if __name__ == "__main__":
    fix_schema()
