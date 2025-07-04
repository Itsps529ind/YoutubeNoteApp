# import sys
# import os
# from PyQt5.QtWidgets import (
#     QApplication, QWidget, QVBoxLayout, QHBoxLayout,
#     QLineEdit, QPushButton, QListWidget, QTextEdit, QFileDialog, QMessageBox
# )
# from PyQt5.QtWebEngineWidgets import QWebEngineView
# from PyQt5.QtCore import QUrl
# from pytube import Playlist
# import datetime

# # Create notes folder if not exists
# os.makedirs("notes", exist_ok=True)

# class YouTubeNotesApp(QWidget):
#     def __init__(self):
#         super().__init__()
#         self.setWindowTitle("\U0001F4D8 YouTube Playlist Notes App")
#         self.setMinimumSize(1000, 700)

#         self.video_urls = []

#         self.layout = QVBoxLayout()
#         self.setLayout(self.layout)

#         # Playlist URL input
#         self.url_input = QLineEdit()
#         self.url_input.setPlaceholderText("Paste YouTube playlist URL here")
#         self.layout.addWidget(self.url_input)

#         self.fetch_btn = QPushButton("Fetch Videos")
#         self.fetch_btn.clicked.connect(self.fetch_videos)
#         self.layout.addWidget(self.fetch_btn)

#         # Horizontal split
#         self.split_layout = QHBoxLayout()
#         self.layout.addLayout(self.split_layout)

#         # Video list
#         self.video_list = QListWidget()
#         self.video_list.itemClicked.connect(self.play_selected_video)
#         self.split_layout.addWidget(self.video_list, 25)

#         # Video + notes column
#         self.right_panel = QVBoxLayout()
#         self.split_layout.addLayout(self.right_panel, 75)

#         # Embedded video
#         self.video_player = QWebEngineView()
#         self.right_panel.addWidget(self.video_player, 65)

#         # Notes area
#         self.notes = QTextEdit()
#         self.notes.setPlaceholderText("Take your notes here...")
#         self.right_panel.addWidget(self.notes, 30)

#         # Buttons
#         self.buttons = QHBoxLayout()
#         self.right_panel.addLayout(self.buttons)

#         self.timestamp_btn = QPushButton("\u23F1 Insert Timestamp")
#         self.timestamp_btn.clicked.connect(self.insert_timestamp)
#         self.buttons.addWidget(self.timestamp_btn)

#         self.save_btn = QPushButton("\U0001F4BE Save Note")
#         self.save_btn.clicked.connect(self.save_note)
#         self.buttons.addWidget(self.save_btn)

#     def fetch_videos(self):
#         url = self.url_input.text()
#         if not url:
#             QMessageBox.warning(self, "Error", "Please enter a playlist URL")
#             return
#         try:
#             playlist = Playlist(url)
#             self.video_urls = playlist.video_urls
#             self.video_list.clear()
#             for i, video_url in enumerate(self.video_urls):
#                 self.video_list.addItem(f"{i+1}. {video_url}")
#             QMessageBox.information(self, "Success", f"Fetched {len(self.video_urls)} videos.")
#         except Exception as e:
#             QMessageBox.critical(self, "Error", f"Failed to fetch playlist:\n{e}")

#     def play_selected_video(self, item):
#         index = self.video_list.row(item)
#         url = self.video_urls[index]
#         self.video_player.load(QUrl(url))

#     def handle_timestamp_result(self, timestamp):
#         cursor = self.notes.textCursor()
#         cursor.insertText('\n'+timestamp + ": ")

#     def insert_timestamp(self):
#         js = """
#             (function() {
#                 var player = document.querySelector('video');
#                 if (player) {
#                     var time = Math.floor(player.currentTime);
#                     var minutes = Math.floor(time / 60);
#                     var seconds = time % 60;
#                     return "[" + minutes.toString().padStart(2, '0') + ":" + seconds.toString().padStart(2, '0') + "]";
#                 }
#                 return "[00:00]";
#             })();
#         """
#         self.video_player.page().runJavaScript(js, self.handle_timestamp_result)


#     def save_note(self):
#         note = self.notes.toPlainText().strip()
#         if not note:
#             QMessageBox.warning(self, "Empty Note", "Cannot save empty note.")
#             return
#         filename, _ = QFileDialog.getSaveFileName(self, "Save Note", "notes/note.txt", "Text Files (*.txt)")
#         if filename:
#             with open(filename, "w", encoding="utf-8") as f:
#                 f.write(note)
#             QMessageBox.information(self, "Saved", f"Note saved to:\n{filename}")

# if __name__ == '__main__':
#     app = QApplication(sys.argv)
#     window = YouTubeNotesApp()
#     window.show()
#     sys.exit(app.exec_())


# version 2
# not worked??

# 


# import sys
# import os
# import sqlite3
# from PyQt5.QtWidgets import (
#     QApplication, QWidget, QVBoxLayout, QHBoxLayout,
#     QLineEdit, QPushButton, QListWidget, QTextEdit, QFileDialog, QMessageBox
# )
# from PyQt5.QtWebEngineWidgets import QWebEngineView
# from PyQt5.QtCore import QUrl
# from pytube import Playlist, YouTube
# import datetime

# # Setup
# os.makedirs("notes", exist_ok=True)
# DB_PATH = "playlist.db"

# # Initialize DB
# conn = sqlite3.connect(DB_PATH)
# c = conn.cursor()
# c.execute("""
#     CREATE TABLE IF NOT EXISTS playlist (
#         id INTEGER PRIMARY KEY AUTOINCREMENT,
#         playlist_url TEXT,
#         video_url TEXT,
#         title TEXT
#     )
# """)
# conn.commit()

# class YouTubeNotesApp(QWidget):
#     def __init__(self):
#         super().__init__()
#         self.setWindowTitle("\U0001F4D8 YouTube Playlist Notes App")
#         self.setMinimumSize(1000, 700)

#         self.video_data = []  # (title, url)

#         self.layout = QVBoxLayout()
#         self.setLayout(self.layout)

#         self.url_input = QLineEdit()
#         self.url_input.setPlaceholderText("Paste YouTube playlist URL here")
#         self.layout.addWidget(self.url_input)

#         self.fetch_btn = QPushButton("Fetch Videos")
#         self.fetch_btn.clicked.connect(self.fetch_videos)
#         self.layout.addWidget(self.fetch_btn)

#         self.split_layout = QHBoxLayout()
#         self.layout.addLayout(self.split_layout)

#         self.video_list = QListWidget()
#         self.video_list.itemClicked.connect(self.play_selected_video)
#         self.split_layout.addWidget(self.video_list, 25)

#         self.right_panel = QVBoxLayout()
#         self.split_layout.addLayout(self.right_panel, 75)

#         self.video_player = QWebEngineView()
#         self.right_panel.addWidget(self.video_player, 65)

#         self.notes = QTextEdit()
#         self.notes.setPlaceholderText("Take your notes here...")
#         self.right_panel.addWidget(self.notes, 30)

#         self.buttons = QHBoxLayout()
#         self.right_panel.addLayout(self.buttons)

#         self.timestamp_btn = QPushButton("\u23F1 Insert Timestamp")
#         self.timestamp_btn.clicked.connect(self.insert_timestamp)
#         self.buttons.addWidget(self.timestamp_btn)

#         self.save_btn = QPushButton("\U0001F4BE Save Note")
#         self.save_btn.clicked.connect(self.save_note)
#         self.buttons.addWidget(self.save_btn)

