
from db import engine, Base
import models
from sqlalchemy import text

def drop_exams():
    print("Dropping exams table...")
    try:
        with engine.connect() as conn:
            conn.execute(text("DROP TABLE IF EXISTS exams"))
            # Also drop dependent tables if foreign key constraint fails, or set CASCADE
            # But for now, let's try dropping exams. SeatAllocation references exams.
            conn.execute(text("SET FOREIGN_KEY_CHECKS=0;"))
            conn.execute(text("DROP TABLE IF EXISTS seat_allocations"))
            conn.execute(text("DROP TABLE IF EXISTS exam_students"))
            conn.execute(text("DROP TABLE IF EXISTS exams"))
            conn.execute(text("SET FOREIGN_KEY_CHECKS=1;"))
            conn.commit()
        print("Exams tables dropped.")
        
        print("Recreating tables...")
        models.Base.metadata.create_all(bind=engine)
        print("Tables recreated.")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    drop_exams()
