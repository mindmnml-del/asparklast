import sqlite3
import os

db_path = r"D:\aisparklast - Copy\backend\aispark_studio.db"

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN credits INTEGER DEFAULT 3")
        conn.commit()
        print("Successfully added 'credits' column to 'users' table.")
    except sqlite3.OperationalError as e:
        print(f"OperationalError (might already exist): {e}")
    finally:
        conn.close()
else:
    print(f"Database not found at {db_path}")
