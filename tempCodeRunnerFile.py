    def save_note(self):
        if not self.current_video_id or not self.current_playlist_id:
            QMessageBox.warning(self, "Error", "No video selected")
            return

        note = self.notes.toPlainText().strip()
        if not note:
            QMessageBox.warning(self, "Empty Note", "Cannot save empty note.")
            return

        try:
            # Get playlist and video info from database
            c.execute("SELECT playlist_url FROM playlists WHERE id = ?", (self.current_playlist_id,))
            playlist_url = c.fetchone()[0]
            
            # Get playlist title
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                info = ydl.extract_info(playlist_url, download=False)
                playlist_title = info.get('title', 'Untitled Playlist')
            
            # Create paths
            safe_playlist_title = re.sub(r'[\\/*?:"<>|]', "", playlist_title)
            safe_video_title = re.sub(r'[\\/*?:"<>|]', "", self.current_video_title)
            note_folder = os.path.join("notes", safe_playlist_title, safe_video_title)
            os.makedirs(note_folder, exist_ok=True)
            
            # Generate filename with timestamp
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(note_folder, f"note_{timestamp}.txt")
            
            # Save note
            with open(filename, "w", encoding="utf-8") as f:
                f.write(note)
                
            QMessageBox.information(self, "Saved", f"Note saved to:\n{filename}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save note:\n{e}")