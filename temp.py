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
from PyQt5 import QtCore
import uuid


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


c.execute('''
CREATE TABLE IF NOT EXISTS VideoKeys (
    id TEXT PRIMARY KEY,
    video_id INTEGER,
    playlist_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (video_id, playlist_id),
    FOREIGN KEY (video_id) REFERENCES videos(id),
    FOREIGN KEY (playlist_id) REFERENCES playlists(id)
)
''')

# 2. Advanced Note Table with formatting + media + timestamp
c.execute('''
CREATE TABLE IF NOT EXISTS Complete_Notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key_id TEXT,
    timestamp_seconds INTEGER,
    content_html TEXT,
    formatting_json TEXT,
    resource_paths TEXT,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (key_id) REFERENCES VideoKeys(id),
    UNIQUE (key_id, timestamp_seconds)
)
''')

# 3. Last Watched Position Table
c.execute('''
CREATE TABLE IF NOT EXISTS LastPlayback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key_id TEXT,
    last_position_seconds INTEGER,
    last_position_str TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (key_id) REFERENCES VideoKeys(id),
    UNIQUE (key_id)
)
''')

conn.commit()


def get_or_create_key_id(video_id, playlist_id):
    """Returns the key_id if exists, else creates and returns a new one"""
    try:
        c.execute("SELECT key_id FROM VideoKeys WHERE video_id = ? AND playlist_id = ?", (video_id, playlist_id))
        result = c.fetchone()
        if result:
            return result[0]
        
        # Create new key_id (use hash of video+playlist or UUID)
        import uuid
        key_id = uuid.uuid4().hex  # Unique 32-char hash
        c.execute("INSERT INTO VideoKeys (video_id, playlist_id, key_id) VALUES (?, ?, ?)", (video_id, playlist_id, key_id))
        conn.commit()
        print(f"🆕 [get_or_create_key_id] Created new key_id: {key_id}")
        return key_id

    except Exception as e:
        print(f"❌ [get_or_create_key_id] Error: {e}")
        return None


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

        self.main_layout = QVBoxLayout(self)
        self.setLayout(self.main_layout)

        self.menu_bar = QtWidgets.QMenuBar(self)
        self.main_layout.setMenuBar(self.menu_bar)


        # 📝 Notes Menu
        self.notes_menu = self.menu_bar.addMenu("📝 Notes")

        # Font Style
        font_combo = QtWidgets.QFontComboBox()
        font_combo.currentFontChanged.connect(lambda font: self.notes.setCurrentFont(font))
        font_style_action = QtWidgets.QWidgetAction(self)
        font_style_action.setDefaultWidget(font_combo)
        self.notes_menu.addAction(font_style_action)

        # Font Size
        font_size_combo = QtWidgets.QComboBox()
        font_size_combo.addItems(["8", "10", "12", "14", "16", "18", "20", "24", "28", "32"])
        font_size_combo.setCurrentText("12")
        font_size_combo.currentTextChanged.connect(lambda size: self.notes.setFontPointSize(float(size)))
        font_size_action = QtWidgets.QWidgetAction(self)
        font_size_action.setDefaultWidget(font_size_combo)
        self.notes_menu.addAction(font_size_action)


        bold = QtWidgets.QAction("Bold", self, shortcut="Ctrl+B", triggered=lambda: self.notes.setFontWeight(QtGui.QFont.Bold if self.notes.fontWeight() != QtGui.QFont.Bold else QtGui.QFont.Normal))
        italic = QtWidgets.QAction("Italic", self, shortcut="Ctrl+I", triggered=lambda: self.notes.setFontItalic(not self.notes.fontItalic()))
        underline = QtWidgets.QAction("Underline", self, shortcut="Ctrl+U", triggered=lambda: self.notes.setFontUnderline(not self.notes.fontUnderline()))

        self.notes_menu.addAction(bold)
        self.notes_menu.addAction(italic)
        self.notes_menu.addAction(underline)
            # Add to menu
        table_action = QtWidgets.QAction("Insert Table", self)
        table_action.triggered.connect(self.insert_custom_table)
        self.notes_menu.addAction(table_action)

        link_action = QtWidgets.QAction("Insert Hyperlink", self)
        link_action.triggered.connect(self.insert_hyperlink)
        self.notes_menu.addAction(link_action)

        img_action = QtWidgets.QAction("Insert Image", self)
        img_action.triggered.connect(self.insert_image)
        self.notes_menu.addAction(img_action)

        file_link_action = QtWidgets.QAction("Insert File Link", self)
        file_link_action.triggered.connect(self.insert_file_link)
        self.notes_menu.addAction(file_link_action)
        
        self.notes_menu.addSeparator()

        bullet_action = QtWidgets.QAction("Insert Bullet List", self)
        bullet_action.triggered.connect(lambda: self.notes.textCursor().insertList(QtGui.QTextListFormat.ListDisc))
        self.notes_menu.addAction(bullet_action)

        numbered_action = QtWidgets.QAction("Insert Numbered List", self)
        numbered_action.triggered.connect(lambda: self.notes.textCursor().insertList(QtGui.QTextListFormat.ListDecimal))
        self.notes_menu.addAction(numbered_action)




        

        self.video_player = QWebEngineView()
        settings = self.video_player.settings()
        settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.PluginsEnabled, True)
        settings.setAttribute(QWebEngineSettings.FullScreenSupportEnabled, True)
        settings.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)

        # self.layout = QVBoxLayout(self)
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Paste YouTube Video or  Playlist URL here and press Enter")
        self.url_input.returnPressed.connect(self.on_enter_pressed)
        self.main_layout.addWidget(self.url_input)


        self.top_buttons_layout = QHBoxLayout()
        self.main_layout.addLayout(self.top_buttons_layout)

        self.fetch_btn = QPushButton("Fetch Videos")
        self.fetch_btn.clicked.connect(self.fetch_videos)
        self.top_buttons_layout.addWidget(self.fetch_btn)

        self.minimize_btn = QPushButton("➖ Hide Video List")
        self.minimize_btn.clicked.connect(self.toggle_video_list_visibility)
        self.top_buttons_layout.addWidget(self.minimize_btn)
        
        self.main_splitter = QSplitter(Qt.Horizontal)
        self.main_layout.addWidget(self.main_splitter)

        # 📺 Left panel: Video List with Minimize button
        self.video_list_panel = QWidget()
        video_list_layout = QVBoxLayout()
        video_list_layout.setContentsMargins(0, 0, 0, 0)


        # Add actual video list
        self.video_list = QListWidget()
        self.video_list.itemClicked.connect(self.play_selected_video)
        video_list_layout.addWidget(self.video_list)
        self.video_list_panel.setLayout(video_list_layout)

        self.notes = QTextEdit()
        self.notes = QtWidgets.QTextBrowser()
        self.notes.setOpenExternalLinks(True)
        self.notes.setOpenLinks(False)
        self.notes.setReadOnly(False)
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
        self.notes.anchorClicked.connect(self.open_screenshot_link)

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

        self.screenshot_btn = QPushButton("📸Take Screenshot")
        self.screenshot_btn.setToolTip("Take Screenshot (Ctrl+Shift+S)") 
        self.screenshot_btn.clicked.connect(self.capture_video_screenshot)
        self.screenshot_btn.setEnabled(False)

        self.buttons.addWidget(self.screenshot_btn)
        # ✅ Add keyboard shortcut for screenshot
        self.screenshot_shortcut = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+Shift+S"), self)
        self.screenshot_shortcut.activated.connect(self.capture_video_screenshot)

        self.view_screenshots_btn = QPushButton("📷Saved Screenshots")
        self.view_screenshots_btn.clicked.connect(self.show_screenshots_for_current_video)
        self.view_screenshots_btn.setEnabled(False)
        self.buttons.addWidget(self.view_screenshots_btn)


        # ✅ Add to layout (no gap)
        self.main_layout.addWidget(self.button_row)

        self.buttons = QHBoxLayout()
        # self.right_panel.addLayout(self.buttons)
        self.history_btn = QPushButton("📜 History")
        self.history_btn.clicked.connect(self.show_history)
        self.main_layout.addWidget(self.history_btn)


        self.saved_playlists_btn = QPushButton("📂 Saved Playlists")
        self.saved_playlists_btn.clicked.connect(self.show_saved_playlists)
        self.main_layout.addWidget(self.saved_playlists_btn)

        
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
                    layout.setContentsMargins(5, 5, 5, 5)

                    open_btn = QPushButton("Play ▶")
                    open_btn.clicked.connect(lambda _, vid_url=video_url: self.play_video_by_url(vid_url))
                    layout.addWidget(open_btn)

                     # 🔁 Loop button (toggles loop for current video)
                    loop_btn = QPushButton("🔁 Loop: OFF")
                    loop_btn.setCheckable(True)

                    def make_toggle_loop(btn, url):
                        def toggle(checked):
                            if checked:
                                btn.setText("🔁 Loop: ON")
                                self.enable_loop_js()
                            else:
                                btn.setText("🔁 Loop: OFF")
                                self.disable_loop_js()
                        return toggle

                    loop_btn.toggled.connect(make_toggle_loop(loop_btn, video_url))
                    layout.addWidget(loop_btn)


                    title_label = QLabel(title)
                    layout.addWidget(title_label, stretch=1)

                    


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
                self.screenshot_btn.setEnabled(True)

                self.save_btn.setEnabled(True)
                self.minimize_btn.setVisible(True)
                self.view_screenshots_btn.setEnabled(True)
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

                

                layout.setContentsMargins(5, 5, 5, 5)

                open_btn = QPushButton("Play ▶")
                open_btn.clicked.connect(lambda _, vid_url=video_url: self.play_video_by_url(vid_url))
                layout.addWidget(open_btn)

                    # 🔁 Loop button (toggles loop for current video)
                loop_btn = QPushButton("🔁 Loop: OFF")
                loop_btn.setCheckable(True)

                def make_toggle_loop(btn, url):
                    def toggle(checked):
                        if checked:
                            btn.setText("🔁 Loop: ON")
                            self.enable_loop_js()
                        else:
                            btn.setText("🔁 Loop: OFF")
                            self.disable_loop_js()
                    return toggle

                loop_btn.toggled.connect(make_toggle_loop(loop_btn, video_url))
                layout.addWidget(loop_btn)

                title_label = QLabel(title)
                layout.addWidget(title_label, stretch=1)

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
                self.view_screenshots_btn.setEnabled(True)


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
        print(f"🎬 Switching to video: {new_title}")
        new_video_id, new_video_url = None, None

        # Match video from self.video_data
        for youtube_id, video_url, title in self.video_data:
            if title == new_title:
                new_video_id = youtube_id
                new_video_url = video_url
                break
            print(f"📺 Matched video ID: {new_video_id}")
        # ✅ Save current timestamp before switching
        if self.current_video_id and self.current_video_id != new_video_id:
            print("🔃 [play_selected_video] Switching video, saving current timestamp...")  # DEBUG
            self.save_current_video_timestamp()

        # ✅ Set current context
        self.current_video_title = new_title
        self.current_video_url = new_video_url
        self.current_video_id = new_video_id

        # ✅ Get internal DB IDs
        c.execute("SELECT id FROM videos WHERE youtube_id = ?", (self.current_video_id,))
        video_result = c.fetchone()
        c.execute("SELECT id FROM playlists WHERE id = ?", (self.current_playlist_id,))
        playlist_result = c.fetchone()

        if not video_result or not playlist_result:
            print("❌ [play_selected_video] Could not resolve video/playlist IDs.")  # DEBUG
            return

        video_db_id = video_result[0]
        playlist_db_id = playlist_result[0]

        # ✅ Get or create key_id
        key_id = get_or_create_key_id(video_db_id, playlist_db_id)
        print(f"🔁 [play_selected_video] Using key_id: {key_id}")  # DEBUG

        # ✅ Load saved notes
        try:
            c.execute("SELECT id FROM videos WHERE youtube_id = ?", (self.current_video_id,))
            video_result = c.fetchone()
            c.execute("SELECT id FROM playlists WHERE id = ?", (self.current_playlist_id,))
            playlist_result = c.fetchone()

            if not video_result or not playlist_result:
                print("❌ [callback] Could not fetch video_id or playlist_id from DB")  # DEBUG
                return

            video_db_id = video_result[0]
            playlist_db_id = playlist_result[0]
            print(f"📦 video_db_id = {video_db_id}, playlist_db_id = {playlist_db_id}")


            key_id = get_or_create_key_id(video_db_id, playlist_db_id)
            print(f"🧠 key_id for this video = {key_id}")
            c.execute("SELECT content_html FROM Complete_Notes WHERE key_id = ? ORDER BY last_updated DESC LIMIT 1", (key_id,))
            if note_result:
                print("📝 Note loaded from Complete_Notes")
            else:
                print("📭 No note found for this key_id")

            note_result = c.fetchone()
            if note_result:
                html = note_result[0]
                self.notes.setHtml(html)
                print("📝 Loaded saved note for this video.")  # DEBUG
            else:
                self.notes.clear()
        except Exception as e:
            print("❌ Failed to load notes:", e)

        # ✅ Load last playback position
        c.execute("SELECT last_position_seconds FROM LastPlayback WHERE key_id = ?", (key_id,))
        res = c.fetchone()
        if res:
            print(f"⏩ Found resume time: {res[0]} seconds")
        else:
            print("🔰 No resume time found.")

        start_seconds = res[0] if res else 0

        # ✅ Load video with resume timestamp
        video_base_url = f"https://www.youtube.com/watch?v={self.current_video_id}"
        video_url_with_time = f"{video_base_url}?t={start_seconds}" if start_seconds > 0 else video_base_url
        self.video_player.load(QUrl(video_url_with_time))
        print(f"🎥 Final YouTube URL: {video_url_with_time}")


        # ✅ Reconnect loadFinished signal
        if self.resume_prompt_connected:
            try:
                self.video_player.page().loadFinished.disconnect(self.check_saved_video_position)
            except Exception:
                pass

        self.video_player.page().loadFinished.connect(self.check_saved_video_position)
        self.resume_prompt_connected = True


    def save_current_video_timestamp(self):
        if not all([self.current_video_id, self.current_playlist_id]):
            print("❌ [save_current_video_timestamp] Missing video ID or playlist ID.")  # DEBUG
            return

        js = """
            (function() {
                var player = document.querySelector('video');
                return player ? Math.floor(player.currentTime) : 0;
            })();
        """

        def callback(seconds):
            print(f"⏳ [callback] JavaScript returned current time: {seconds} sec")  # DEBUG
        
            try:
                if seconds > 0:
                    print(f"🎯 Current playlist ID: {self.current_playlist_id}")
                    print(f"🎯 Current video ID: {self.current_video_id}")
                    # Get internal DB ids
                    # 🔍 Get DB IDs
                    c.execute("SELECT id FROM videos WHERE youtube_id = ?", (self.current_video_id,))
                    video_result = c.fetchone()
                    c.execute("SELECT id FROM playlists WHERE id = ?", (self.current_playlist_id,))
                    playlist_result = c.fetchone()

                    if not video_result or not playlist_result:
                        print("❌ [save_current_video_timestamp] Could not resolve DB IDs")
                        return

                    video_db_id = video_result[0]
                    playlist_db_id = playlist_result[0]

                    # 🔑 Get key_id
                    key_id = get_or_create_key_id(video_db_id, playlist_db_id)
                    print(f"🔑 [save_current_video_timestamp] key_id = {key_id}")


                    # Save time as seconds and formatted string
                    mins, secs = divmod(seconds, 60)
                    hours, mins = divmod(mins, 60)
                    time_str = f"{hours:02}:{mins:02}:{secs:02}"

                    c.execute("""
                        INSERT OR REPLACE INTO LastPlayback (key_id, last_position_seconds, last_position_str)
                        VALUES (?, ?, ?)
                    """, (key_id, seconds, time_str))
                    conn.commit()

            except Exception as e:
                print("❌ [callback] Error saving LastPlayback:", e)  # DEBUG
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
        print("🛠️ Timestamps button clicked")
        if not self.current_video_id or not self.current_playlist_id:
            QMessageBox.warning(self, "No video", "No video is currently loaded.")
            return

        video_db_id = self.get_video_db_id(self.current_video_id)
        
        try:
            c.execute('''
                SELECT timestamp_seconds, created_at FROM video_timestamps
                WHERE playlist_id = ? AND video_id = ?
                ORDER BY timestamp_seconds
            ''', (self.current_playlist_id, video_db_id))
            timestamps = c.fetchall()
        except Exception as e:
            QMessageBox.critical(self, "Database Error", str(e))
            return

        if not timestamps:
            QMessageBox.information(self, "No Timestamps", "No timestamps saved for this video.")
            return

        # 📁 Determine folder structure
        try:
            c.execute("""
                SELECT p.playlist_url, v.title 
                FROM playlists p
                JOIN videos v ON v.youtube_id = ?
                WHERE p.id = ?
            """, (self.current_video_id, self.current_playlist_id))
            result = c.fetchone()
            playlist_url, video_title = result if result else (None, None)
        except Exception as e:
            QMessageBox.critical(self, "Database Error", str(e))
            return

        safe_playlist = re.sub(r'[\\/*?:"<>|]', "", f"Playlist_{self.current_playlist_id}" if not playlist_url else "Unnamed_Playlist")
        safe_video = re.sub(r'[\\/*?:"<>|]', "", video_title)
        base_folder = os.path.join("ScreenShot", safe_playlist, safe_video)

        # Create the base folder if it doesn't exist
        os.makedirs(base_folder, exist_ok=True)

        # 🪟 Dialog UI
        dlg = QtWidgets.QDialog(self)
        dlg.setWindowTitle("⏳ Saved Timestamps with Screenshots")
        dlg.resize(600, 500)

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        layout = QVBoxLayout(container)

        for seconds, created_at in timestamps:
            mins, secs = divmod(seconds, 60)
            time_str = f"[{mins:02}:{secs:02}]"
            filename = f"{safe_video}_{seconds}.png"
            full_path = os.path.join(base_folder, filename)

            row = QWidget()
            row_layout = QHBoxLayout(row)

            label = QLabel(f"{time_str}  (Saved at {created_at})")
            row_layout.addWidget(label)

            if os.path.exists(full_path):
                # 🖼️ Show thumbnail preview
                pixmap = QtGui.QPixmap(full_path).scaledToWidth(120, Qt.SmoothTransformation)
                preview = QLabel()
                preview.setPixmap(pixmap)
                row_layout.addWidget(preview)

                # 🔗 Open screenshot button
                open_btn = QPushButton("Open")
                open_btn.clicked.connect(lambda _, path=full_path: QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(path)))
                row_layout.addWidget(open_btn)

                # 📂 Open folder button
                folder_btn = QPushButton("Show Folder")
                folder_btn.clicked.connect(lambda _, path=base_folder: QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(path)))
                row_layout.addWidget(folder_btn)

            layout.addWidget(row)

        container.setLayout(layout)
        scroll.setWidget(container)
        main_layout = QVBoxLayout(dlg)
        main_layout.addWidget(scroll)

        dlg.exec_()  # Show the dialog

    def save_note(self):
        print("💾 [save_note] Attempting to save current note...")

        if not all([self.current_video_id, self.current_playlist_id]):
            QMessageBox.warning(self, "Error", "No video selected")
            return

        note = self.notes.toPlainText().strip()
        if not note:
            QMessageBox.warning(self, "Empty Note", "Cannot save empty note")
            print("⚠️ [save_note] Note is empty, skipping save.")
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
            
            # 🔁 Also save HTML content to database
            from datetime import datetime
            html = self.notes.toHtml()

            # Resolve DB IDs
            c.execute("SELECT id FROM videos WHERE youtube_id = ?", (self.current_video_id,))
            video_result = c.fetchone()
            c.execute("SELECT id FROM playlists WHERE id = ?", (self.current_playlist_id,))
            playlist_result = c.fetchone()

            if not video_result or not playlist_result:
                print("❌ [save_note] Could not resolve video/playlist DB IDs")
                return

            video_db_id = video_result[0]
            playlist_db_id = playlist_result[0]
            key_id = get_or_create_key_id(video_db_id, playlist_db_id)
            print(f"🔑 [save_note] key_id = {key_id}")

            # Save to DB
            c.execute("""
                INSERT INTO Complete_Notes (key_id, video_title, content_html, last_updated)
                VALUES (?, ?, ?, ?)
            """, (key_id, video_title, html, datetime.now().isoformat()))
            conn.commit()

            print("✅ [save_note] Note also saved to DB table Complete_Notes.")


        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save note:\n{e}")
 
    def open_screenshot_link(self, url):
        path = url.toLocalFile()
        if os.path.exists(path):
            QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(path))
        else:
            QMessageBox.warning(self, "File Not Found", f"The screenshot file was not found:\n{path}")

    
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

    def capture_video_screenshot(self):
        if not all([self.current_video_id, self.current_playlist_id]):
            QMessageBox.warning(self, "Error", "No video loaded")
            return

        # 🕒 Grab timestamp from player
        js = "Math.floor(document.querySelector('video')?.currentTime || 0);"

        def handle_time(seconds):
            try:
                if seconds is None:
                    raise ValueError("Couldn't fetch video time")

                # 🧼 Prepare clean names
                c.execute("""
                    SELECT p.playlist_url, v.title 
                    FROM playlists p
                    JOIN videos v ON v.youtube_id = ?
                    WHERE p.id = ?
                """, (self.current_video_id, self.current_playlist_id))
                result = c.fetchone()
                playlist_name, video_title = result if result else ("Unknown", "Untitled")
                
                safe_playlist = re.sub(r'[\\/*?:"<>|]', "", f"Playlist_{self.current_playlist_id}" if not playlist_name else "Unnamed_Playlist")
                safe_video = re.sub(r'[\\/*?:"<>|]', "", video_title)

                folder = os.path.join("ScreenShot", safe_playlist, safe_video)
                os.makedirs(folder, exist_ok=True)

                screenshot_name = f"{safe_video}_{seconds}.png"
                filepath = os.path.join(folder, screenshot_name)

                # 📸 Take screenshot of video player only
                pixmap = self.video_player.grab()
                pixmap.save(filepath)

                # 🗂️ Save to DB (re-use timestamp logic)
                c.execute("""
                    INSERT INTO video_timestamps (playlist_id, video_id, timestamp_seconds)
                    VALUES (?, ?, ?)
                """, (self.current_playlist_id, self.get_video_db_id(self.current_video_id), seconds))
                conn.commit()

                # ✅ Insert screenshot link into note editor
                mins, secs = divmod(seconds, 60)
                timestamp_text = f"[{mins:02}:{secs:02}]"
                screenshot_html = f"{timestamp_text}: <a href='file:///{os.path.abspath(filepath)}'>📷 Screenshot</a></br>"

                # self.notes.moveCursor(QtGui.QTextCursor.End)
                # self.notes.insertHtml(screenshot_html)
                # Get current content
                cursor = self.notes.textCursor()
                cursor.movePosition(QtGui.QTextCursor.End)

                # 1. Insert the screenshot link
                cursor.insertHtml(screenshot_html)

                # 2. Insert an invisible "end of anchor" marker
                cursor.insertText("\uFEFF")  # Zero-width no-break space
                cursor.setCharFormat(QtGui.QTextCharFormat())  # Reset format

                # 3. Add a space for separation (optional)
                cursor.insertText(" ")

                # 4. Ensure cursor is at end with clean format
                cursor.movePosition(QtGui.QTextCursor.End)
                default_format = QtGui.QTextCharFormat()
                default_format.setAnchor(False)
                cursor.setCharFormat(default_format)
                self.notes.setTextCursor(cursor)


                QMessageBox.information(self, "Saved", f"Screenshot saved:\n{filepath}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to capture screenshot:\n{e}")

        # Get current time from video via JS
        self.video_player.page().runJavaScript(js, handle_time)

    def show_screenshots_for_current_video(self):
        if not self.current_video_id or not self.current_playlist_id:
            QMessageBox.warning(self, "No video", "No video is currently loaded.")
            return

        video_db_id = self.get_video_db_id(self.current_video_id)
        c.execute('''
            SELECT timestamp_seconds FROM video_timestamps
            WHERE playlist_id = ? AND video_id = ?
            ORDER BY timestamp_seconds
        ''', (self.current_playlist_id, video_db_id))
        timestamps = c.fetchall()

        if not timestamps:
            QMessageBox.information(self, "No Screenshots", "No screenshots saved for this video.")
            return

        # 🎯 Build screenshot path
        c.execute("""
            SELECT p.playlist_url, v.title 
            FROM playlists p
            JOIN videos v ON v.youtube_id = ?
            WHERE p.id = ?
        """, (self.current_video_id, self.current_playlist_id))
        result = c.fetchone()
        playlist_url, video_title = result if result else (None, None)

        safe_playlist = re.sub(r'[\\/*?:"<>|]', "", f"Playlist_{self.current_playlist_id}" if not playlist_url else "Unnamed_Playlist")
        safe_video = re.sub(r'[\\/*?:"<>|]', "", video_title)
        base_folder = os.path.join("ScreenShot", safe_playlist, safe_video)

        # 🪟 UI Dialog
        dlg = QtWidgets.QDialog(self)
        dlg.setWindowTitle("📷 Saved Screenshots")
        dlg.resize(500, 400)

        layout = QVBoxLayout()
        list_widget = QListWidget()

        for (seconds,) in timestamps:
            filename = f"{safe_video}_{seconds}.png"
            full_path = os.path.join(base_folder, filename)

            if os.path.exists(full_path):
                mins, secs = divmod(seconds, 60)
                item_text = f"[{mins:02}:{secs:02}] - {filename}"
                list_item = QListWidgetItem(item_text)

                # 📎 Add buttons inside item
                btn_open = QPushButton("Open")
                btn_open.clicked.connect(lambda _, path=full_path: QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(path)))

                btn_folder = QPushButton("Show Folder")
                btn_folder.clicked.connect(lambda _, path=base_folder: QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(path)))

                # Composite widget
                row_widget = QWidget()
                row_layout = QHBoxLayout(row_widget)
                row_layout.addWidget(QLabel(item_text))
                row_layout.addWidget(btn_open)
                row_layout.addWidget(btn_folder)
                row_layout.setContentsMargins(5, 2, 5, 2)

                item = QListWidgetItem()
                item.setSizeHint(row_widget.sizeHint())
                list_widget.addItem(item)
                list_widget.setItemWidget(item, row_widget)

        layout.addWidget(list_widget)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dlg.close)
        layout.addWidget(close_btn, alignment=Qt.AlignRight)

        dlg.setLayout(layout)
        dlg.exec_()

    def insert_custom_table(self):
        rows, ok1 = QtWidgets.QInputDialog.getInt(self, "Table Rows", "Enter number of rows:", 2, 1, 10)
        if not ok1: return
        cols, ok2 = QtWidgets.QInputDialog.getInt(self, "Table Columns", "Enter number of columns:", 2, 1, 10)
        if not ok2: return

        cursor = self.notes.textCursor()
        table_format = QtGui.QTextTableFormat()
        table_format.setBorder(1)
        table_format.setCellPadding(4)
        table_format.setCellSpacing(0)
        cursor.insertTable(rows, cols, table_format)

    def insert_hyperlink(self):
        url, ok = QtWidgets.QInputDialog.getText(self, "Insert Link", "Enter URL:")
        if ok and url:
            cursor = self.notes.textCursor()
            text = cursor.selectedText() or "Link"
            html = f'<a href="{url}" style="color:#0066cc;text-decoration:underline;">{text}</a>'
            cursor.insertHtml(html)

    def insert_image(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Insert Image", "", "Images (*.png *.jpg *.jpeg *.bmp *.gif)")
        if path:
            cursor = self.notes.textCursor()
            cursor.insertHtml(f'<img src="file:///{path}" width="300">')

    def insert_file_link(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Insert File", "", "All Files (*.*)")
        if path:
            name = os.path.basename(path)
            cursor = self.notes.textCursor()
            cursor.insertHtml(f'<a href="file:///{path}" style="color:#0066cc;">📄 {name}</a></br>')

    def enable_loop_js(self):
        js = """
            var video = document.querySelector('video');
            if (video) video.loop = true;
        """
        self.video_player.page().runJavaScript(js)
        print("🔁 Full video loop ENABLED")

    def disable_loop_js(self):
        js = """
            var video = document.querySelector('video');
            if (video) video.loop = false;
        """
        self.video_player.page().runJavaScript(js)
        print("⏹️ Full video loop DISABLED")

def get_or_create_key_id(video_id, playlist_id):
    """Returns the key_id if exists, else creates and returns a new one"""
    try:
        c.execute("SELECT key_id FROM VideoKeys WHERE video_id = ? AND playlist_id = ?", (video_id, playlist_id))
        result = c.fetchone()
        if result:
            return result[0]
        
        # Create new key_id (use hash of video+playlist or UUID)
        import uuid
        key_id = uuid.uuid4().hex  # Unique 32-char hash
        c.execute("INSERT INTO VideoKeys (video_id, playlist_id, key_id) VALUES (?, ?, ?)", (video_id, playlist_id, key_id))
        conn.commit()
        print(f"🆕 [get_or_create_key_id] Created new key_id: {key_id}")
        return key_id

    except Exception as e:
        print(f"❌ [get_or_create_key_id] Error: {e}")
        return None

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

