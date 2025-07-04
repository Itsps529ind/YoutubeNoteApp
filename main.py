import sys
import os
import sqlite3
import re
import yt_dlp
from PyQt5.QtWidgets import QListWidgetItem, QHBoxLayout, QLabel, QPushButton 
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QListWidget, QTextEdit, QFileDialog, QMessageBox
)
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings
from PyQt5.QtCore import QUrl, Qt

# Setup
os.makedirs("notes", exist_ok=True)
DB_PATH = "playlist.db"

# Initialize DB
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# Create tables if not exist
c.execute('''
CREATE TABLE IF NOT EXISTS playlists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    playlist_url TEXT UNIQUE
)
''')

c.execute('''
CREATE TABLE IF NOT EXISTS videos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    youtube_id TEXT UNIQUE,
    video_url TEXT,
    title TEXT
)
''')

c.execute('''
CREATE TABLE IF NOT EXISTS playlist_videos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    playlist_id INTEGER,
    video_id INTEGER,
    position INTEGER,
    last_position_seconds INTEGER DEFAULT 0,
    FOREIGN KEY (playlist_id) REFERENCES playlists(id),
    FOREIGN KEY (video_id) REFERENCES videos(id),
    UNIQUE (playlist_id, video_id)
)
''')

conn.commit()

class YouTubeNotesApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("\U0001F4D8 YouTube Playlist Notes App")
        self.setMinimumSize(1000, 700)

        self.current_video_title = None
        self.current_video_url = None
        self.current_video_id = None
        self.current_playlist_id = None
        self.video_data = []
        self.playback_cache = {}
        self.resume_prompt_connected = False

        self.video_player = QWebEngineView()
        settings = self.video_player.settings()
        settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.PluginsEnabled, True)
        settings.setAttribute(QWebEngineSettings.FullScreenSupportEnabled, True)
        settings.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)

        self.layout = QVBoxLayout(self)
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Paste YouTube playlist URL here and press Enter")
        self.url_input.returnPressed.connect(self.on_enter_pressed)
        self.layout.addWidget(self.url_input)

        self.fetch_btn = QPushButton("Fetch Videos")
        self.fetch_btn.clicked.connect(self.fetch_videos)
        self.layout.addWidget(self.fetch_btn)

        self.split_layout = QHBoxLayout()
        self.layout.addLayout(self.split_layout)

        self.video_list = QListWidget()
        self.video_list.itemClicked.connect(self.play_selected_video)
        self.split_layout.addWidget(self.video_list, 30)

        self.right_panel = QVBoxLayout()
        self.split_layout.addLayout(self.right_panel, 70)
        self.right_panel.addWidget(self.video_player, 60)

        self.notes = QTextEdit()
        self.notes.setPlaceholderText("Take your notes here...")
        self.right_panel.addWidget(self.notes, 30)

        self.buttons = QHBoxLayout()
        self.right_panel.addLayout(self.buttons)

        self.add_playlist_btn = QPushButton("➕ Add Playlist to DB")
        self.add_playlist_btn.setEnabled(False)
        self.add_playlist_btn.clicked.connect(self.save_playlist_to_db)
        self.buttons.addWidget(self.add_playlist_btn)

        self.timestamp_btn = QPushButton("⏱ Insert Timestamp")
        self.timestamp_btn.clicked.connect(self.insert_timestamp)
        self.buttons.addWidget(self.timestamp_btn)

        self.save_btn = QPushButton("💾 Save Note")
        self.save_btn.clicked.connect(self.save_note)
        self.buttons.addWidget(self.save_btn)

        self.timestamp_btn.setEnabled(False)
        self.save_btn.setEnabled(False)

    def on_enter_pressed(self):
        """Handler for when Enter key is pressed in URL input"""
        if not self.url_input.text().strip():
            QMessageBox.warning(self, "Error", "Please enter a playlist URL first")
        else:
            self.fetch_videos()

    def fetch_videos(self):
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Error", "Please enter a playlist URL")
            return

        try:
            ydl_opts = {
                'quiet': True,
                'extract_flat': True,
                'dump_single_json': True
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                self.video_data.clear()
                self.video_list.clear()

                for entry in info['entries']:
                    title = entry['title']
                    video_url = f"https://www.youtube.com/watch?v={entry['id']}"
                    youtube_id = entry['id']
                    self.video_data.append((youtube_id, video_url, title))
                    
                    # Create custom widget for each video
                    item = QListWidgetItem()
                    widget = QWidget()
                    layout = QHBoxLayout()
                    
                    # Add video title
                    title_label = QLabel(title)
                    layout.addWidget(title_label, stretch=1)
                    
                    # Add open button
                    open_btn = QPushButton("Play ▶")
                    open_btn.clicked.connect(lambda _, vid_url=video_url: self.play_video_by_url(vid_url))
                    layout.addWidget(open_btn)
                    
                    widget.setLayout(layout)
                    item.setSizeHint(widget.sizeHint())
                    
                    self.video_list.addItem(item)
                    self.video_list.setItemWidget(item, widget)

            c.execute("SELECT id FROM playlists WHERE playlist_url = ?", (url,))
            result = c.fetchone()

            if result:
                self.current_playlist_id = result[0]
                self.add_playlist_btn.setEnabled(False)
                self.timestamp_btn.setEnabled(True)
                self.save_btn.setEnabled(True)
                QMessageBox.information(self, "Info", "Existing playlist loaded from database")
            else:
                self.add_playlist_btn.setEnabled(True)
                QMessageBox.information(self, "Success", f"Fetched {len(self.video_data)} videos. Click 'Add Playlist' to save.")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to fetch playlist:\n{str(e)}")

    def play_video_by_url(self, video_url):
        """Play video directly from URL"""
        # Find the video in our data
        for youtube_id, v_url, title in self.video_data:
            if v_url == video_url:
                self.current_video_title = title
                self.current_video_url = video_url
                self.current_video_id = youtube_id
                break
                
        self.notes.clear()
        self.video_player.load(QUrl(video_url))
        
        # Disconnect any previous handlers
        try:
            self.video_player.page().loadFinished.disconnect()
        except Exception:
            pass
            
        # Connect new handler
        self.video_player.page().loadFinished.connect(
            lambda ok: self.check_saved_video_position(ok),
            Qt.QueuedConnection
        )
    def save_playlist_to_db(self):
        url = self.url_input.text().strip()
        try:
            c.execute("INSERT INTO playlists (playlist_url) VALUES (?)", (url,))
            self.current_playlist_id = c.lastrowid

            for position, (youtube_id, video_url, title) in enumerate(self.video_data, start=1):
                c.execute("""
                    INSERT OR IGNORE INTO videos (youtube_id, video_url, title) 
                    VALUES (?, ?, ?)
                """, (youtube_id, video_url, title))

                c.execute("SELECT id FROM videos WHERE youtube_id = ?", (youtube_id,))
                video_id = c.fetchone()[0]

                c.execute("""
                    INSERT INTO playlist_videos (playlist_id, video_id, position) 
                    VALUES (?, ?, ?)
                """, (self.current_playlist_id, video_id, position))

            conn.commit()
            self.add_playlist_btn.setEnabled(False)
            self.timestamp_btn.setEnabled(True)
            self.save_btn.setEnabled(True)
            QMessageBox.information(self, "Success", "Playlist saved to database")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save playlist:\n{str(e)}")

    def play_selected_video(self, item):
        new_title = item.text()
        new_video_id, new_video_url = None, None

        for youtube_id, video_url, title in self.video_data:
            if title == new_title:
                new_video_id = youtube_id
                new_video_url = video_url
                break

        if self.current_video_id and self.current_video_id != new_video_id:
            self.save_current_video_timestamp()

        self.current_video_title = new_title
        self.current_video_url = new_video_url
        self.current_video_id = new_video_id
        self.notes.clear()
        self.video_player.load(QUrl(self.current_video_url))

        if self.resume_prompt_connected:
            try:
                self.video_player.page().loadFinished.disconnect(self.check_saved_video_position)
            except Exception:
                pass

        self.video_player.page().loadFinished.connect(self.check_saved_video_position)
        self.resume_prompt_connected = True

    def save_current_video_timestamp(self):
        if not all([self.current_video_id, self.current_playlist_id]):
            return

        js = """
            (function() {
                var player = document.querySelector('video');
                return player ? Math.floor(player.currentTime) : 0;
            })();
        """

        def callback(seconds):
            try:
                if seconds > 0:
                    c.execute("""
                        UPDATE playlist_videos
                        SET last_position_seconds = ?
                        WHERE playlist_id = ? 
                        AND video_id = (SELECT id FROM videos WHERE youtube_id = ?)
                    """, (seconds, self.current_playlist_id, self.current_video_id))
                    conn.commit()
            except Exception as e:
                print("Error saving timestamp:", e)

        self.video_player.page().runJavaScript(js, callback)

    def check_saved_video_position(self, ok):
        if not ok or not self.current_video_id or not self.current_playlist_id:
            return

        try:
            c.execute("""
                SELECT last_position_seconds FROM playlist_videos
                WHERE playlist_id = ? 
                AND video_id = (SELECT id FROM videos WHERE youtube_id = ?)
            """, (self.current_playlist_id, self.current_video_id))

            result = c.fetchone()
            if result and result[0] is not None and result[0] > 0:
                seconds = result[0]
                mins, secs = divmod(seconds, 60)

                reply = QMessageBox.question(
                    self, "Resume Playback?",
                    f"Resume '{self.current_video_title}' at {mins}:{secs:02}?",
                    QMessageBox.Yes | QMessageBox.No
                )

                if reply == QMessageBox.Yes:
                    js = f"""
                        var player = document.querySelector('video');
                        if (player) {{
                            player.currentTime = {seconds};
                            player.play();
                        }}
                    """
                    self.video_player.page().runJavaScript(js)
        except Exception as e:
            print("Error checking for resume:", e)

    def insert_timestamp(self):
        js = """
            (function() {
                var player = document.querySelector('video');
                if (!player) return "00:00";
                var time = Math.floor(player.currentTime);
                var mins = Math.floor(time / 60);
                var secs = time % 60;
                return "[" + mins.toString().padStart(2, '0') + 
                    ":" + secs.toString().padStart(2, '0') + "] ";
            })();
        """

        def callback(timestamp):
            cursor = self.notes.textCursor()
            cursor.insertText(timestamp)

        self.video_player.page().runJavaScript(js, callback)

    def save_note(self):
        note = self.notes.toPlainText().strip()
        if not note:
            QMessageBox.warning(self, "Empty Note", "Cannot save empty note.")
            return

        safe_title = re.sub(r'[\\/*?:"<>|]', "", self.current_video_title)
        default_name = f"notes/{safe_title}.txt"

        filename, _ = QFileDialog.getSaveFileName(
            self, "Save Note", default_name, "Text Files (*.txt)"
        )

        if filename:
            try:
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(note)
                QMessageBox.information(self, "Saved", f"Note saved to:\n{filename}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save note:\n{e}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = YouTubeNotesApp()
    window.show()
    sys.exit(app.exec_())

#  this is new code with new concept but resume video remain same it always showint to resume of last played video not that original video consider this again try fix resum time stamp problem that has same error