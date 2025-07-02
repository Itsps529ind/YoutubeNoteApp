import sqlite3

conn = sqlite3.connect("playlist.db")
c = conn.cursor()

try:
    c.execute("ALTER TABLE playlist ADD COLUMN played_time TEXT")
except sqlite3.OperationalError:
    print("Column 'played_time' already exists.")

try:
    c.execute("ALTER TABLE playlist ADD COLUMN last_video_timestamp TEXT")
except sqlite3.OperationalError:
    print("Column 'last_video_timestamp' already exists.")

conn.commit()
conn.close()
print("Migration complete.")
