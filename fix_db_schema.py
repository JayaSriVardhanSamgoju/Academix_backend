import logging
from sqlalchemy import text, inspect
from db import engine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_schema():
    """
    Fixes the database schema by adding missing columns.
    """
    inspector = inspect(engine)
    
    # Check if 'exams' table exists
    if not inspector.has_table("exams"):
        logger.error("Table 'exams' does not exist.")
        return

    # Check columns in 'exams' table
    columns = [col['name'] for col in inspector.get_columns("exams")]
    logger.info(f"Existing columns in 'exams': {columns}")

    with engine.connect() as connection:
        # Check and add 'faculty_id' to 'exams' table
        if "faculty_id" not in columns:
            logger.info("Adding 'faculty_id' column to 'exams' table...")
            try:
                connection.execute(text("ALTER TABLE exams ADD COLUMN faculty_id INT NULL"))
                logger.info("'faculty_id' column added successfully.")
                
                # Check if 'faculty' table exists before adding Foreign Key
                if inspector.has_table("faculty"):
                    logger.info("Adding Foreign Key constraint for 'faculty_id'...")
                    try:
                        connection.execute(text("ALTER TABLE exams ADD CONSTRAINT fk_exams_faculty FOREIGN KEY (faculty_id) REFERENCES faculty(id)"))
                        logger.info("Foreign Key constraint added successfully.")
                    except Exception as e:
                        logger.warning(f"Failed to add Foreign Key constraint: {e}")
                else:
                    logger.warning("'faculty' table does not exist. Skipping Foreign Key constraint.")
                    
                connection.commit()
            except Exception as e:
                logger.error(f"Error adding 'faculty_id' column: {e}")
                connection.rollback()
        else:
            logger.info("'faculty_id' column already exists in 'exams' table.")

if __name__ == "__main__":
    fix_schema()