#     def fetch_videos(self):
#         url = self.url_input.text().strip()
#         if not url:
#             QMessageBox.warning(self, "Error", "Please enter a playlist URL")
#             return
#         try:
#             playlist = Playlist(url)
#             self.video_data.clear()
#             self.video_list.clear()
#             for video_url in playlist.video_urls:
#                 yt = YouTube(video_url)
#                 title = yt.title
#                 self.video_data.append((title, video_url))
#                 self.video_list.addItem(title)
#                 # Save to DB
#                 c.execute("INSERT INTO playlist (playlist_url, video_url, title) VALUES (?, ?, ?)",
#                           (url, video_url, title))
#             conn.commit()
#             QMessageBox.information(self, "Success", f"Fetched {len(self.video_data)} videos.")
#         except Exception as e:
#             QMessageBox.critical(self, "Error", f"Failed to fetch playlist:\n{e}")

#     def play_selected_video(self, item):
#         title = item.text()
#         url = None
#         for t, u in self.video_data:
#             if t == title:
#                 url = u
#                 break
#         if url:
#             embed_url = url.replace("watch?v=", "embed/").split("&")[0]
#             self.video_player.load(QUrl(embed_url))

#     def insert_timestamp(self):
#         # Placeholder logic — needs JS eval to fetch actual video time
#         cursor = self.notes.textCursor()
#         cursor.insertText("\n[00:00] ")

#     def save_note(self):
#         note = self.notes.toPlainText().strip()
#         if not note:
#             QMessageBox.warning(self, "Empty Note", "Cannot save empty note.")
#             return
#         filename, _ = QFileDialog.getSaveFileName(self, "Save Note", "notes/note.txt", "Text Files (*.txt)")
#         if filename:
#             with open(filename, "w", encoding="utf-8") as f:
#                 f.write(note)
#             QMessageBox.information(self, "Saved", f"Note saved to:\n{filename}")

# if __name__ == '__main__':
    # app = QApplication(sys.argv)
    # window = YouTubeNotesApp()
    # window.show()
    # sys.exit(app.exec_())

#######################################################################################

# # version 3

# import sys
# import os
# import sqlite3
# from PyQt5.QtWidgets import (
#     QApplication, QWidget, QVBoxLayout, QHBoxLayout,
#     QLineEdit, QPushButton, QListWidget, QTextEdit, QFileDialog, QMessageBox
# )
# from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings
# from PyQt5.QtWebEngineWidgets import QWebEngineView
# from PyQt5.QtCore import QUrl
# import yt_dlp

# # Setup
# os.makedirs("notes", exist_ok=True)
# DB_PATH = "playlist.db"

# # Initialize DB
# conn = sqlite3.connect(DB_PATH)
# c = conn.cursor()
# c.execute("""
#     CREATE TABLE IF NOT EXISTS playlist (
#         id INTEGER PRIMARY KEY AUTOINCREMENT,
#         playlist_url TEXT,
#         video_url TEXT,
#         title TEXT
#     )
# """)
# conn.commit()

# class YouTubeNotesApp(QWidget):
#     def __init__(self):
#         super().__init__()  # Call the superclass constructor first
#         self.setWindowTitle("\U0001F4D8 YouTube Playlist Notes App")
#         self.setMinimumSize(1000, 700)

#         # Initialize video player
#         self.video_player = QWebEngineView()
#         settings = self.video_player.settings()
#         settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
#         settings.setAttribute(QWebEngineSettings.PluginsEnabled, True)
#         settings.setAttribute(QWebEngineSettings.FullScreenSupportEnabled, True)
#         settings.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)

#         self.video_data = []  # (title, url)

#         self.layout = QVBoxLayout()
#         self.setLayout(self.layout)

#         self.url_input = QLineEdit()
#         self.url_input.setPlaceholderText("Paste YouTube playlist URL here")
#         self.layout.addWidget(self.url_input)

#         self.fetch_btn = QPushButton("Fetch Videos")
#         self.fetch_btn.clicked.connect(self.fetch_videos)
#         self.layout.addWidget(self.fetch_btn)

#         self.split_layout = QHBoxLayout()
#         self.layout.addLayout(self.split_layout)

#         self.video_list = QListWidget()
#         self.video_list.itemClicked.connect(self.play_selected_video)
#         self.split_layout.addWidget(self.video_list, 25)

#         self.right_panel = QVBoxLayout()
#         self.split_layout.addLayout(self.right_panel, 75)

#         self.right_panel.addWidget(self.video_player, 65)

#         self.notes = QTextEdit()
#         self.notes.setPlaceholderText("Take your notes here...")
#         self.right_panel.addWidget(self.notes, 30)

#         self.buttons = QHBoxLayout()
#         self.right_panel.addLayout(self.buttons)

#         self.timestamp_btn = QPushButton("\u23F1 Insert Timestamp")
#         self.timestamp_btn.clicked.connect(self.insert_timestamp)
#         self.buttons.addWidget(self.timestamp_btn)

#         self.save_btn = QPushButton("\U0001F4BE Save Note")
#         self.save_btn.clicked.connect(self.save_note)
#         self.buttons.addWidget(self.save_btn)

#     def fetch_videos(self):
#         url = self.url_input.text().strip()
#         if not url:
#             QMessageBox.warning(self, "Error", "Please enter a playlist URL")
#             return
#         try:
#             ydl_opts = {
#                 'quiet': True,
#                 'extract_flat': True,
#                 'dump_single_json': True
#             }
#             with yt_dlp.YoutubeDL(ydl_opts) as ydl:
#                 info = ydl.extract_info(url, download=False)
#                 self.video_data.clear()
#                 self.video_list.clear()
#                 for entry in info['entries']:
#                     title = entry['title']
#                     video_url = f"https://www.youtube.com/watch?v={entry['id']}"
#                     self.video_data.append((title, video_url))
#                     self.video_list.addItem(title)
#                     # Save to DB
#                     c.execute("INSERT INTO playlist (playlist_url, video_url, title) VALUES (?, ?, ?)",
#                               (url, video_url, title))
#                 conn.commit()
#             QMessageBox.information(self, "Success", f"Fetched {len(self.video_data)} videos.")
#         except Exception as e:
#             QMessageBox.critical(self, "Error", f"Failed to fetch playlist:\n{e}")

#     def play_selected_video(self, item):
#         title = item.text()
#         url = None
#         for t, u in self.video_data:
#             if t == title:
#                 url = u
#                 break
#         if url:
#             self.video_player.load(QUrl(url))

#     def handle_timestamp_result(self, timestamp):
#         cursor = self.notes.textCursor()
#         cursor.insertText('\n'+timestamp + ": ")

#     def insert_timestamp(self):
#         js = """
#             (function() {
#                 var player = document.querySelector('video');
#                 if (player) {
#                     var time = Math.floor(player.currentTime);
#                     var minutes = Math.floor(time / 60);
#                     var seconds = time % 60;
#                     return "[" + minutes.toString().padStart(2, '0') + ":" + seconds.toString().padStart(2, '0') + "]";
#                 }
#                 return "[00:00]";
#             })();
#         """
#         self.video_player.page().runJavaScript(js, self.handle_timestamp_result)

#     def save_note(self):
#         note = self.notes.toPlainText().strip()
#         if not note:
#             QMessageBox.warning(self, "Empty Note", "Cannot save empty note.")
#             return
#         filename, _ = QFileDialog.getSaveFileName(self, "Save Note", "notes/note.txt", "Text Files (*.txt)")
#         if filename:
#             with open(filename, "w", encoding="utf-8") as f:
#                 f.write(note)
#             QMessageBox.information(self, "Saved", f"Note saved to:\n{filename}")

# if __name__ == '__main__':
#     app = QApplication(sys.argv)
#     window = YouTubeNotesApp()
#     window.show()
#     sys.exit(app.exec_())


#here we replace link by its title 

#########################################################################################################

#version 4

