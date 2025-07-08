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

        self.timestamp_btn = QPushButton("⏱ Insert Timestamp")
        self.timestamp_btn.setEnabled(False)
        self.buttons.addWidget(self.timestamp_btn)

        self.save_btn = QPushButton("💾 Save Note")
        self.save_btn.setEnabled(False)
        self.buttons.addWidget(self.save_btn)

        # ✅ Add to layout (no gap)
        self.layout.addWidget(self.button_row)