import sys
import os
import glob
import sqlite3
import re
import yt_dlp
from PyQt5.QtWidgets import QListWidgetItem, QHBoxLayout, QLabel, QPushButton 
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QListWidget, QTextEdit, QFileDialog, QMessageBox
)
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings
from PyQt5.QtWidgets import QSplitter
from PyQt5.QtCore import QUrl, Qt
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QSplitter
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

c.execute('''
CREATE TABLE IF NOT EXISTS history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT UNIQUE,
    accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

c.execute('''
CREATE TABLE IF NOT EXISTS video_timestamps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    playlist_id INTEGER,
    video_id INTEGER,
    timestamp_seconds INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (playlist_id) REFERENCES playlists(id),
    FOREIGN KEY (video_id) REFERENCES videos(id)
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
        self.url_input.setPlaceholderText("Paste YouTube Video or  Playlist URL here and press Enter")
        self.url_input.returnPressed.connect(self.on_enter_pressed)
        self.layout.addWidget(self.url_input)

        # self.fetch_btn = QPushButton("Fetch Videos")
        # self.fetch_btn.clicked.connect(self.fetch_videos)
        # self.layout.addWidget(self.fetch_btn)

        self.top_buttons_layout = QHBoxLayout()
        self.layout.addLayout(self.top_buttons_layout)

        self.fetch_btn = QPushButton("Fetch Videos")
        self.fetch_btn.clicked.connect(self.fetch_videos)
        self.top_buttons_layout.addWidget(self.fetch_btn)

        self.minimize_btn = QPushButton("➖ Hide Video List")
        self.minimize_btn.clicked.connect(self.toggle_video_list_visibility)
        self.top_buttons_layout.addWidget(self.minimize_btn)
        

        # self.split_layout = QHBoxLayout()
        # self.layout.addLayout(self.split_layout)

        # self.video_list = QListWidget()
        # self.video_list.itemClicked.connect(self.play_selected_video)
        # self.split_layout.addWidget(self.video_list, 30)

        # self.right_panel = QVBoxLayout()
        # self.split_layout.addLayout(self.right_panel, 70)
        # self.right_panel.addWidget(self.video_player, 60)
        # self.right_panel.addWidget(self.notes, 30)

        # self.right_panel = QVBoxLayout()
        # self.split_layout.addLayout(self.right_panel, 70)
         
        

        # Split main area horizontally
        self.main_splitter = QSplitter(Qt.Horizontal)
        self.layout.addWidget(self.main_splitter)

        # 📺 Left panel: Video List with Minimize button
        self.video_list_panel = QWidget()
        video_list_layout = QVBoxLayout()
        video_list_layout.setContentsMargins(0, 0, 0, 0)

        # Add Minimize button on top of video list
        # self.minimize_btn = QPushButton("➖ Minimize")
        # self.minimize_btn.clicked.connect(self.toggle_video_list_visibility)
        # video_list_layout.addWidget(self.minimize_btn)

        # Add actual video list
        self.video_list = QListWidget()
        self.video_list.itemClicked.connect(self.play_selected_video)
        video_list_layout.addWidget(self.video_list)
        self.video_list_panel.setLayout(video_list_layout)

        self.notes = QTextEdit()
        self.notes.setPlaceholderText("Take your notes here...\n\n"
                        "=== Keyboard Shortcuts ===\n"
                        "Note Management:\n"
                        "- Ctrl+S: Save current note\n"
                        "- Ctrl+T: Insert timestamp at current position\n"
                        "\n"
                        "Navigation:\n"
                        "- Ctrl+N: Focus notes editor\n"
                        "- Ctrl+L: Focus video list\n"
                        "- Space: Play/Pause video\n"
                        "- F11: Toggle fullscreen mode")
        font = self.notes.font()
        font.setPointSize(12)  # Change 12 to your desired font size
        self.notes.setFont(font)

        # ✅ 2. Now safely create the vertical splitter
        self.right_splitter = QSplitter(Qt.Vertical)
        self.right_splitter.addWidget(self.video_player)
        self.right_splitter.addWidget(self.notes)
        self.right_splitter.setSizes([400, 300])
        # Set the font size for the notes QTextEdit

        # 🧠 Right panel (browser + notes in vertical splitter)


        # Add both panels to main splitter
        self.main_splitter.addWidget(self.video_list_panel)
        self.main_splitter.addWidget(self.right_splitter)
        self.main_splitter.setSizes([300, 700])  # Initial sizes       
        
        # ✅ Create a container widget for the button row
        self.button_row = QWidget()
        self.buttons = QHBoxLayout(self.button_row)

        # 🧽 Tighten spacing inside the button row
        self.buttons.setContentsMargins(5, 2, 5, 2)
        self.buttons.setSpacing(10)

        # ✂️ Remove extra height
        self.button_row.setFixedHeight(40)

        # Add buttons
        self.add_playlist_btn = QPushButton("➕ Add Playlist to DB")
        self.add_playlist_btn.setEnabled(False)
        self.buttons.addWidget(self.add_playlist_btn)

        # Insert Timestamp Button
        self.timestamp_btn = QPushButton("⏱ Insert Timestamp")
        self.timestamp_btn.clicked.connect(self.insert_timestamp)
        self.timestamp_btn.setEnabled(False)
        self.buttons.addWidget(self.timestamp_btn)

        # ✅ NEW: Timestamps Button
        self.view_timestamps_btn = QPushButton("⏳ Timestamps")
        self.view_timestamps_btn.clicked.connect(self.show_timestamps_for_current_video)
        self.view_timestamps_btn.setEnabled(False)
        self.buttons.addWidget(self.view_timestamps_btn)


        self.save_btn = QPushButton("💾 Save Note")
        self.save_btn.setEnabled(False)
        self.buttons.addWidget(self.save_btn)

        # ✅ Add to layout (no gap)
        self.layout.addWidget(self.button_row)

        self.buttons = QHBoxLayout()
        # self.right_panel.addLayout(self.buttons)
        self.history_btn = QPushButton("📜 History")
        self.history_btn.clicked.connect(self.show_history)
        self.layout.addWidget(self.history_btn)


        self.saved_playlists_btn = QPushButton("📂 Saved Playlists")
        self.saved_playlists_btn.clicked.connect(self.show_saved_playlists)
        self.layout.addWidget(self.saved_playlists_btn)

        
        # self.minimize_btn.setVisible(False)
        # self.timestamp_btn.setEnabled(False)
        # self.save_btn.setEnabled(False)
        # self.add_playlist_btn.setEnabled(False)
        self.minimize_btn.setVisible(False)          # Hidden until playlist is fetched
        self.add_playlist_btn.setVisible(True)       # Always visible
        self.add_playlist_btn.setEnabled(False)      # But disabled initially

        self.timestamp_btn.setVisible(True)
        self.timestamp_btn.setEnabled(False)

        self.save_btn.setVisible(True)
        self.save_btn.setEnabled(False)


        self.setup_shortcuts()

    def setup_shortcuts(self):
        """Configure keyboard shortcuts for common actions"""
        # Save Note - Ctrl+S
        self.save_shortcut = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+S"), self)
        self.save_shortcut.activated.connect(self.save_note)
        
        # Insert Timestamp - Ctrl+T
        self.timestamp_shortcut = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+T"), self)
        self.timestamp_shortcut.activated.connect(self.insert_timestamp)
        
        # Focus Notes - Ctrl+N
        self.focus_notes_shortcut = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+N"), self)
        self.focus_notes_shortcut.activated.connect(self.notes.setFocus)
        
        # Focus Video List - Ctrl+L
        self.focus_list_shortcut = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+L"), self)
        self.focus_list_shortcut.activated.connect(self.video_list.setFocus)
        
        # Play/Pause Toggle - Space
        self.play_pause_shortcut = QtWidgets.QShortcut(Qt.Key_Space, self)
        self.play_pause_shortcut.activated.connect(self.toggle_play_pause)
        
        # Fullscreen Toggle - F11
        self.fullscreen_shortcut = QtWidgets.QShortcut(QtGui.QKeySequence("F11"), self)
        self.fullscreen_shortcut.activated.connect(self.toggle_fullscreen)

    def toggle_play_pause(self):
        """Toggle video play/pause state"""
        js = """
        (function() {
            var player = document.querySelector('video');
            if (player) {
                if (player.paused) {
                    player.play();
                } else {
                    player.pause();
                }
            }
        })();
        """
        self.video_player.page().runJavaScript(js)

    def toggle_fullscreen(self):
        """Toggle fullscreen mode"""
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()


    def on_enter_pressed(self):
        """Handler for when Enter key is pressed in URL input"""
        if not self.url_input.text().strip():
            QMessageBox.warning(self, "Error", "Please enter a playlist URL first")
        else:
            self.fetch_videos()

    def fetch_videos(self):
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Error", "Please enter a YouTube video or playlist URL")
            return

        # ✅ Option 3: Disable UI
        self.setEnabled(False)
        try:
            # Add to history (or update timestamp)
            c.execute("""
                INSERT INTO history (url) VALUES (?)
                ON CONFLICT(url) DO UPDATE SET accessed_at = CURRENT_TIMESTAMP
            """, (url,))
            conn.commit()
        except Exception as e:
            print("Error logging to history:", e)

        # if not url:
        #     QMessageBox.warning(self, "Error", "Please enter a YouTube video or playlist URL")
        #     return

        try:
            self.video_data.clear()
            self.video_list.clear()
            self.current_playlist_id = None

            ydl_opts = {
                'quiet': True,
                'dump_single_json': True,
                'extract_flat': True,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

                # Check if it's a playlist
            if 'entries' in info:
    # Playlist
                for entry in info['entries']:
                    title = entry.get('title')
                    video_url = f"https://www.youtube.com/watch?v={entry['id']}"
                    youtube_id = entry.get('id')
                    self.video_data.append((youtube_id, video_url, title))

                    # Add to list widget
                    item = QListWidgetItem()
                    widget = QWidget()
                    layout = QHBoxLayout()
                    title_label = QLabel(title)
                    layout.addWidget(title_label, stretch=1)
                    open_btn = QPushButton("Play ▶")
                    open_btn.clicked.connect(lambda _, vid_url=video_url: self.play_video_by_url(vid_url))
                    layout.addWidget(open_btn)
                    widget.setLayout(layout)
                    item.setSizeHint(widget.sizeHint())
                    self.video_list.addItem(item)
                    self.video_list.setItemWidget(item, widget)
                    self.minimize_btn.setVisible(True)
                    self.view_timestamps_btn.setEnabled(True)


                # 🔁 ✅ Now check DB only for playlists
                c.execute("SELECT id FROM playlists WHERE playlist_url = ?", (url,))
                result = c.fetchone()

                if result:
                    self.current_playlist_id = result[0]
                    self.add_playlist_btn.setEnabled(False)
                    self.add_playlist_btn.setText("📁 Playlist Already Added")
                    QMessageBox.information(self, "Info", "Existing playlist loaded from database")
                else:
                    self.add_playlist_btn.setEnabled(True)
                    QMessageBox.information(self, "Success", f"Fetched {len(self.video_data)} videos. Click 'Add Playlist' to save.")

                self.timestamp_btn.setEnabled(True)
                self.save_btn.setEnabled(True)
                self.minimize_btn.setVisible(True)
                # self.timestamp_btn.setEnabled(True)
                self.add_playlist_btn.setEnabled(True)

            else:
                # Single video
                title = info.get('title')
                youtube_id = info.get('id')
                video_url = f"https://www.youtube.com/watch?v={youtube_id}"
                self.video_data.append((youtube_id, video_url, title))

                item = QListWidgetItem()
                widget = QWidget()
                layout = QHBoxLayout()
                title_label = QLabel(title)
                layout.addWidget(title_label, stretch=1)
                open_btn = QPushButton("Play ▶")
                open_btn.clicked.connect(lambda _, vid_url=video_url: self.play_video_by_url(vid_url))
                layout.addWidget(open_btn)
                widget.setLayout(layout)
                item.setSizeHint(widget.sizeHint())
                self.video_list.addItem(item)
                self.video_list.setItemWidget(item, widget)

                # 🔁 ✅ Don't check DB — just enable buttons
                self.add_playlist_btn.setEnabled(False)
                self.add_playlist_btn.setText("➕ Add Playlist to DB")      
                self.timestamp_btn.setEnabled(True)
                self.save_btn.setEnabled(True)
                self.minimize_btn.setVisible(False)
                self.view_timestamps_btn.setEnabled(True)

                QMessageBox.information(self, "Success", f"Fetched single video: {title}")


        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to fetch video/playlist:\n{str(e)}")
        
        finally:
        # ✅ Re-enable UI
            self.setEnabled(True)

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
            self.view_timestamps_btn.setEnabled(True)
            QMessageBox.information(self, "Success", "Playlist saved to database","Button are enabled")

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
                if (!player) return "\\n[00:00]:";
                var time = Math.floor(player.currentTime);
                var mins = Math.floor(time / 60);
                var secs = time % 60;
                return "\\n[" + mins.toString().padStart(2, '0') + 
                    ":" + secs.toString().padStart(2, '0') + "]:"; 
            })();
        """

        def callback(timestamp_text):  # ✅ The variable is passed here
            # ✅ Insert into notes
            cursor = self.notes.textCursor()
            cursor.insertText(timestamp_text)

            # ✅ Save to DB as seconds
            try:
                match = re.search(r'\[(\d+):(\d+)\]', timestamp_text)
                if match and self.current_video_id and self.current_playlist_id:
                    mins, secs = int(match.group(1)), int(match.group(2))
                    total_seconds = mins * 60 + secs
                    c.execute('''
                        INSERT INTO video_timestamps (playlist_id, video_id, timestamp_seconds)
                        VALUES (?, ?, ?)
                    ''', (self.current_playlist_id, self.get_video_db_id(self.current_video_id), total_seconds))
                    conn.commit()
            except Exception as e:
                print("Error saving timestamp:", e)

        self.video_player.page().runJavaScript(js, callback)

    def get_video_db_id(self, youtube_id):
        c.execute("SELECT id FROM videos WHERE youtube_id = ?", (youtube_id,))
        result = c.fetchone()
        return result[0] if result else None
    

    def show_timestamps_for_current_video(self):
        if not self.current_video_id or not self.current_playlist_id:
            QMessageBox.warning(self, "No video", "No video is currently loaded.")
            return

        video_db_id = self.get_video_db_id(self.current_video_id)
        c.execute('''
            SELECT timestamp_seconds, created_at FROM video_timestamps
            WHERE playlist_id = ? AND video_id = ?
            ORDER BY timestamp_seconds
        ''', (self.current_playlist_id, video_db_id))
        timestamps = c.fetchall()

        if not timestamps:
            QMessageBox.information(self, "No Timestamps", "No timestamps saved for this video.")
            return

        dlg = QtWidgets.QDialog(self)
        dlg.setWindowTitle("⏳ Saved Timestamps")
        dlg.resize(400, 300)

        layout = QVBoxLayout()
        list_widget = QListWidget()
        for seconds, created_at in timestamps:
            mins, secs = divmod(seconds, 60)
            text = f"[{mins:02}:{secs:02}] (Saved at {created_at})"
            list_item = QListWidgetItem(text)
            list_widget.addItem(list_item)
        layout.addWidget(list_widget)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dlg.close)
        layout.addWidget(close_btn, alignment=Qt.AlignRight)

        dlg.setLayout(layout)
        dlg.exec_()


    def save_note(self):
        if not all([self.current_video_id, self.current_playlist_id]):
            QMessageBox.warning(self, "Error", "No video selected")
            return

        note = self.notes.toPlainText().strip()
        if not note:
            QMessageBox.warning(self, "Empty Note", "Cannot save empty note")
            return

        try:
            # Get info from database
            c.execute("""
                SELECT p.playlist_url, v.title 
                FROM playlists p
                JOIN videos v ON v.youtube_id = ?
                WHERE p.id = ?
            """, (self.current_video_id, self.current_playlist_id))
            result = c.fetchone()
            
            playlist_url, video_title = result if result else (None, None)

            # Create folder names
            playlist_name = f"Playlist_{self.current_playlist_id}" if not playlist_url else "Unnamed_Playlist"
            video_name = video_title if video_title else f"Video_{self.current_video_id}"
            
            safe_playlist = re.sub(r'[\\/*?:"<>|]', "", playlist_name)
            safe_video = re.sub(r'[\\/*?:"<>|]', "", video_name)
            
            note_folder = os.path.join("notes", safe_playlist, safe_video)
            os.makedirs(note_folder, exist_ok=True)

            # Save with timestamp
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(note_folder, f"note_{timestamp}.txt")
            
            with open(filename, "w", encoding="utf-8") as f:
                f.write(note)

            QMessageBox.information(self, "Saved", f"Note saved to:\n{filename}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save note:\n{e}")

    
    def show_saved_playlists(self):
        dlg = QtWidgets.QDialog(self)
        dlg.setWindowTitle("📂 Your Saved Playlists")
        dlg.resize(600, 400)

        layout = QVBoxLayout()
        list_widget = QtWidgets.QListWidget()

        # Fetch saved playlists from DB
        c.execute("SELECT id, playlist_url FROM playlists ORDER BY id DESC")
        playlists = c.fetchall()

        if not playlists:
            QMessageBox.information(self, "No Saved Playlists", "You haven't saved any playlists yet.")
            return

        for pid, url in playlists:
            item = QListWidgetItem()
            widget = QWidget()
            hbox = QHBoxLayout()

            # Short display version of URL
            short_url = url if len(url) < 60 else url[:55] + "..."
            url_label = QLabel(short_url)
            url_label.setToolTip(url)
            hbox.addWidget(url_label, stretch=2)

            # Open Playlist Button
            open_btn = QPushButton("Open Playlist")
            open_btn.clicked.connect(lambda _, playlist_url=url: self.open_saved_playlist(playlist_url, dlg))
            hbox.addWidget(open_btn)

            widget.setLayout(hbox)
            item.setSizeHint(widget.sizeHint())
            list_widget.addItem(item)
            list_widget.setItemWidget(item, widget)

        layout.addWidget(list_widget)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dlg.close)
        layout.addWidget(close_btn, alignment=Qt.AlignRight)

        dlg.setLayout(layout)
        dlg.exec_()
    
    def open_saved_playlist(self, playlist_url, dialog):
        self.url_input.setText(playlist_url)
        dialog.close()
        self.url_input.returnPressed.emit()

    def show_history(self):
        dlg = QtWidgets.QDialog(self)
        dlg.setWindowTitle("📜 History - Recently Accessed")
        dlg.resize(600, 400)

        layout = QVBoxLayout()
        list_widget = QtWidgets.QListWidget()

        # Fetch history entries
        c.execute("SELECT url, accessed_at FROM history ORDER BY accessed_at DESC LIMIT 50")
        rows = c.fetchall()

        if not rows:
            QMessageBox.information(self, "No History", "No previously accessed items found.")
            return

        for url, timestamp in rows:
            item = QListWidgetItem()
            widget = QWidget()
            hbox = QHBoxLayout()

            short_url = url if len(url) < 60 else url[:55] + "..."
            url_label = QLabel(f"{short_url}")
            url_label.setToolTip(f"{url}\nAccessed: {timestamp}")
            hbox.addWidget(url_label, stretch=2)

            open_btn = QPushButton("Open")
            open_btn.clicked.connect(lambda _, u=url: self.open_from_history(u, dlg))
            hbox.addWidget(open_btn)

            widget.setLayout(hbox)
            item.setSizeHint(widget.sizeHint())
            list_widget.addItem(item)
            list_widget.setItemWidget(item, widget)

        layout.addWidget(list_widget)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dlg.close)
        layout.addWidget(close_btn, alignment=Qt.AlignRight)

        dlg.setLayout(layout)
        dlg.exec_()

    def open_from_history(self, url, dialog):
        self.url_input.setText(url)
        dialog.close()
        self.url_input.returnPressed.emit()

    def toggle_video_list_visibility(self):
        sizes = self.main_splitter.sizes()
        total = sum(sizes)

        if sizes[0] > 0:
            # Collapse video list
            self.main_splitter.setSizes([0, total])
            self.minimize_btn.setText("➕ Show Video List")
        else:
            # Expand video list back to 300
            self.main_splitter.setSizes([300, total - 300])
            self.minimize_btn.setText("➖ Hide Video List")




def cleanup_temp_files():
    for f in glob.glob("*.tmp"):
        try:
            os.remove(f)
        except:
            pass

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = YouTubeNotesApp()
    window.show()
    cleanup_temp_files()
    sys.exit(app.exec_())

