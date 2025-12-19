from sqlalchemy import create_engine, text, inspect
import os
import sys

# Add current directory to path so we can import models and db
sys.path.append(os.getcwd())

from db import Base
from models import *  # Import all models to ensure metadata is populated

# EXPLICIT TARGET DATABASE URL
DATABASE_URL = "mysql+pymysql://root:JSPCikIqwwbeYgBzbdvWGrMvCAGdwHvj@caboose.proxy.rlwy.net:40426/railway"

def migrate_database():
    print(f"Connecting to database: {DATABASE_URL}")
    engine = create_engine(DATABASE_URL)
    
    # 1. Create any missing tables (This is safe, won't affect existing ones)
    print("Step 1: Creating missing tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables check complete.")

    # 2. Inspect existing tables and add missing columns
    print("Step 2: Checking for new columns in existing tables...")
    inspector = inspect(engine)
    
    with engine.connect() as conn:
        conn = conn.execution_options(isolation_level="AUTOCOMMIT")
        
        # --- Helper to add column safely ---
        def add_column_if_missing(table_name, column_name, column_type, default_val=None):
            columns = [col['name'] for col in inspector.get_columns(table_name)]
            if column_name not in columns:
                print(f"  -> Adding '{column_name}' to '{table_name}'...")
                try:
                    alter_query = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
                    if default_val is not None:
                        alter_query += f" DEFAULT {default_val}"
                    
                    conn.execute(text(alter_query))
                    print(f"     Success: Added {column_name}")
                except Exception as e:
                    print(f"     Error adding {column_name}: {e}")
            else:
                print(f"  -> Column '{column_name}' already exists in '{table_name}'. Skipping.")

        # --- Check 'courses' table ---
        if inspector.has_table("courses"):
            add_column_if_missing("courses", "title", "VARCHAR(100)", "'Untitled Course'")
            add_column_if_missing("courses", "enrolled_count", "INTEGER", "0")
            add_column_if_missing("courses", "syllabus_text", "TEXT")
            add_column_if_missing("courses", "mindmap_id", "INTEGER")
            add_column_if_missing("courses", "instructor_id", "INTEGER")

        # --- Check 'exams' table ---
        if inspector.has_table("exams"):
            add_column_if_missing("exams", "title", "VARCHAR(150)")
        
        # --- Check 'students' table ---
        if inspector.has_table("students"):
            # Often updated fields
            add_column_if_missing("students", "academic_status", "VARCHAR(50)", "'PROMOTED'")
            add_column_if_missing("students", "current_semester", "INTEGER")

        # --- Check 'users' table ---
        if inspector.has_table("users"):
            add_column_if_missing("users", "phone", "VARCHAR(20)")

    print("\nMigration checks completed successfully!")

if __name__ == "__main__":
    try:
        migrate_database()
    except Exception as e:
        print(f"\nCRITICAL ERROR during migration: {e}")
