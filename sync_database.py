import mysql.connector as mysql
import csv

conn = mysql.connect(host='localhost', user='root', password='sample', database = 'project')

if conn.is_connected():
    cur = conn.cursor()
else:
    print("Failed to connect to MySQL server")
    exit() # this quits the program
    
    
def sync_db():
    cur.execute("""CREATE TABLE IF NOT EXISTS songs (
                    song_id INT NOT NULL PRIMARY KEY,
                    title VARCHAR(100) NOT NULL,
                    artist VARCHAR(100) NOT NULL,
                    liked TINYINT(1) NOT NULL,
                    album VARCHAR(100),
                    release_date DATE,
                    spotify_id VARCHAR(100)
                ); """)
    
    with open("songs.csv") as f:
        reader = csv.reader(f)
        
        for song_id, title, artist, liked, album, release_date, spotify_id in reader:
            insert_query = "INSERT INTO songs VALUES (%s, %s, %s, %s, %s, %s, %s)"
            cur.execute(insert_query, (int(song_id), title, artist, int(liked), album, release_date, spotify_id))
            
        conn.commit()
sync_db()