# import sys
# import os
# import sqlite3
# from PyQt5.QtWidgets import (
#     QApplication, QWidget, QVBoxLayout, QHBoxLayout,
#     QLineEdit, QPushButton, QListWidget, QTextEdit, QFileDialog, QMessageBox
# )
# from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings
# from PyQt5.QtCore import QUrl, QTimer
# import yt_dlp
# from datetime import datetime
# import re
# # Setup
# os.makedirs("notes", exist_ok=True)
# DB_PATH = "playlist.db"

# # Initialize DB
# conn = sqlite3.connect(DB_PATH)
# c = conn.cursor()
# c.execute("""
#     CREATE TABLE IF NOT EXISTS playlist (
#         id INTEGER PRIMARY KEY AUTOINCREMENT,
#         playlist_url TEXT,
#         video_url TEXT,
#         title TEXT,
#         played_time TEXT,
#         last_video_timestamp TEXT
#     )
# """)
# conn.commit()


# class YouTubeNotesApp(QWidget):
#     def __init__(self):
        
#         super().__init__()
#         self.setWindowTitle("📘 YouTube Playlist Notes App")
#         self.setMinimumSize(1000, 700)
#         self.current_video_title = None
#         self.current_video_url = None
#         self.video_data = []

#         # Video Player
#         self.video_player = QWebEngineView()
#         settings = self.video_player.settings()
#         settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
#         settings.setAttribute(QWebEngineSettings.PluginsEnabled, True)
#         settings.setAttribute(QWebEngineSettings.FullScreenSupportEnabled, True)
#         settings.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)

#         self.layout = QVBoxLayout(self)
#         self.url_input = QLineEdit()
#         self.url_input.setPlaceholderText("Paste YouTube playlist URL here")
#         self.layout.addWidget(self.url_input)

#         self.fetch_btn = QPushButton("Fetch Videos")
#         self.fetch_btn.clicked.connect(self.fetch_videos)
#         self.layout.addWidget(self.fetch_btn)

#         self.split_layout = QHBoxLayout()
#         self.layout.addLayout(self.split_layout)

#         self.video_list = QListWidget()
#         self.video_list.itemClicked.connect(self.play_selected_video)
#         self.split_layout.addWidget(self.video_list, 25)

#         self.right_panel = QVBoxLayout()
#         self.split_layout.addLayout(self.right_panel, 75)

#         self.right_panel.addWidget(self.video_player, 65)

#         self.notes = QTextEdit()
#         self.notes.setPlaceholderText("Take your notes here...")
#         self.right_panel.addWidget(self.notes, 30)

#         # Add Playlist Button
#         self.add_playlist_btn = QPushButton("➕ Add Playlist to DB")
#         self.add_playlist_btn.setEnabled(False)
#         self.add_playlist_btn.clicked.connect(self.save_playlist_to_db)
#         self.right_panel.addWidget(self.add_playlist_btn)

        

#         self.buttons = QHBoxLayout()
#         self.right_panel.addLayout(self.buttons)

#         self.timestamp_btn = QPushButton("⏱ Insert Timestamp")
#         self.timestamp_btn.clicked.connect(self.insert_timestamp)
#         self.buttons.addWidget(self.timestamp_btn)

#         self.save_btn = QPushButton("💾 Save Note")
#         self.save_btn.clicked.connect(self.save_note)
#         self.buttons.addWidget(self.save_btn)

#         self.add_playlist_btn.setEnabled(False)
#         self.timestamp_btn.setEnabled(False)
#         self.save_btn.setEnabled(False)

#     # def fetch_videos(self):
#     #     url = self.url_input.text().strip()
#     #     if not url:
#     #         QMessageBox.warning(self, "Error", "Please enter a playlist URL")
#     #         return
#     #     try:
#     #         ydl_opts = {
#     #             'quiet': True,
#     #             'extract_flat': True,
#     #             'dump_single_json': True
#     #         }
#     #         with yt_dlp.YoutubeDL(ydl_opts) as ydl:
#     #             info = ydl.extract_info(url, download=False)
#     #             self.video_data.clear()
#     #             self.video_list.clear()
#     #             for entry in info['entries']:
#     #                 title = entry['title']
#     #                 video_url = f"https://www.youtube.com/watch?v={entry['id']}"
#     #                 self.video_data.append((title, video_url))
#     #                 self.video_list.addItem(title)
#     #         self.add_playlist_btn.setEnabled(True)
#     #         QMessageBox.information(self, "Fetched", f"Fetched {len(self.video_data)} videos.")
#     #     except Exception as e:
#     #         QMessageBox.critical(self, "Error", f"Failed to fetch playlist:\n{e}")


#     def fetch_videos(self):
#         url = self.url_input.text().strip()
#         if not url:
#             QMessageBox.warning(self, "Error", "Please enter a playlist URL")
#             return
#         try:
#             ydl_opts = {
#                 'quiet': True,
#                 'extract_flat': True,
#                 'dump_single_json': True
#             }
#             with yt_dlp.YoutubeDL(ydl_opts) as ydl:
#                 info = ydl.extract_info(url, download=False)
#                 self.video_data.clear()
#                 self.video_list.clear()
#                 for entry in info['entries']:
#                     title = entry['title']
#                     video_url = f"https://www.youtube.com/watch?v={entry['id']}"
#                     self.video_data.append((title, video_url))
#                     self.video_list.addItem(title)
#             self.add_playlist_btn.setEnabled(True)
#             self.timestamp_btn.setEnabled(False)
#             self.save_btn.setEnabled(False)
#             QMessageBox.information(self, "Fetched", f"Fetched {len(self.video_data)} videos.")
#         except Exception as e:
#             QMessageBox.critical(self, "Error", f"Failed to fetch playlist:\n{e}")

#     def save_playlist_to_db(self):
#         url = self.url_input.text().strip()
#         for title, video_url in self.video_data:
#             c.execute("SELECT COUNT(*) FROM playlist WHERE video_url = ?", (video_url,))
#             if c.fetchone()[0] == 0:
#                 c.execute("""
#                     INSERT INTO playlist (playlist_url, video_url, title, played_time, last_video_timestamp)
#                     VALUES (?, ?, ?, ?, ?)
#                 """, (url, video_url, title, None, None))
#         conn.commit()
#         self.add_playlist_btn.setEnabled(False)
#         self.timestamp_btn.setEnabled(True)
#         self.save_btn.setEnabled(True)
#         QMessageBox.information(self, "Saved", "Playlist saved to database. All features unlocked.")

#     def play_selected_video(self, item):
#         self.save_note_and_timestamp_on_switch()
#         title = item.text()
#         url = None
#         for t, u in self.video_data:
#             if t == title:
#                 url = u
#                 break
#         if url:
#             self.video_player.load(QUrl(url))
#             self.current_video_title = title
#             self.current_video_url = url

#             # def try_resume():
#             #     c.execute("SELECT last_video_timestamp FROM playlist WHERE title = ?", (title,))
#             #     result = c.fetchone()
#             #     if result and result[0]:
#             #         seconds = int(float(result[0]))
#             #         mins, secs = divmod(seconds, 60)
#             #         resume_text = f"{mins:02}:{secs:02}"
#             #         confirm = QMessageBox.question(self, "Resume Playback", f"Resume from {resume_text}?",
#             #                                        QMessageBox.Yes | QMessageBox.No)
#             #         if confirm == QMessageBox.Yes:
#             #             js = f"document.querySelector('video').currentTime = {seconds};"
#             #             self.video_player.page().runJavaScript(js)

#             QTimer.singleShot(2000, lambda: self.try_resume(title))

