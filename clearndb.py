import os
import sqlite3

DATABASE_PATH = "playlist.db"

def clean_db():
    try:
        # Delete the old database file if it exists
        if os.path.exists(DATABASE_PATH):
            os.remove(DATABASE_PATH)
            print(f"Removed existing database: {DATABASE_PATH}")

        # Create new database with optimized schema
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        # Create tables with proper indexes
        cursor.execute("""
        CREATE TABLE playlists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            playlist_url TEXT NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        cursor.execute("""
        CREATE TABLE videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            youtube_id TEXT NOT NULL,
            video_url TEXT NOT NULL UNIQUE,
            title TEXT NOT NULL,
            duration_seconds INTEGER,
            thumbnail_url TEXT,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        cursor.execute("""
        CREATE TABLE playlist_videos (
            playlist_id INTEGER NOT NULL,
            video_id INTEGER NOT NULL,
            position INTEGER NOT NULL,
            last_played_at TIMESTAMP,
            last_position_seconds INTEGER DEFAULT 0,
            FOREIGN KEY(playlist_id) REFERENCES playlists(id) ON DELETE CASCADE,
            FOREIGN KEY(video_id) REFERENCES videos(id) ON DELETE CASCADE,
            PRIMARY KEY (playlist_id, video_id)
        )
        """)

        cursor.execute("""
        CREATE TABLE notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            playlist_video_id INTEGER NOT NULL,
            timestamp_seconds INTEGER NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(playlist_video_id) REFERENCES playlist_videos(id) ON DELETE CASCADE
        )
        """)

        # Create indexes for faster queries
        cursor.execute("CREATE INDEX idx_videos_youtube_id ON videos (youtube_id)")
        cursor.execute("CREATE INDEX idx_playlist_videos_position ON playlist_videos (playlist_id, position)")
        cursor.execute("CREATE INDEX idx_notes_timestamp ON notes (playlist_video_id, timestamp_seconds)")

        conn.commit()
        print("Successfully created new database with optimized schema")
        
    except Exception as e:
        print(f"Error cleaning database: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    confirm = input("This will DELETE ALL YOUR DATA and recreate the database. Continue? (y/n): ").lower()
    if confirm == 'y':
        clean_db()
    else:
        print("Database cleanup cancelled")
