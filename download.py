import os
import gi
import youtube_dl

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

class YouTubeDownloader(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="YouTube Downloader")
        self.set_border_width(10)
        self.set_default_size(500, 400)

        # URL input
        self.url_label = Gtk.Label(label="YouTube URL:")
        self.url_entry = Gtk.Entry()

        # Format selection
        self.format_label = Gtk.Label(label="Select Format:")
        self.format_combobox = Gtk.ComboBoxText()
        self.format_combobox.append_text('best')
        self.format_combobox.append_text('mp4')
        self.format_combobox.append_text('webm')
        self.format_combobox.append_text('mkv')
        self.format_combobox.append_text('flv')
        self.format_combobox.set_active(0)

        # Download type selection
        self.type_label = Gtk.Label(label="Download Type:")
        self.video_radio = Gtk.RadioButton.new_with_label_from_widget(None, "Video")
        self.audio_radio = Gtk.RadioButton.new_with_label_from_widget(self.video_radio, "Audio")
        self.playlist_radio = Gtk.RadioButton.new_with_label_from_widget(self.video_radio, "Playlist")
        self.video_radio.set_active(True)

        # Directory selection
        self.dir_label = Gtk.Label(label="Save Directory:")
        self.dir_entry = Gtk.Entry()
        self.dir_button = Gtk.Button(label="Browse")
        self.dir_button.connect("clicked", self.on_browse_clicked)

        # Download button
        self.download_button = Gtk.Button(label="Download")
        self.download_button.connect("clicked", self.download_video)

        # Status
        self.status_label = Gtk.Label(label="")
        
        # Progress bar
        self.progress_bar = Gtk.ProgressBar()

        # Layout
        grid = Gtk.Grid()
        grid.set_row_spacing(10)
        grid.set_column_spacing(10)
        grid.attach(self.url_label, 0, 0, 1, 1)
        grid.attach(self.url_entry, 1, 0, 2, 1)
        grid.attach(self.format_label, 0, 1, 1, 1)
        grid.attach(self.format_combobox, 1, 1, 2, 1)
        grid.attach(self.type_label, 0, 2, 1, 1)
        grid.attach(self.video_radio, 1, 2, 1, 1)
        grid.attach(self.audio_radio, 2, 2, 1, 1)
        grid.attach(self.playlist_radio, 3, 2, 1, 1)
        grid.attach(self.dir_label, 0, 3, 1, 1)
        grid.attach(self.dir_entry, 1, 3, 1, 1)
        grid.attach(self.dir_button, 2, 3, 1, 1)
        grid.attach(self.download_button, 0, 4, 3, 1)
        grid.attach(self.progress_bar, 0, 5, 3, 1)
        grid.attach(self.status_label, 0, 6, 3, 1)

        self.add(grid)

    def on_browse_clicked(self, widget):
        dialog = Gtk.FileChooserDialog(
            "Select Save Directory",
            self,
            Gtk.FileChooserAction.SELECT_FOLDER,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
        )
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.dir_entry.set_text(dialog.get_filename())
        dialog.destroy()

    def download_video(self, widget):
        url = self.url_entry.get_text()
        format_choice = self.format_combobox.get_active_text()
        download_type = "video" if self.video_radio.get_active() else "audio" if self.audio_radio.get_active() else "playlist"
        save_directory = self.dir_entry.get_text()

        if not url:
            self.show_message_dialog("Input Error", "Please enter a YouTube URL.")
            return

        if not save_directory:
            self.show_message_dialog("Input Error", "Please select a directory to save the file.")
            return

        def hook(d):
            if d['status'] == 'downloading':
                downloaded_bytes = d.get('downloaded_bytes', 0)
                total_bytes = d.get('total_bytes', 0)
                if total_bytes > 0:
                    percent_complete = downloaded_bytes / total_bytes
                    GLib.idle_add(self.progress_bar.set_fraction, percent_complete)

        ydl_opts = {
            'format': format_choice,
            'progress_hooks': [hook],
            'outtmpl': f'{save_directory}/%(title)s.%(ext)s'
        }

        if download_type == "audio":
            ydl_opts['format'] = 'bestaudio/best'
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        elif download_type == "playlist":
            ydl_opts['noplaylist'] = False
        else:
            ydl_opts['noplaylist'] = True

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            try:
                info_dict = ydl.extract_info(url, download=False)
                file_path = ydl.prepare_filename(info_dict)

                if os.path.exists(file_path):
                    if not self.confirm_replace(file_path):
                        self.status_label.set_text("Download Cancelled")
                        return

                self.status_label.set_text("Downloading...")
                ydl.download([url])
                self.status_label.set_text("Download Complete")
                GLib.idle_add(self.progress_bar.set_fraction, 1.0)
            except Exception as e:
                self.status_label.set_text("Error: " + str(e))

    def show_message_dialog(self, title, message):
        dialog = Gtk.MessageDialog(
            self, 0, Gtk.MessageType.INFO,
            Gtk.ButtonsType.OK, title
        )
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()

    def confirm_replace(self, file_path):
        dialog = Gtk.MessageDialog(
            self, 0, Gtk.MessageType.QUESTION,
            Gtk.ButtonsType.YES_NO, "File Exists"
        )
        dialog.format_secondary_text(f"{file_path} already exists. Do you want to replace it?")
        response = dialog.run()
        dialog.destroy()
        return response == Gtk.ResponseType.YES

if __name__ == "__main__":
    app = YouTubeDownloader()
    app.connect("destroy", Gtk.main_quit)
    app.show_all()
    Gtk.main()