#     def try_resume(self, title):
#         c.execute("SELECT last_video_timestamp FROM playlist WHERE title = ?", (title,))
#         row = c.fetchone()
#         if row and row[0]:
#             timestamp = row[0].strip()
#             resume = QMessageBox.question(self, "Resume?",
#                         f"Resume '{title}' at [{timestamp}]?",
#                         QMessageBox.Yes | QMessageBox.No)
#             if resume == QMessageBox.Yes:
#                 # Try converting [mm:ss] → seconds safely
#                 import re
#                 match = re.match(r"\[(\d+):(\d+)\]", timestamp)
#                 if match:
#                     minutes = int(match.group(1))
#                     seconds = int(match.group(2))

#                     # Validate minutes and seconds
#                     if minutes < 0 or seconds < 0 or seconds >= 60:
#                         QMessageBox.warning(self, "Invalid Timestamp", f"Invalid timestamp format: {timestamp}. Seconds must be between 0 and 59.")
#                         return

#                     total_seconds = minutes * 60 + seconds
#                     js = f"""
#                         var video = document.querySelector('video');
#                         if (video) {{
#                             video.currentTime = {total_seconds};
#                         }}
#                     """
#                     self.video_player.page().runJavaScript(js)
#                 else:
#                     QMessageBox.warning(self, "Invalid Timestamp", f"Invalid timestamp format: {timestamp}")


#     def save_note_and_timestamp_on_switch(self):
#         note = self.notes.toPlainText().strip()
#         if self.current_video_title:
#             if note:
#                 confirm = QMessageBox.question(self, "Save Note", f"Save note for '{self.current_video_title}'?",
#                                                QMessageBox.Yes | QMessageBox.No)
#                 if confirm == QMessageBox.Yes:
#                     safe_title = re.sub(r'[\\/*?:"<>|]', "", self.current_video_title)
#                     filename = f"notes/{safe_title}.txt"
#                     with open(filename, "w", encoding="utf-8") as f:
#                         f.write(note)

#                     QMessageBox.information(self, "Saved", f"Note saved to:\n{filename}")
#             else:
#                 confirm = QMessageBox.question(self, "No Note Taken",
#                                                f"No note for '{self.current_video_title}'. Switch anyway?",
#                                                QMessageBox.Yes | QMessageBox.No)
#                 if confirm == QMessageBox.No:
#                     return

#             # Save current timestamp to DB
#             js = "document.querySelector('video')?.currentTime || 0;"
#             def store_time(sec):
#                 now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#                 try:
#                     c.execute("UPDATE playlist SET last_video_timestamp = ?, played_time = ? WHERE title = ?",
#                               (str(sec), now, self.current_video_title))
#                     conn.commit()
#                 except Exception as e:
#                     print("DB Update Error:", e)

#             self.video_player.page().runJavaScript(js, store_time)

#     def insert_timestamp(self):
#         # Update last played timestamp for the current video
#         js = """
#             (function() {
#                 var player = document.querySelector('video');
#                 if (player) {
#                     var time = Math.floor(player.currentTime);
#                     var minutes = Math.floor(time / 60);
#                     var seconds = time % 60;
#                     return minutes.toString().padStart(2, '0') + ":" + seconds.toString().padStart(2, '0');
#                 }
#                 return "00:00";
#             })();
#         """

#         def update_timestamp_in_db(timestamp):
#             c.execute("UPDATE playlist SET last_video_timestamp = ? WHERE title = ?", (timestamp, self.current_video_title))
#             conn.commit()

#         self.video_player.page().runJavaScript(js, update_timestamp_in_db)


#     def handle_timestamp_result(self, timestamp):
#         cursor = self.notes.textCursor()
#         cursor.insertText('\n' + timestamp + ": ")

#     def save_note(self):
#         note = self.notes.toPlainText().strip()
#         if not note:
#             QMessageBox.warning(self, "Empty Note", "Cannot save empty note.")
#             return
#         filename, _ = QFileDialog.getSaveFileName(self, "Save Note", "notes/note.txt", "Text Files (*.txt)")
#         if filename:
#             with open(filename, "w", encoding="utf-8") as f:
#                 f.write(note)
#             QMessageBox.information(self, "Saved", f"Note saved to:\n{filename}")


# if __name__ == '__main__':

#     app = QApplication(sys.argv)
#     window = YouTubeNotesApp()
#     window.show()

#     sys.exit(app.exec_())


# not worked error in time stamp

######################################################################


# version 5


# import sys
# import os
# import sqlite3
# from PyQt5.QtWidgets import (
#     QApplication, QWidget, QVBoxLayout, QHBoxLayout,
#     QLineEdit, QPushButton, QListWidget, QTextEdit, QFileDialog, QMessageBox
# )
# from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings
# from PyQt5.QtCore import QUrl, QTimer
# import yt_dlp
# from datetime import datetime
# import re

# # Setup
# os.makedirs("notes", exist_ok=True)
# DB_PATH = "playlist.db"

# # Initialize DB
# conn = sqlite3.connect(DB_PATH)
# c = conn.cursor()
# c.execute("""
#     CREATE TABLE IF NOT EXISTS playlist (
#     playlist_url TEXT PRIMARY KEY,  -- Use playlist_url as the primary key
#     video_url TEXT UNIQUE,           -- Ensures each video URL is unique
#     title TEXT,
#     played_time TEXT,
#     last_video_timestamp TEXT
#     )
# """)
# conn.commit()

# class YouTubeNotesApp(QWidget):
#     def __init__(self):
#         super().__init__()
#         self.setWindowTitle("📘 YouTube Playlist Notes App")
#         self.setMinimumSize(1000, 700)
#         self.current_video_title = None
#         self.current_video_url = None
#         self.video_data = []

#         # Video Player
#         self.video_player = QWebEngineView()
#         settings = self.video_player.settings()
#         settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
#         settings.setAttribute(QWebEngineSettings.PluginsEnabled, True)
#         settings.setAttribute(QWebEngineSettings.FullScreenSupportEnabled, True)
#         settings.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)

#         self.layout = QVBoxLayout(self)
#         self.url_input = QLineEdit()
#         self.url_input.setPlaceholderText("Paste YouTube playlist URL here")
#         self.layout.addWidget(self.url_input)

#         self.fetch_btn = QPushButton("Fetch Videos")
#         self.fetch_btn.clicked.connect(self.fetch_videos)
#         self.layout.addWidget(self.fetch_btn)

#         self.split_layout = QHBoxLayout()
#         self.layout.addLayout(self.split_layout)

#         self.video_list = QListWidget()
#         self.video_list.itemClicked.connect(self.play_selected_video)
#         self.split_layout.addWidget(self.video_list, 25)

#         self.right_panel = QVBoxLayout()
#         self.split_layout.addLayout(self.right_panel, 75)

#         self.right_panel.addWidget(self.video_player, 65)

#         self.notes = QTextEdit()
#         self.notes.setPlaceholderText("Take your notes here...")
#         self.right_panel.addWidget(self.notes, 30)

#         # Add Playlist Button
#         self.add_playlist_btn = QPushButton("➕ Add Playlist to DB")
#         self.add_playlist_btn.setEnabled(False)
#         self.add_playlist_btn.clicked.connect(self.save_playlist_to_db)
#         self.right_panel.addWidget(self.add_playlist_btn)

#         self.buttons = QHBoxLayout()
#         self.right_panel.addLayout(self.buttons)

#         self.timestamp_btn = QPushButton("⏱ Insert Timestamp")
#         self.timestamp_btn.clicked.connect(self.insert_timestamp)
#         self.buttons.addWidget(self.timestamp_btn)

#         self.save_btn = QPushButton("💾 Save Note")
#         self.save_btn.clicked.connect(self.save_note)
#         self.buttons.addWidget(self.save_btn)

#         self.timestamp_btn.setEnabled(False)
#         self.save_btn.setEnabled(False)

