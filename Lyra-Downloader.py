import os
import sys
import requests
import threading
import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser
import yt_dlp
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import re

# ---------- SAFE FILE/FOLDER NAME ----------
def safe_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "", name)

# ---------- DEBUG LOGGER ----------
def log(app, message):
    app.debug_box.insert(tk.END, message + "\n")
    app.debug_box.see(tk.END)

# ---------- LYRA API ----------
def get_all_tracks(app, playlist_url):
    try:
        playlist_id = playlist_url.rstrip("/").split("/")[-1]
        log(app, f"[INFO] Playlist ID: {playlist_id}")
    except:
        log(app, "[ERROR] Invalid playlist URL")
        return [], None

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://listen.lyramusic.app/",
        "Accept": "application/json"
    }

    # STEP 1: Metadata
    meta_url = f"https://api.lyramusic.app/share/playlist/{playlist_id}"
    log(app, f"[REQUEST] {meta_url}")

    res = requests.get(meta_url, headers=headers)
    log(app, f"[STATUS] {res.status_code}")

    if res.status_code != 200:
        log(app, res.text[:500])
        return [], None

    data = res.json()
    real_id = data.get("itemId")
    playlist_name = safe_filename(data.get("name") or "Lyra Playlist")

    if not real_id:
        log(app, "[ERROR] Could not find itemId")
        return [], None

    log(app, f"[INFO] Playlist Name: {playlist_name}")
    log(app, f"[INFO] Real ID: {real_id}")

    # ---------- SAFE DOWNLOAD FOLDER ----------
    script_dir = os.path.dirname(os.path.abspath(__file__))
    download_dir = os.path.join(script_dir, playlist_name)
    try:
        os.makedirs(download_dir, exist_ok=True)
    except PermissionError:
        # Fallback to user Downloads folder
        user_downloads = os.path.join(os.path.expanduser("~"), "Downloads")
        download_dir = os.path.join(user_downloads, playlist_name)
        os.makedirs(download_dir, exist_ok=True)
        log(app, f"[INFO] Using Downloads folder instead: {download_dir}")

    # STEP 2: Tracks
    all_tracks = []
    offset = 0
    while True:
        url = f"https://api.lyramusic.app/share/playlist/{real_id}/content?offset={offset}&limit=100"
        log(app, f"[REQUEST] {url}")

        res = requests.get(url, headers=headers)
        log(app, f"[STATUS] {res.status_code}")
        if res.status_code != 200:
            log(app, res.text[:500])
            break

        data = res.json()
        items = data.get("tracks", [])
        if not items:
            break

        for item in items:
            try:
                title = item.get("name")
                artists = ", ".join(
                    a.get("name") for a in item.get("artists", []) if a.get("name")
                )
                if title and artists:
                    all_tracks.append((title, artists))
                    log(app, f"[TRACK] {artists} - {title}")
            except Exception as e:
                log(app, f"[ERROR] {e}")

        offset += 100

    log(app, f"[INFO] Total tracks: {len(all_tracks)}")
    return all_tracks, download_dir

# ---------- YOUTUBE SEARCH ----------
def search_youtube(query):
    ydl_opts = {"quiet": True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(f"ytsearch5:{query}", download=False)
            for entry in result["entries"]:
                title = entry["title"].lower()
                channel = entry.get("channel", "").lower()
                if "official audio" in title or "topic" in channel:
                    return entry["webpage_url"]
            return result["entries"][0]["webpage_url"]
    except Exception as e:
        return f"Error: {e}"

# ---------- MP3 DOWNLOAD ----------
def download_mp3(url, download_dir):
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": os.path.join(download_dir, "%(title)s.%(ext)s"),
        "quiet": True,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

# ---------- GUI ----------
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Lyra → MP3 Downloader (Safe)")
        self.root.geometry("900x650")

        self.url_entry = tk.Entry(root, width=100)
        self.url_entry.pack(pady=5)

        self.fetch_btn = tk.Button(root, text="Fetch + Download MP3s", command=self.start_fetch)
        self.fetch_btn.pack(pady=5)

        self.status = tk.Label(root, text="Idle")
        self.status.pack()

        self.tree = ttk.Treeview(root, columns=("Song", "Link"), show="headings")
        self.tree.heading("Song", text="Song")
        self.tree.heading("Link", text="YouTube Link")
        self.tree.column("Song", width=350)
        self.tree.column("Link", width=500)
        self.tree.pack(fill="both", expand=True)

        self.tree.bind("<Double-1>", self.open_link)

        tk.Label(root, text="Debug Console:").pack()
        self.debug_box = tk.Text(root, height=12, bg="black", fg="lime")
        self.debug_box.pack(fill="both", expand=True)

    def start_fetch(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("Error", "Enter a playlist URL")
            return
        self.debug_box.delete("1.0", tk.END)
        for row in self.tree.get_children():
            self.tree.delete(row)
        threading.Thread(target=self.process, args=(url,), daemon=True).start()

    def process(self, url):
        self.update_status("Fetching playlist...")
        tracks, download_dir = get_all_tracks(self, url)
        if not tracks:
            self.update_status("No tracks found or permission error.")
            return

        self.update_status(f"{len(tracks)} tracks found. Searching YouTube...")

        results = [None] * len(tracks)
        batch_size = 20

        for start in range(0, len(tracks), batch_size):
            batch = tracks[start:start + batch_size]
            with ThreadPoolExecutor(max_workers=len(batch)) as executor:
                futures = {
                    executor.submit(search_youtube, f"{artist} {title} official audio"): i + start
                    for i, (title, artist) in enumerate(batch)
                }
                for future in as_completed(futures):
                    i = futures[future]
                    try:
                        results[i] = future.result()
                    except Exception as e:
                        results[i] = f"Error: {e}"
                    self.update_status(f"{i+1}/{len(tracks)} found")
            time.sleep(0.3)

        self.update_status("Downloading MP3s...")

        for i, ((title, artist), link) in enumerate(zip(tracks, results)):
            self.tree.insert("", "end", values=(f"{artist} - {title}", link))
            try:
                download_mp3(link, download_dir)
                log(self, f"[DOWNLOADED] {artist} - {title}")
            except Exception as e:
                log(self, f"[ERROR] {e}")
            self.update_status(f"{i+1}/{len(tracks)} downloaded")

        self.update_status(f"Finished! Saved to: {download_dir}")

    def update_status(self, text):
        self.status.config(text=text)

    def open_link(self, event):
        selected = self.tree.selection()
        if selected:
            item = self.tree.item(selected[0])
            webbrowser.open(item["values"][1])

# ---------- RUN ----------
if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
