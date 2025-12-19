import pymysql
from urllib.parse import urlparse

# Connection string from config.py: "mysql+pymysql://root:1105@localhost/academic_db"
DB_USER = "root"
DB_PASS = "1105"
DB_HOST = "localhost"
DB_NAME = "academic_db"

def create_database():
    try:
        # Connect to MySQL server (not the specific database)
        connection = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASS
        )
        cursor = connection.cursor()
        
        # Recreate database
        print(f"Dropping database '{DB_NAME}' if exists...")
        cursor.execute(f"DROP DATABASE IF EXISTS {DB_NAME}")
        print(f"Creating database '{DB_NAME}'...")
        cursor.execute(f"CREATE DATABASE {DB_NAME}")
        print("Database created or already exists.")
        
        cursor.close()
        connection.close()

        # Try connecting to the specific database
        print(f"Testing connection to '{DB_NAME}'...")
        conn2 = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASS,
            database=DB_NAME
        )
        print("Connected to database successfully!")
        conn2.close()

    except Exception as e:
        print(f"Error creating/connecting database: {e}")

if __name__ == "__main__":
    create_database()