#     def fetch_videos(self):
#         url = self.url_input.text().strip()
#         if not url:
#             QMessageBox.warning(self, "Error", "Please enter a playlist URL")
#             return
#         try:
#             ydl_opts = {
#                 'quiet': True,
#                 'extract_flat': True,
#                 'dump_single_json': True
#             }
#             with yt_dlp.YoutubeDL(ydl_opts) as ydl:
#                 info = ydl.extract_info(url, download=False)
#                 self.video_data.clear()
#                 self.video_list.clear()
#                 for entry in info['entries']:
#                     title = entry['title']
#                     video_url = f"https://www.youtube.com/watch?v={entry['id']}"
#                     self.video_data.append((title, video_url))
#                     self.video_list.addItem(title)
#             self.add_playlist_btn.setEnabled(True)
#             self.timestamp_btn.setEnabled(False)
#             self.save_btn.setEnabled(False)
#             QMessageBox.information(self, "Fetched", f"Fetched {len(self.video_data)} videos.")
#         except Exception as e:
#             QMessageBox.critical(self, "Error", f"Failed to fetch playlist:\n{e}")

#     def save_playlist_to_db(self):
#         url = self.url_input.text().strip()
#         for title, video_url in self.video_data:
#             c.execute("SELECT COUNT(*) FROM playlist WHERE video_url = ?", (video_url,))
#             if c.fetchone()[0] == 0:
#                 c.execute("""
#                     INSERT INTO playlist (playlist_url, video_url, title, played_time, last_video_timestamp)
#                     VALUES (?, ?, ?, ?, ?)
#                 """, (url, video_url, title, None, None))
#         conn.commit()
#         self.add_playlist_btn.setEnabled(False)
#         self.timestamp_btn.setEnabled(True)
#         self.save_btn.setEnabled(True)
#         QMessageBox.information(self, "Saved", "Playlist saved to database. All features unlocked.")

#     def play_selected_video(self, item):
#         self.save_note_and_timestamp_on_switch()
#         title = item.text()
#         url = None
#         for t, u in self.video_data:
#             if t == title:
#                 url = u
#                 break
#         if url:
#             self.video_player.load(QUrl(url))
#             self.current_video_title = title
#             self.current_video_url = url
#             QTimer.singleShot(2000, lambda: self.try_resume(title))

#     def try_resume(self, title):
#         c.execute("SELECT last_video_timestamp FROM playlist WHERE title = ?", (title,))
#         row = c.fetchone()
#         if row and row[0]:
#             timestamp = row[0].strip()
#             if self.is_valid_timestamp(timestamp):
#                 resume = QMessageBox.question(self, "Resume?",
#                         f"Resume '{title}' at [{timestamp}]?",
#                         QMessageBox.Yes | QMessageBox.No)
#                 if resume == QMessageBox.Yes:
#                     minutes, seconds = map(int, timestamp[1:-1].split(':'))
#                     total_seconds = minutes * 60 + seconds
#                     js = f"""
#                         var video = document.querySelector('video');
#                         if (video) {{
#                             video.currentTime = {total_seconds};
#                         }}
#                     """
#                     self.video_player.page().runJavaScript(js)
#             else:
#                 QMessageBox.warning(self, "Invalid Timestamp", f"Invalid timestamp format: {timestamp}")

#     def is_valid_timestamp(self, timestamp):
#         """Check if the timestamp is in the format [mm:ss] and valid."""
#         match = re.match(r"\[(\d+):(\d+)\]", timestamp)
#         if match:
#             minutes = int(match.group(1))
#             seconds = int(match.group(2))
#             return minutes >= 0 and 0 <= seconds < 60
#         return False

#     def save_note_and_timestamp_on_switch(self):
#         note = self.notes.toPlainText().strip()
#         if self.current_video_title:
#             if note:
#                 confirm = QMessageBox.question(self, "Save Note", f"Save note for '{self.current_video_title}'?",
#                                                QMessageBox.Yes | QMessageBox.No)
#                 if confirm == QMessageBox.Yes:
#                     safe_title = re.sub(r'[\\/*?:"<>|]', "", self.current_video_title)
#                     filename = f"notes/{safe_title}.txt"
#                     with open(filename, "w", encoding="utf-8") as f:
#                         f.write(note)
#                     QMessageBox.information(self, "Saved", f"Note saved to:\n{filename}")
#             else:
#                 confirm = QMessageBox.question(self, "No Note Taken",
#                                                f"No note for '{self.current_video_title}'. Switch anyway?",
#                                                QMessageBox.Yes | QMessageBox.No)
#                 if confirm == QMessageBox.No:
#                     return

#             # Save current timestamp to DB
#             js = "document.querySelector('video')?.currentTime || 0;"
#             def store_time(sec):
#                 now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#                 try:
#                     timestamp_str = f"[{int(sec // 60):02}:{int(sec % 60):02}]"
#                     c.execute("UPDATE playlist SET last_video_timestamp = ?, played_time = ? WHERE title = ?",
#                               (timestamp_str, now, self.current_video_title))
#                     conn.commit()
#                 except Exception as e:
#                     print("DB Update Error:", e)

#             self.video_player.page().runJavaScript(js, store_time)

#     def insert_timestamp(self):
#         # Update last played timestamp for the current video
#         js = """
#             (function() {
#                 var player = document.querySelector('video');
#                 if (player) {
#                     var time = Math.floor(player.currentTime);
#                     var minutes = Math.floor(time / 60);
#                     var seconds = time % 60;
#                     return "[" + minutes.toString().padStart(2, '0') + ":" + seconds.toString().padStart(2, '0') + "]";
#                 }
#                 return "[00:00]";
#             })();
#         """

#         def update_timestamp_in_db(timestamp):
#             c.execute("UPDATE playlist SET last_video_timestamp = ? WHERE title = ?", (timestamp, self.current_video_title))
#             conn.commit()

#         self.video_player.page().runJavaScript(js, update_timestamp_in_db)

#     def save_note(self):
#         note = self.notes.toPlainText().strip()
#         if not note:
#             QMessageBox.warning(self, "Empty Note", "Cannot save empty note.")
#             return
#         filename, _ = QFileDialog.getSaveFileName(self, "Save Note", "notes/note.txt", "Text Files (*.txt)")
#         if filename:
#             with open(filename, "w", encoding="utf-8") as f:
#                 f.write(note)
#             QMessageBox.information(self, "Saved", f"Note saved to:\n{filename}")

# if __name__ == '__main__':
#     app = QApplication(sys.argv)
#     window = YouTubeNotesApp()
#     window.show()
#     sys.exit(app.exec_())


# time stamp fixed but problem with linking database

##############################################################################################

# version 6

# import sys
# import os
# import sqlite3
# import re
# import yt_dlp
# from PyQt5.QtWidgets import (
#     QApplication, QWidget, QVBoxLayout, QHBoxLayout,
#     QLineEdit, QPushButton, QListWidget, QTextEdit, QFileDialog, QMessageBox
# )
# from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings
# from PyQt5.QtCore import QUrl

# # Setup
# os.makedirs("notes", exist_ok=True)
# DB_PATH = "playlist.db"

# # Initialize DB
# conn = sqlite3.connect(DB_PATH)
# c = conn.cursor()

# class YouTubeNotesApp(QWidget):
#     def __init__(self):
#         super().__init__()
#         self.setWindowTitle("📘 YouTube Playlist Notes App")
#         self.setMinimumSize(1000, 700)
#         self.current_video_title = None
#         self.current_video_url = None
#         self.current_video_id = None
#         self.current_playlist_id = None
#         self.video_data = []  # List of (youtube_id, video_url, title)

