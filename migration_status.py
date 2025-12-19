from sqlalchemy import create_engine, text, inspect
from config import SQLALCHEMY_DATABASE_URL

def run_migration():
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    inspector = inspect(engine)
    
    if "students" not in inspector.get_table_names():
        print("Table 'students' not found. Skipping.")
        return

    columns = [col['name'] for col in inspector.get_columns("students")]
    print(f"Existing columns: {columns}")
    
    if "academic_status" not in columns:
        print("Adding 'academic_status' column...")
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE students ADD COLUMN academic_status VARCHAR(50) DEFAULT 'PROMOTED'"))
            conn.commit()
        print("Migration successful: Added 'academic_status'.")
    else:
        print("Column 'academic_status' already exists. No action needed.")

if __name__ == "__main__":
    run_migration()
