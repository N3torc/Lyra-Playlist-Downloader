# Lyra → MP3 Downloader

Download songs from Lyra Music playlists and convert them to MP3. Playlist tracks are automatically organized in a folder named after the playlist. No administrator permissions are required.

---

## Features

- Fetch playlists directly from Lyra Music
- Search YouTube for official audio automatically
- Download and convert songs to MP3 using `yt-dlp` and `ffmpeg`
- Organize downloads in playlist-named folders
- Debug console for monitoring requests and track info
- Parallel YouTube search for faster results

---

## How It Works

1. **Fetch Playlist Data:**  
   The tool takes a Lyra playlist URL and uses Lyra’s public API to get the playlist metadata and track list.

2. **Extract Track Info:**  
   For each track, it gets the **song name** and **artist**.  

3. **Search YouTube:**  
   It automatically searches YouTube for the **official audio version** using the track’s name and artist. The tool prioritizes official channels and audio releases.

4. **Download MP3:**  
   Using `yt-dlp` and `ffmpeg`, the tool downloads the track and converts it to an MP3 file. Each song is saved in a folder named after the playlist.

5. **Parallel Processing:**  
   Multiple YouTube searches are performed in parallel to speed up large playlists. Downloads are processed sequentially but can be enhanced for full parallelism if needed.

6. **Debug Console:**  
   A built-in console logs all API calls, track info, YouTube links, and errors for full transparency.

---

## Installation

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/LyraDownloader.git
cd LyraDownloader