#         # Video Player
#         self.video_player = QWebEngineView()
#         settings = self.video_player.settings()
#         settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
#         settings.setAttribute(QWebEngineSettings.PluginsEnabled, True)
#         settings.setAttribute(QWebEngineSettings.FullScreenSupportEnabled, True)
#         settings.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)

#         # Create UI
#         self.layout = QVBoxLayout(self)

#         # Playlist URL Input
#         self.url_input = QLineEdit()
#         self.url_input.setPlaceholderText("Paste YouTube playlist URL here")
#         self.layout.addWidget(self.url_input)

#         # Fetch Button
#         self.fetch_btn = QPushButton("Fetch Videos")
#         self.fetch_btn.clicked.connect(self.fetch_videos)
#         self.layout.addWidget(self.fetch_btn)

#         # Main Content Area
#         self.split_layout = QHBoxLayout()
#         self.layout.addLayout(self.split_layout)

#         # Video List
#         self.video_list = QListWidget()
#         self.video_list.itemClicked.connect(self.play_selected_video)
#         self.split_layout.addWidget(self.video_list, 30)

#         # Right Panel
#         self.right_panel = QVBoxLayout()
#         self.split_layout.addLayout(self.right_panel, 70)

#         # Video Player
#         self.right_panel.addWidget(self.video_player, 60)

#         # Notes Area
#         self.notes = QTextEdit()
#         self.notes.setPlaceholderText("Take your notes here...")
#         self.right_panel.addWidget(self.notes, 30)

#         # Buttons
#         self.buttons = QHBoxLayout()
#         self.right_panel.addLayout(self.buttons)

#         self.add_playlist_btn = QPushButton("➕ Add Playlist to DB")
#         self.add_playlist_btn.setEnabled(False)
#         self.add_playlist_btn.clicked.connect(self.save_playlist_to_db)
#         self.buttons.addWidget(self.add_playlist_btn)

#         self.timestamp_btn = QPushButton("⏱ Insert Timestamp")
#         self.timestamp_btn.clicked.connect(self.insert_timestamp)
#         self.buttons.addWidget(self.timestamp_btn)

#         self.save_btn = QPushButton("💾 Save Note")
#         self.save_btn.clicked.connect(self.save_note)
#         self.buttons.addWidget(self.save_btn)

#         self.timestamp_btn.setEnabled(False)
#         self.save_btn.setEnabled(False)

#     def fetch_videos(self):
#         url = self.url_input.text().strip()
#         if not url:
#             QMessageBox.warning(self, "Error", "Please enter a playlist URL")
#             return

#         try:
#             ydl_opts = {
#                 'quiet': True,
#                 'extract_flat': True,
#                 'dump_single_json': True
#             }
#             with yt_dlp.YoutubeDL(ydl_opts) as ydl:
#                 info = ydl.extract_info(url, download=False)
#                 self.video_data.clear()
#                 self.video_list.clear()

#                 for entry in info['entries']:
#                     title = entry['title']
#                     video_url = f"https://www.youtube.com/watch?v={entry['id']}"
#                     youtube_id = entry['id']
#                     self.video_data.append((youtube_id, video_url, title))
#                     self.video_list.addItem(title)

#             c.execute("SELECT id FROM playlists WHERE playlist_url = ?", (url,))
#             result = c.fetchone()

#             if result:
#                 self.current_playlist_id = result[0]
#                 self.add_playlist_btn.setEnabled(False)
#                 self.timestamp_btn.setEnabled(True)
#                 self.save_btn.setEnabled(True)
#                 QMessageBox.information(self, "Info", "Existing playlist loaded from database")
#             else:
#                 self.add_playlist_btn.setEnabled(True)
#                 QMessageBox.information(self, "Success", f"Fetched {len(self.video_data)} videos. Click 'Add Playlist' to save.")

#         except Exception as e:
#             QMessageBox.critical(self, "Error", f"Failed to fetch playlist:\n{str(e)}")

#     def save_playlist_to_db(self):
#         url = self.url_input.text().strip()
#         try:
#             c.execute("INSERT INTO playlists (playlist_url) VALUES (?)", (url,))
#             self.current_playlist_id = c.lastrowid

#             for position, (youtube_id, video_url, title) in enumerate(self.video_data, start=1):
#                 c.execute("""
#                     INSERT OR IGNORE INTO videos (youtube_id, video_url, title) 
#                     VALUES (?, ?, ?)
#                 """, (youtube_id, video_url, title))

#                 c.execute("SELECT id FROM videos WHERE youtube_id = ?", (youtube_id,))
#                 video_id = c.fetchone()[0]

#                 c.execute("""
#                     INSERT INTO playlist_videos (playlist_id, video_id, position) 
#                     VALUES (?, ?, ?)
#                 """, (self.current_playlist_id, video_id, position))

#             conn.commit()
#             self.add_playlist_btn.setEnabled(False)
#             self.timestamp_btn.setEnabled(True)
#             self.save_btn.setEnabled(True)
#             QMessageBox.information(self, "Success", "Playlist saved to database")

#         except Exception as e:
#             QMessageBox.critical(self, "Error", f"Failed to save playlist:\n{str(e)}")

#         def play_selected_video(self, item):
#             new_title = item.text()
#             new_video_id = None
#             new_video_url = None

#             for youtube_id, video_url, title in self.video_data:
#                 if title == new_title:
#                     new_video_id = youtube_id
#                     new_video_url = video_url
#                     break

#             # Save the current video's timestamp before switching
#             if self.current_video_id and self.current_video_id != new_video_id:
#                 self.save_current_video_timestamp(silent=True)

#             # Update current video info
#             self.current_video_title = new_title
#             self.current_video_url = new_video_url
#             self.current_video_id = new_video_id

#             # Clear notes and load the new video
#             self.notes.clear()
#             self.video_player.load(QUrl(self.current_video_url))

#             # Check for saved position after the new video loads
#             self.video_player.page().loadFinished.connect(
#                 lambda ok: self.check_saved_video_position(ok),
#                 Qt.ConnectionType.SingleConnection  # Ensures it runs only once
#             )

#     def save_current_video_timestamp(self, silent=True):
#         if not all([self.current_video_id, self.current_playlist_id]):
#             return

#         js = """
#             (function() {
#                 var player = document.querySelector('video');
#                 return player ? Math.floor(player.currentTime) : 0;
#             })();
#         """

#         def callback(seconds):
#             try:
#                 if seconds > 0:
#                     c.execute("""
#                         UPDATE playlist_videos
#                         SET last_position_seconds = ?
#                         WHERE playlist_id = ? 
#                         AND video_id = (SELECT id FROM videos WHERE youtube_id = ?)
#                     """, (seconds, self.current_playlist_id, self.current_video_id))
#                     conn.commit()

#                     if not silent:
#                         mins, secs = divmod(seconds, 60)
#                         QMessageBox.information(
#                             self, "Position Saved", 
#                             f"Saved {self.current_video_title} at {mins}:{secs:02}"
#                         )
#             except Exception as e:
#                 print("Error saving timestamp:", e)

#             self.video_player.page().runJavaScript(js, callback)
    
#     def check_saved_video_position(self, ok):
#         if not ok:
#             return

#         try:
#             c.execute("""
#                 SELECT last_position_seconds FROM playlist_videos
#                 WHERE playlist_id = ? 
#                 AND video_id = (SELECT id FROM videos WHERE youtube_id = ?)
#             """, (self.current_playlist_id, self.current_video_id))

#             result = c.fetchone()
#             if result and result[0] and result[0] > 0:
#                 seconds = result[0]
#                 mins = int(seconds // 60)
#                 secs = int(seconds % 60)

