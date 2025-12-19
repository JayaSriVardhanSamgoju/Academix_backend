from sqlalchemy import create_engine, text
from config import SQLALCHEMY_DATABASE_URL as DATABASE_URL

def add_academic_status_column():
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        try:
            # Check if column exists
            result = conn.execute(text("PRAGMA table_info(students)"))
            columns = [row[1] for row in result.fetchall()]
            
            if "academic_status" not in columns:
                print("Adding academic_status column to students table...")
                conn.execute(text("ALTER TABLE students ADD COLUMN academic_status VARCHAR(50) DEFAULT 'PROMOTED'"))
                print("Column added successfully.")
            else:
                print("academic_status column already exists.")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    add_academic_status_column()
