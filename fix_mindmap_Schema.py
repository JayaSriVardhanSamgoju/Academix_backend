from db import engine, Base
from models import MindMap
from sqlalchemy import text

def recreate_mindmaps_table():
    print("Resetting MindMap Table...")
    try:
        # Drop table if exists
        with engine.connect() as conn:
            conn.execute(text("DROP TABLE IF EXISTS mindmaps"))
            conn.commit()
        print("Dropped table 'mindmaps'.")
        
        # Create table
        Base.metadata.create_all(bind=engine)
        print("Recreated table 'mindmaps'.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    recreate_mindmaps_table()