#                 reply = QMessageBox.question(
#                     self, "Resume Playback?",
#                     f"Resume '{self.current_video_title}' at {mins}:{secs:02}?",
#                     QMessageBox.Yes | QMessageBox.No
#                 )

#                 if reply == QMessageBox.Yes:
#                     js = f"""
#     #                     var player = document.querySelector('video');
#     #                     if (player) {{
#     #                         player.currentTime = {seconds};
#     #                     }}
#     #                 """
#                     self.video_player.page().runJavaScript(js)
#         except Exception as e:
#             print("Error checking for resume:", e)

#     def check_saved_video_position(self, ok):
#         if not ok or not self.current_video_id or not self.current_playlist_id:
#             return

#         try:
#             c.execute("""
#                 SELECT last_position_seconds FROM playlist_videos
#                 WHERE playlist_id = ? 
#                 AND video_id = (SELECT id FROM videos WHERE youtube_id = ?)
#             """, (self.current_playlist_id, self.current_video_id))

#             result = c.fetchone()
#             if result and result[0] is not None and result[0] > 0:
#                 seconds = result[0]
#                 mins, secs = divmod(seconds, 60)

#                 reply = QMessageBox.question(
#                     self, "Resume Playback?",
#                     f"Resume '{self.current_video_title}' at {mins}:{secs:02}?",
#                     QMessageBox.Yes | QMessageBox.No
#                 )

#                 if reply == QMessageBox.Yes:
#                     js = f"""
#                         var player = document.querySelector('video');
#                         if (player) {{
#                             player.currentTime = {seconds};
#                             player.play();
#                         }}
#                     """
#                     self.video_player.page().runJavaScript(js)
#         except Exception as e:
#             print("Error checking for resume:", e)

#     def insert_timestamp(self):
#         js = """
#             (function() {
#                 var player = document.querySelector('video');
#                 if (!player) return "00:00";
#                 var time = Math.floor(player.currentTime);
#                 var mins = Math.floor(time / 60);
#                 var secs = time % 60;
#                 return "[" + mins.toString().padStart(2, '0') + 
#                     ":" + secs.toString().padStart(2, '0') + "] ";
#             })();
#         """

#         def callback(timestamp):
#             cursor = self.notes.textCursor()
#             cursor.insertText(timestamp)

#         self.video_player.page().runJavaScript(js, callback)

#     def save_note(self):
#             note = self.notes.toPlainText().strip()
#             if not note:
#                 QMessageBox.warning(self, "Empty Note", "Cannot save empty note.")
#                 return

#             safe_title = re.sub(r'[\\/*?:"<>|]', "", self.current_video_title)
#             default_name = f"notes/{safe_title}.txt"

#             filename, _ = QFileDialog.getSaveFileName(
#                 self, "Save Note", default_name, "Text Files (*.txt)"
#             )

#             if filename:
#                 try:
#                     with open(filename, "w", encoding="utf-8") as f:
#                         f.write(note)
#                     QMessageBox.information(self, "Saved", f"Note saved to:\n{filename}")
#                 except Exception as e:
#                     QMessageBox.critical(self, "Error", f"Failed to save note:\n{e}")

# if __name__ == '__main__':
#     app = QApplication(sys.argv)
#     window = YouTubeNotesApp()
#     window.show()
#     sys.exit(app.exec_())\


# import sys
# import os
# import sqlite3
# import re
# import yt_dlp
# from PyQt5.QtWidgets import (
#     QApplication, QWidget, QVBoxLayout, QHBoxLayout,
#     QLineEdit, QPushButton, QListWidget, QTextEdit, QFileDialog, QMessageBox
# )
# from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings
# from PyQt5.QtCore import QUrl, Qt

# # Setup
# os.makedirs("notes", exist_ok=True)
# DB_PATH = "playlist.db"

# # Initialize DB
# conn = sqlite3.connect(DB_PATH)
# c = conn.cursor()
# # Create tables if they do not exist
# c.execute('''
# CREATE TABLE IF NOT EXISTS playlists (
#     id INTEGER PRIMARY KEY AUTOINCREMENT,
#     playlist_url TEXT UNIQUE
# )
# ''')

# c.execute('''
# CREATE TABLE IF NOT EXISTS videos (
#     id INTEGER PRIMARY KEY AUTOINCREMENT,
#     youtube_id TEXT UNIQUE,
#     video_url TEXT,
#     title TEXT
# )
# ''')

# c.execute('''
# CREATE TABLE IF NOT EXISTS playlist_videos (
#     id INTEGER PRIMARY KEY AUTOINCREMENT,
#     playlist_id INTEGER,
#     video_id INTEGER,
#     position INTEGER,
#     last_position_seconds INTEGER DEFAULT 0,
#     FOREIGN KEY (playlist_id) REFERENCES playlists(id),
#     FOREIGN KEY (video_id) REFERENCES videos(id),
#     UNIQUE (playlist_id, video_id)
# )
# ''')

# conn.commit()

# class YouTubeNotesApp(QWidget):
    
#     def __init__(self):
#         super().__init__()
#         self.setWindowTitle("\U0001F4D8 YouTube Playlist Notes App")
#         self.setMinimumSize(1000, 700)
#         self.current_video_title = None
#         self.current_video_url = None
#         self.current_video_id = None
#         self.current_playlist_id = None
#         self.video_data = []

#         self.video_player = QWebEngineView()
#         settings = self.video_player.settings()
#         settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
#         settings.setAttribute(QWebEngineSettings.PluginsEnabled, True)
#         settings.setAttribute(QWebEngineSettings.FullScreenSupportEnabled, True)
#         settings.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)

#         self.layout = QVBoxLayout(self)

#         self.url_input = QLineEdit()
#         self.url_input.setPlaceholderText("Paste YouTube playlist URL here")
#         self.layout.addWidget(self.url_input)

#         self.fetch_btn = QPushButton("Fetch Videos")
#         self.fetch_btn.clicked.connect(self.fetch_videos)
#         self.layout.addWidget(self.fetch_btn)

#         self.split_layout = QHBoxLayout()
#         self.layout.addLayout(self.split_layout)

#         self.video_list = QListWidget()
#         self.video_list.itemClicked.connect(self.play_selected_video)
#         self.split_layout.addWidget(self.video_list, 30)

#         self.right_panel = QVBoxLayout()
#         self.split_layout.addLayout(self.right_panel, 70)

#         self.right_panel.addWidget(self.video_player, 60)

#         self.notes = QTextEdit()
#         self.notes.setPlaceholderText("Take your notes here...")
#         self.right_panel.addWidget(self.notes, 30)

#         self.buttons = QHBoxLayout()
#         self.right_panel.addLayout(self.buttons)

#         self.add_playlist_btn = QPushButton("\u2795 Add Playlist to DB")
#         self.add_playlist_btn.setEnabled(False)
#         self.add_playlist_btn.clicked.connect(self.save_playlist_to_db)
#         self.buttons.addWidget(self.add_playlist_btn)

#         self.timestamp_btn = QPushButton("\u23F1 Insert Timestamp")
#         self.timestamp_btn.clicked.connect(self.insert_timestamp)
#         self.buttons.addWidget(self.timestamp_btn)

#         self.save_btn = QPushButton("💾 Save Note")
#         self.save_btn.clicked.connect(self.save_note)
#         self.buttons.addWidget(self.save_btn)

#         self.timestamp_btn.setEnabled(False)
#         self.save_btn.setEnabled(False)

#     def fetch_videos(self):
#         url = self.url_input.text().strip()
#         if not url:
#             QMessageBox.warning(self, "Error", "Please enter a playlist URL")
#             return

#         try:
#             ydl_opts = {
#                 'quiet': True,
#                 'extract_flat': True,
#                 'dump_single_json': True
#             }
#             with yt_dlp.YoutubeDL(ydl_opts) as ydl:
#                 info = ydl.extract_info(url, download=False)
#                 self.video_data.clear()
#                 self.video_list.clear()

