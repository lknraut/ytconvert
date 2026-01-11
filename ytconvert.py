import customtkinter as ctk
from tkinter import filedialog, messagebox
import yt_dlp
import threading
import os

# --- Configuration & UI Theme ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class YouTubeDownloaderApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window Setup
        self.title("Modern YouTube Downloader")
        self.geometry("600x550")
        self.resizable(False, False)

        # State Variables
        self.download_folder = ""
        self.is_downloading = False

        # --- UI Layout ---
        self.create_widgets()

    def create_widgets(self):
        # Title
        self.title_label = ctk.CTkLabel(self, text="YouTube to MP3/MP4", font=("Roboto", 24, "bold"))
        self.title_label.pack(pady=20)

        # Link Input
        self.url_entry = ctk.CTkEntry(self, width=450, placeholder_text="Paste YouTube Link Here...")
        self.url_entry.pack(pady=10)

        # Format Selection (Tabs)
        self.format_label = ctk.CTkLabel(self, text="Select Format:", font=("Roboto", 14))
        self.format_label.pack(pady=(10, 0))
        
        self.type_var = ctk.StringVar(value="mp4")
        self.radio_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.radio_frame.pack(pady=5)
        
        self.radio_mp4 = ctk.CTkRadioButton(self.radio_frame, text="MP4 (Video)", variable=self.type_var, value="mp4", command=self.toggle_resolution_visibility)
        self.radio_mp4.pack(side="left", padx=10)
        
        self.radio_mp3 = ctk.CTkRadioButton(self.radio_frame, text="MP3 (Audio)", variable=self.type_var, value="mp3", command=self.toggle_resolution_visibility)
        self.radio_mp3.pack(side="left", padx=10)

        # Resolution Dropdown (Only for MP4)
        self.res_var = ctk.StringVar(value="1080p")
        self.res_menu = ctk.CTkOptionMenu(self, values=["2160p", "1440p", "1080p", "720p", "480p", "360p"], variable=self.res_var)
        self.res_menu.pack(pady=10)

        # Save Location Button
        self.save_btn = ctk.CTkButton(self, text="Choose Save Folder", command=self.select_folder, fg_color="#555555", hover_color="#333333")
        self.save_btn.pack(pady=10)
        
        self.path_label = ctk.CTkLabel(self, text="No folder selected", text_color="gray", font=("Roboto", 12))
        self.path_label.pack(pady=(0, 10))

        # Progress Section
        self.progress_bar = ctk.CTkProgressBar(self, width=400)
        self.progress_bar.set(0)
        self.progress_bar.pack(pady=20)

        self.status_label = ctk.CTkLabel(self, text="Ready", font=("Roboto", 12))
        self.status_label.pack(pady=(0, 10))

        # Action Buttons
        self.button_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.button_frame.pack(pady=20)

        self.download_btn = ctk.CTkButton(self.button_frame, text="Download", command=self.start_download_thread, width=150, height=40, font=("Roboto", 16, "bold"))
        self.download_btn.pack(side="left", padx=10)

        self.reset_btn = ctk.CTkButton(self.button_frame, text="Next Convert", command=self.reset_ui, width=150, height=40, fg_color="#DB3E39", hover_color="#A62B27")
        self.reset_btn.pack(side="left", padx=10)

    def toggle_resolution_visibility(self):
        if self.type_var.get() == "mp3":
            self.res_menu.configure(state="disabled", fg_color="gray")
        else:
            self.res_menu.configure(state="normal", fg_color=["#3B8ED0", "#1F6AA5"]) # Default blue

    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.download_folder = folder
            self.path_label.configure(text=f"Saving to: {os.path.basename(folder)}", text_color="white")

    def reset_ui(self):
        self.url_entry.delete(0, 'end')
        self.progress_bar.set(0)
        self.status_label.configure(text="Ready", text_color="white")
        self.download_btn.configure(state="normal", text="Download")
        self.is_downloading = False

    def progress_hook(self, d):
        if d['status'] == 'downloading':
            try:
                p = d.get('_percent_str', '0%').replace('%','')
                self.progress_bar.set(float(p) / 100)
                self.status_label.configure(text=f"Downloading: {d.get('_percent_str')} | ETA: {d.get('_eta_str', '?')}s")
            except:
                pass
        elif d['status'] == 'finished':
            self.status_label.configure(text="Conversion in progress... (This may take a moment)", text_color="orange")
            self.progress_bar.set(1)

    def start_download_thread(self):
        if self.is_downloading: return
        
        url = self.url_entry.get()
        if not url:
            messagebox.showerror("Error", "Please paste a YouTube link first.")
            return
        if not self.download_folder:
            messagebox.showerror("Error", "Please select a save folder.")
            return

        self.is_downloading = True
        self.download_btn.configure(state="disabled", text="Running...")
        
        # Run in separate thread to prevent UI freezing
        threading.Thread(target=self.download_logic, args=(url,)).start()

    def download_logic(self, url):
        try:
            format_type = self.type_var.get()
            resolution = self.res_var.get().replace('p', '')
            
            ydl_opts = {
                'outtmpl': f'{self.download_folder}/%(title)s.%(ext)s',
                'progress_hooks': [self.progress_hook],
                'noplaylist': True,
            }

            if format_type == "mp3":
                ydl_opts.update({
                    'format': 'bestaudio/best',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }],
                })
            else: # MP4
                # Download best video up to selected resolution + best audio
                ydl_opts.update({
                    'format': f'bestvideo[height<={resolution}]+bestaudio/best[height<={resolution}]',
                    'merge_output_format': 'mp4',
                })

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            self.status_label.configure(text="Success! Download Complete.", text_color="#2CC985")
            messagebox.showinfo("Success", "Download and Conversion Complete!")

        except Exception as e:
            self.status_label.configure(text="Error occurred.", text_color="red")
            retry = messagebox.askretrycancel("Error", f"Download failed:\n{str(e)}\n\nDo you want to retry?")
            if retry:
                self.reset_ui() # Reset UI but keep the URL effectively if user wants to re-paste or just click download again (logic reset)
                self.is_downloading = False
                self.download_btn.configure(state="normal", text="Retry Download")
                return

        self.is_downloading = False
        self.download_btn.configure(state="normal", text="Download")

if __name__ == "__main__":
    app = YouTubeDownloaderApp()
    app.mainloop()
