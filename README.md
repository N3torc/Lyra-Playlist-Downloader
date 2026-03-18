# Lyra → MP3 Downloader

This is a Python tool to download all songs from a Lyra Music playlist and convert them into MP3 files. The downloaded songs are organized in a folder named after the playlist. No administrator permissions are required.

---

## Features

- Fetch playlists from Lyra Music
- Automatically organize songs in playlist-named folders
- Search YouTube for **official audio** tracks
- Download and convert tracks to MP3 using `yt-dlp` and `ffmpeg`
- Parallel YouTube searching for faster results
- Built-in debug console for API requests and track info

---

## Requirements

- Python 3.8+
- `yt-dlp` Python package
- `requests` Python package
- **FFmpeg** installed and available in system PATH

Install Python packages:

```bash
pip install -r requirements.txt