#                 for entry in info['entries']:
#                     title = entry['title']
#                     video_url = f"https://www.youtube.com/watch?v={entry['id']}"
#                     youtube_id = entry['id']
#                     self.video_data.append((youtube_id, video_url, title))
#                     self.video_list.addItem(title)

#             c.execute("SELECT id FROM playlists WHERE playlist_url = ?", (url,))
#             result = c.fetchone()

#             if result:
#                 self.current_playlist_id = result[0]
#                 self.add_playlist_btn.setEnabled(False)
#                 self.timestamp_btn.setEnabled(True)
#                 self.save_btn.setEnabled(True)
#                 QMessageBox.information(self, "Info", "Existing playlist loaded from database")
#             else:
#                 self.add_playlist_btn.setEnabled(True)
#                 QMessageBox.information(self, "Success", f"Fetched {len(self.video_data)} videos. Click 'Add Playlist' to save.")

#         except Exception as e:
#             QMessageBox.critical(self, "Error", f"Failed to fetch playlist:\n{str(e)}")

#     def save_playlist_to_db(self):
#         url = self.url_input.text().strip()
#         try:
#             c.execute("INSERT INTO playlists (playlist_url) VALUES (?)", (url,))
#             self.current_playlist_id = c.lastrowid

#             for position, (youtube_id, video_url, title) in enumerate(self.video_data, start=1):
#                 c.execute("""
#                     INSERT OR IGNORE INTO videos (youtube_id, video_url, title) 
#                     VALUES (?, ?, ?)
#                 """, (youtube_id, video_url, title))

#                 c.execute("SELECT id FROM videos WHERE youtube_id = ?", (youtube_id,))
#                 video_id = c.fetchone()[0]

#                 c.execute("""
#                     INSERT INTO playlist_videos (playlist_id, video_id, position) 
#                     VALUES (?, ?, ?)
#                 """, (self.current_playlist_id, video_id, position))

#             conn.commit()
#             self.add_playlist_btn.setEnabled(False)
#             self.timestamp_btn.setEnabled(True)
#             self.save_btn.setEnabled(True)
#             QMessageBox.information(self, "Success", "Playlist saved to database")

#         except Exception as e:
#             QMessageBox.critical(self, "Error", f"Failed to save playlist:\n{str(e)}")

#     def play_selected_video(self, item):
#         new_title = item.text()
#         new_video_id = None
#         new_video_url = None

#         # Find video info
#         for youtube_id, video_url, title in self.video_data:
#             if title == new_title:
#                 new_video_id = youtube_id
#                 new_video_url = video_url
#                 break

#         # Save current timestamp
#         if self.current_video_id and self.current_video_id != new_video_id:
#             self.save_current_video_timestamp(silent=True)

#         # Update current video info
#         self.current_video_title = new_title
#         self.current_video_url = new_video_url
#         self.current_video_id = new_video_id

#         # Clear notes and load video
#         self.notes.clear()
#         self.video_player.load(QUrl(self.current_video_url))

#         # Use single-shot lambda to check saved position only once
#         def check_once(ok):
#             if ok:
#                 self.check_saved_video_position()

#             # Disconnect previous connections (optional)
#             try:
#                 self.video_player.page().loadFinished.disconnect()
#             except:
#                 pass

#             self.video_player.page().loadFinished.connect(check_once)

#             def save_current_video_timestamp(self, silent=True):
#                 if not all([self.current_video_id, self.current_playlist_id]):
#                     return

#                 js = """
#                     (function() {
#                         var player = document.querySelector('video');
#                         return player ? Math.floor(player.currentTime) : 0;
#                     })();
#                 """

#                 def callback(seconds):
#                     try:
#                         if seconds > 0:
#                             c.execute("""
#                                 UPDATE playlist_videos
#                                 SET last_position_seconds = ?
#                                 WHERE playlist_id = ? 
#                                 AND video_id = (SELECT id FROM videos WHERE youtube_id = ?)
#                             """, (seconds, self.current_playlist_id, self.current_video_id))
#                             conn.commit()
#                             if not silent:
#                                 mins, secs = divmod(seconds, 60)
#                                 QMessageBox.information(
#                                     self, "Position Saved", 
#                                     f"Saved {self.current_video_title} at {mins}:{secs:02}"
#                                 )
#                     except Exception as e:
#                         print("Error saving timestamp:", e)
#                         print("Saving timestamp for:", self.current_video_id)


#         self.video_player.page().runJavaScript(js, callback)

#     def check_saved_video_position_once(self, ok):
#         try:
#             self.video_player.page().loadFinished.disconnect()
#         except Exception:
#             pass
#         self.check_saved_video_position(ok)
#     def check_saved_video_position(self):
#         try:
#             c.execute("""
#                 SELECT last_position_seconds FROM playlist_videos
#                 WHERE playlist_id = ? 
#                 AND video_id = (SELECT id FROM videos WHERE youtube_id = ?)
#             """, (self.current_playlist_id, self.current_video_id))

#             result = c.fetchone()
#             if result and result[0] and result[0] > 0:
#                 seconds = result[0]
#                 mins = int(seconds // 60)
#                 secs = int(seconds % 60)

#                 reply = QMessageBox.question(
#                     self, "Resume Playback?",
#                     f"Resume '{self.current_video_title}' at {mins}:{secs:02}?",
#                     QMessageBox.Yes | QMessageBox.No
#                 )

#                 if reply == QMessageBox.Yes:
#                     js = f"""
#                         var player = document.querySelector('video');
#                         if (player) {{
#                             player.currentTime = {seconds};
#                             player.play();
#                         }}
#                     """
#                     self.video_player.page().runJavaScript(js)
#         except Exception as e:
#             print("Error checking resume position:", e)

#     def insert_timestamp(self):
#         js = """
#             (function() {
#                 var player = document.querySelector('video');
#                 if (!player) return "00:00";
#                 var time = Math.floor(player.currentTime);
#                 var mins = Math.floor(time / 60);
#                 var secs = time % 60;
#                 return "[" + mins.toString().padStart(2, '0') + 
#                        ":" + secs.toString().padStart(2, '0') + "] ";
#             })();
#         """

#         def callback(timestamp):
#             cursor = self.notes.textCursor()
#             cursor.insertText(timestamp)

#         self.video_player.page().runJavaScript(js, callback)

#     def save_note(self):
#         note = self.notes.toPlainText().strip()
#         if not note:
#             QMessageBox.warning(self, "Empty Note", "Cannot save empty note.")
#             return

#         safe_title = re.sub(r'[\\/*?:"<>|]', "", self.current_video_title)
#         default_name = f"notes/{safe_title}.txt"

#         filename, _ = QFileDialog.getSaveFileName(
#             self, "Save Note", default_name, "Text Files (*.txt)"
#         )

#         if filename:
#             try:
#                 with open(filename, "w", encoding="utf-8") as f:
#                     f.write(note)
#                 QMessageBox.information(self, "Saved", f"Note saved to:\n{filename}")
#             except Exception as e:
#                 QMessageBox.critical(self, "Error", f"Failed to save note:\n{e}")

# if __name__ == '__main__':
#     app = QApplication(sys.argv)
#     window = YouTubeNotesApp()
#     window.show()
#     sys.exit(app.exec_())


import sys
import os
import sqlite3
import re
import yt_dlp
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
        self.url_input.setPlaceholderText("Paste YouTube playlist URL here")
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
                    self.video_list.addItem(title)

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
    app = QApplication(sys.argv)
    window = YouTubeNotesApp()
    window.show()
    sys.exit(app.exec_())