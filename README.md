# Music Player CLI

A command-line music player that allows you to search for songs on Spotify, manage your local music library, and listen to music directly from your terminal.

## Features

- Search for songs on Spotify.
- Add songs to your local library.
- Songs are automatically downloaded from YouTube Music.
- Create and manage playlists.
- View your library of liked songs, recently played songs, and albums.
- Keyboard shortcuts for easy navigation and control.
- Rich terminal UI with progress bars and tables.

## Setup

1. **Clone the repository.**
2. **Install the required Python packages:**
   ```
   pip install -r requirements.txt
   ```
3. **Set up your Spotify API credentials:**
   - Create a `.env` file in the project root with the following content:
     ```
     SPOTIPY_CLIENT_ID='your-client-id'
     SPOTIPY_CLIENT_SECRET='your-client-secret'
     ```
   - You can get your credentials from the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard).
4. **Run the database synchronization script:**
   ```
   python sync_database.py
   ```
5. **Run the main application:**
   ```
   python main.py
   ```

## Key Bindings

### Home Screen

- `ctrl+r`: Ends the program.
- `ctrl+d`: Remove the selected song from queue.
- `ctrl+p`: Pause / Unpause current song.
- `ctrl+a`: Like the currently playing song.
- `ctrl+s`: Search for songs / albums.
- `ctrl+l`: Open your library.
- `ctrl+v`: Toggle loop.
- `ctrl+w`: Toggle shuffle.
- `ctrl+m`: Play the selected song in the queue.
- `Up/Down`: Navigate through the queue.
- `Right`: Play next song.

### Search Screen

- `ctrl+r`: Returns to the home screen.
- `Enter`: Queue a song / album.

### Library Screen

- `ctrl+r`: Return to home screen.
- `ctrl+d`: Delete the selected song from playlist or the selected playlist.
- `ctrl+q`: Queue the seleted album / playlist / song.
- `ctrl+a`: Add song(s) to the selected playlist.
- `ctrl+n`: Create a new playlist.
- `Up/Down`: Navigate through albums / playlists.
- `Left/Right`: Switch between album and playist.
- `Enter`: Toggle Navigating through the selected album / playlist.
