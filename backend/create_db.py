import pymysql
from app.core.config import settings

def create_database():
    # Parse username, host, port from DATABASE_URL
    # settings.DATABASE_URL is "mysql+pymysql://root@localhost:3306/pfa_db"
    # We will connect to MySQL without specifying the db first
    print("Connecting to MySQL server to ensure database exists...")
    connection = pymysql.connect(
        host="localhost",
        user="root",
        password="",
        port=3306
    )
    try:
        with connection.cursor() as cursor:
            cursor.execute("CREATE DATABASE IF NOT EXISTS pfa_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
            print("Database 'pfa_db' checked/created successfully.")
    finally:
        connection.close()

if __name__ == "__main__":
    create_database()
