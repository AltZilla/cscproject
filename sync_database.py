import sqlite3
import csv

conn = sqlite3.connect('music.db')
cur = conn.cursor()
    
def sync_db():
    cur.execute("""CREATE TABLE IF NOT EXISTS songs (
                    song_id INT NOT NULL PRIMARY KEY,
                    album_id INT,
                    title VARCHAR(100) NOT NULL,
                    artist VARCHAR(100) NOT NULL,
                    liked TINYINT(1) NOT NULL,
                    release_date DATE,
                    duration INT,
                    spotify_id VARCHAR(100)
                )""")
    
    cur.execute("""CREATE TABLE IF NOT EXISTS albums (
                    album_id INT NOT NULL PRIMARY KEY,
                    album_name VARCHAR(100) NOT NULL,
                    artist VARCHAR(100) NOT NULL,
                    liked TINYINT(1) NOT NULL,
                    created_at DATE
                )""")
    
    cur.execute("""CREATE TABLE IF NOT EXISTS playlists (
                    playlist_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    playlist_name VARCHAR(100) NOT NULL
                )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS playlistsongs (
                    song_id INT NOT NULL,
                    playlist_id INT NOT NULL
                )""")
    
    cur.execute("""CREATE TABLE IF NOT EXISTS recentlyplayed (
                    song_id INT NOT NULL,
                    played_at DATETIME
                );""")
    
    with open("songs.csv") as f:
        with open("albums.csv") as f2:
            reader = csv.reader(f)
            reader2 = csv.reader(f2)
            
            for id, name, artist, liked, created in reader2:
                insert_query = "INSERT INTO albums VALUES (?, ?, ?, ?, ?)"
                cur.execute(insert_query, (int(id), name, artist, int(liked), created))
            
            for song_id, title, artist, liked, album, release_date, dur, spotify_id in reader:
                insert_query = "INSERT INTO songs VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
                cur.execute(insert_query, (int(song_id), int(album), title, artist, int(liked), release_date, int(dur), spotify_id))
            
        conn.commit()
sync_db()