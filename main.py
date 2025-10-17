import sqlite3
import pygame
import time
import datetime
import keyboard
import random 
import os
import yt_dlp
from ytmusicapi import YTMusic
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

load_dotenv()

sp = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())

from rich.console import Console, Group
from rich.panel import Panel
from rich.live import Live
from rich.text import Text
from rich.align import Align
from rich.table import Table, box
from rich.layout import Layout
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn

console = Console()

live = None

pygame.init()
pygame.mixer.music.set_endevent(45)
pygame.mixer.music.set_volume(0.5)

conn = sqlite3.connect('music.db')
cur = conn.cursor()

currently_playing = None
queue = [] # This will have the structure [song_id, title, album, artist, liked, duration].
pressed_keys = []

paused = loop = shuffle = False

def handle_key_press(key):
    if keyboard.is_pressed("ctrl") and key.name != "ctrl":
        pressed_keys.append("ctrl+{}".format(key.name))
        
    elif key.name != "ctrl":
        pressed_keys.append(key.name)

keyboard.on_press(handle_key_press) # The handle_key_press(key) func will be called whenever a key is pressed.

def play_next_song():
    global currently_playing, paused
    paused = False
    
    if currently_playing:
        cur.execute("INSERT INTO recentlyplayed (song_id, played_at) VALUES(?, ?)", (currently_playing[0], datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        conn.commit()
        
    if shuffle == True:
        random.shuffle(queue)
    if loop == True and currently_playing != None:
        queue.append(currently_playing)
    if queue != []:
        song_data = queue.pop(0) # Get the first song
        song_id, title, album, artist, liked, duration, spotify_id = song_data
        song_path = f"songs/{song_id}.mp3"

        if not os.path.exists(song_path):
            search_query = f"{title} {artist}"
            if spotify_id:
                try:
                    track = sp.track(spotify_id)
                    search_query = f"{track['name']} {track['artists'][0]['name']}"
                except:
                    pass

            ytmusic = YTMusic()
            search_results = ytmusic.search(search_query, filter="songs")
            if search_results:
                video_id = search_results[0]['videoId']
                
                with Progress(
                    TextColumn("[bold blue]{task.description}", justify="right"),
                    BarColumn(bar_width=None),
                    "[progress.percentage]{task.percentage:>3.0f}%",
                    "•",
                    TimeRemainingColumn(),
                ) as progress:
                    task_id = progress.add_task("Downloading", total=None)

                    def my_hook(d):
                        if d['status'] == 'downloading':
                            total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate')
                            if total_bytes:
                                progress.update(task_id, total=total_bytes, completed=d['downloaded_bytes'])
                        if d['status'] == 'finished':
                            progress.update(task_id, completed=d.get('total_bytes'))

                    ydl_opts = {
                        'format': 'bestaudio/best',
                        'outtmpl': f"songs/{song_id}",
                        'progress_hooks': [my_hook],
                        'postprocessors': [{
                            'key': 'FFmpegExtractAudio',
                            'preferredcodec': 'mp3',
                            'preferredquality': '192',
                        }],
                    }
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        ydl.download([f"https://www.youtube.com/watch?v={video_id}"])

        try:
            pygame.mixer.music.load(song_path)
        except Exception as e:
            play_next_song()
            return
        pygame.mixer.music.play()
        currently_playing = song_data
    else:
        pygame.mixer.music.stop()
        currently_playing = None
        return False

def pause_unpause():
    global paused
    if paused:
        pygame.mixer.music.unpause()
    else:
        pygame.mixer.music.pause()
    paused = not paused
        
def queue_song(song_id):
    query = "SELECT songs.title, albums.album_name, songs.artist, songs.liked, duration, songs.spotify_id FROM albums, songs WHERE songs.album_id = albums.album_id AND songs.song_id = ?"
    cur.execute(query, (song_id,))

    title, album, artist, liked, duration, spotify_id = cur.fetchone()
    queue.append([song_id, title, album, artist, liked, duration, spotify_id])
    
    if currently_playing == None:
        play_next_song()
        
def like_song(song_id):
    # Check if the song is already liked
    cur.execute("SELECT liked FROM songs WHERE song_id = ?", (song_id,))
    result = cur.fetchone()

    liked = not result[0]  # Toggle the liked status
    cur.execute("UPDATE songs SET liked=? WHERE song_id=?", (int(liked), song_id))
    conn.commit()
    
    if currently_playing and currently_playing[0] == song_id:
        currently_playing[4] = liked
    for data in queue:
        if data[0] == song_id:
            data[4] = liked
    return liked

def like_album(album_id):
    # Check if the album is already liked
    cur.execute("SELECT liked FROM albums WHERE album_id = ?", (album_id,))
    result = cur.fetchone()

    liked = not result[0]  # Toggle the liked status
    cur.execute("UPDATE albums SET liked=? WHERE album_id=?", (int(liked), album_id))
    conn.commit()
    return liked

def create_playlist(name):
    cur.execute("INSERT INTO playlists (playlist_name) VALUES(?)", (name,))
    conn.commit()

def format_sec(seconds):
    seconds = int(seconds)
    min, sec = divmod(seconds, 60)
    if sec < 10:
        sec = "0" + str(sec)
    return "{}:{}".format(min, sec)

def chunk_list(lst, chunk_size = 10):
    """Split a list into smaller chunks of a specified size."""
    chunked = []
    for i in range(0, len(lst), chunk_size):
        chunk = lst[i:i + chunk_size]
        chunked.append(chunk)
    return chunked

def get_library_albums():
    cur.execute("SELECT songs.song_id, songs.title, songs.liked, songs.duration FROM albums, songs WHERE songs.album_id = albums.album_id AND songs.liked = 1")
    liked_songs = cur.fetchall()
    
    cur.execute("SELECT songs.song_id, songs.title, songs.liked, songs.duration, COUNT(songs.song_id) FROM songs, recentlyplayed WHERE songs.song_id = recentlyplayed.song_id GROUP BY songs.song_id ORDER BY COUNT(songs.song_id) DESC")
    recently_played = cur.fetchall()
    
    albums = [
            {'id': -2, 'name': "Liked Songs", "songs": liked_songs},
            {'id': -1, 'name': "Recently Played", "songs": recently_played}
        ]
    
    cur.execute("SELECT album_id, album_name FROM albums WHERE liked=1")
    details = cur.fetchall()
    for data in details:
        cur.execute("SELECT songs.song_id, songs.title, songs.liked, songs.duration FROM albums, songs WHERE songs.album_id = albums.album_id AND albums.album_id=?", (data[0],))
        songs = cur.fetchall()
        albums.append({'id': data[0], "name": data[1], "songs": songs})

    return albums

def get_all_playlists():
    playlists = []
    cur.execute("SELECT playlist_id, playlist_name FROM playlists")
    details = cur.fetchall()
    for data in details:
        cur.execute("SELECT songs.song_id, songs.title, songs.liked, songs.duration FROM songs, playlistsongs WHERE songs.song_id = playlistsongs.song_id AND playlistsongs.playlist_id=?", (data[0],))
        songs = cur.fetchall()
        playlists.append({'id': data[0], "name": data[1], "songs": songs})

    return playlists
    
def handle_input(current_input):
    changed = False
    for key in pressed_keys:
        if key == 'backspace':
            current_input = current_input[:-1]
            changed = True
        elif len(key) == 1:
            current_input += key
            changed = True
        elif key == "space":
            current_input += " "
            changed = True
    return current_input, changed
    
def handle_events():
    for event in pygame.event.get():
        if event.type == 45:
            play_next_song()
            
def within_range(index, start, end):
    """Wrap the given index within the specified range, if index is more than end value, place index at the start and if index is less than start, place index at end."""
    if index < start:
        index = end
    elif index > end:
        index = start

    return index

def show_commands(commands):
    table = Table(show_header=True, header_style="bold magenta", box = box.SIMPLE_HEAD, padding = (0, 3)) # padding = 3 spaces between headers
    table.add_column("Binding", style="cyan")
    table.add_column("Description", style="yellow")

    for binding, description in commands.items():
        table.add_row(binding, description)

    panel = Panel.fit(table, title="Command List (Press ENTER to exit)") # fit will make the panel the size of the table
    live.update(Align.center(panel), refresh = True)
    keyboard.wait("enter")
            
def make_search_layout(results, query, selected_index = 0, selected_type = 0):
    search_table = Table(title = "Search Results ({})".format("songs" if selected_type == 0 else "albums"), box = box.SIMPLE_HEAD, expand = True)
    search_table.add_column("#", style = 'dim')
    search_table.add_column("Name", style = 'yellow')
    search_table.add_column("Artist", style = 'yellow')
    if selected_type == 0:
        search_table.add_column("Duration", style = 'dim')
        
    for i in range(len(results)):
        style = None
        if i == selected_index:
            style = 'black on yellow'
        title = results[i]['name']
        artist = results[i]['artists'][0]['name']
        if selected_type == 0:
            duration = results[i]['duration_ms'] / 1000
            search_table.add_row(str(i + 1), title, artist, format_sec(duration), style = style)
        else:
            search_table.add_row(str(i + 1), title, artist, style = style)

    if results == []:
        search_query_text = Text.from_markup("🔎 [yellow] Searching For: [/] {}[blink]|[/]".format(query), justify = 'left')
    else:
        remaining_text = results[selected_index]['name'][len(query):] # this will get the rest of the title from the selected song
        search_query_text = Text.from_markup("🔎 [yellow] Searching For: [/] {}[blink]|[/][dim]{}[/]".format(query, remaining_text), justify = 'left')
    
    layout = Group(
        search_table,
        search_query_text
    )
    return layout

def add_spotify_track_to_db(track):
    # Check if song exists
    cur.execute("SELECT song_id FROM songs WHERE spotify_id = ?", (track['id'],))
    result = cur.fetchone()
    if result:
        return result[0]

    # Check if album exists
    cur.execute("SELECT album_id FROM albums WHERE spotify_album_id = ?", (track['album']['id'],))
    album_result = cur.fetchone()
    if album_result:
        album_id = album_result[0]
    else:
        # Create new album
        cur.execute("SELECT MAX(album_id) FROM albums")
        max_id = cur.fetchone()[0]
        album_id = max_id + 1 if max_id else 1
        album_name = track['album']['name']
        artist = track['album']['artists'][0]['name']
        created_at = track['album']['release_date']
        cur.execute("INSERT INTO albums (album_id, album_name, artist, liked, created_at, spotify_album_id) VALUES (?, ?, ?, ?, ?, ?)",
                    (album_id, album_name, artist, 0, created_at, track['album']['id']))
        conn.commit()

    # Create new song
    cur.execute("SELECT MAX(song_id) FROM songs")
    max_id = cur.fetchone()[0]
    song_id = max_id + 1 if max_id else 1
    title = track['name']
    artist = track['artists'][0]['name']
    duration = track['duration_ms'] / 1000
    release_date = track['album']['release_date']
    spotify_id = track['id']

    cur.execute("INSERT INTO songs (song_id, album_id, title, artist, liked, release_date, duration, spotify_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (song_id, album_id, title, artist, 0, release_date, duration, spotify_id))
    conn.commit()

    return song_id

def search_screen():
    pressed_keys.append('backspace') # Mimic backspace to show search results initially
    search_query = ""
    selected_index = 0
    results = []
    log = []
    search_type = 0 # 0 for songs, 1 for albums
    
    running = True
    
    last_input_time = 0
    search_delay = 0.25
    last_searched_query = ""

    key_bindings = {"ctrl+r": "Returns to the home screen.",
                    "Enter": "Queue a song / album",
                    "tab": "Switch between song and album search."}
    
    while running:
        handle_events()
        
        time.sleep(0.1)
        
        search_query, changed = handle_input(search_query)

        if changed:
            last_input_time = time.time()

        for char in pressed_keys:
            if char == "ctrl+r":
                running = False
            elif char == "ctrl+i":
                show_commands(key_bindings)
            elif char == "up":
                selected_index -= 1
            elif char == "down":
                selected_index += 1
            elif char == "tab":
                search_type = not search_type
                results = []
            elif char == "enter" and results != []:
                if search_type == 0:
                    track = results[selected_index]
                    song_id = add_spotify_track_to_db(track)
                    if song_id != -1:
                        queue_song(song_id)
                        log.append("Added [green]{}[/] to the queue.".format(track['name']))
                        if live:
                            live.update(make_main_layout(), refresh=True)
                else:
                    album = results[selected_index]
                    tracks = sp.album_tracks(album['id'])
                    for track in tracks['items']:
                        # The track object from album_tracks is different from the one from search, so we need to get the full track object
                        full_track = sp.track(track['id'])
                        song_id = add_spotify_track_to_db(full_track)
                        if song_id != -1:
                            queue_song(song_id)
                    log.append("Added album [green]{}[/] to the queue.".format(album['name']))
                    if live:
                        live.update(make_main_layout(), refresh=True)

    
        pressed_keys.clear()
        
        if time.time() - last_input_time > search_delay and search_query != last_searched_query:
            if search_query:
                search_type_str = 'track' if search_type == 0 else 'album'
                spotify_results = sp.search(search_query, type=search_type_str, limit=15)
                results = spotify_results['tracks' if search_type == 0 else 'albums']['items']
            else:
                results = []
            last_searched_query = search_query
        
        selected_index = within_range(selected_index, 0, len(results) - 1)
        panel = make_search_layout(results, search_query, selected_index = selected_index, selected_type=search_type)
        
        layout = Group(
            Text.from_markup('\n'.join(log[-4:])), # Last 4 logs,
            panel
        )
        live.update(layout, refresh = True)
        
def make_library_layout(albums, playlists, selected_type = 0, selected_index=0, is_navigating = False, navigation_index = 0):
    layout = Layout()
    layout.split_column(
        Layout(name = "library"),
        Layout(name = "details")
    )
    layout["library"].split_row(
        Layout(name = "album", ratio = (2 if selected_type == 0 else 1)),
        Layout(name = "playlist", ratio = (2 if selected_type == 1 else 1))
    )
    
    details_table = Table(box = box.SIMPLE_HEAD, expand = True)
    details_table.add_column("#", style = 'dim')
    details_table.add_column("Name", style = 'yellow')
    details_table.add_column("Duration", style = 'dim')
    
    if selected_type == 0 and selected_index == 1: # Recently played album, special case.
        details_table.add_column("Times Played", style = 'dim')
        
    if playlists == []:
        layout['library']['playlist'].update(Panel("No Playlists Created.", title = "Playlist"))
    else:
        playlist_table = Table(title = "{} Playlists".format(len(playlists)), box = box.SIMPLE_HEAD, expand = True)
        playlist_table.add_column("Name", style = 'yellow')
        playlist_table.add_column("# Songs", style = 'dim')
            
        for i in range(len(playlists)):
            
            songs = playlists[i]["songs"]
            
            style = None
            if selected_type == 1 and selected_index == i:
                style = 'black on yellow'
                if songs != []:
                        
                    chunk_size = (console.height // 2) - 6 # This is the max no. of songs we can fit in the page
                
                    if chunk_size < 1:
                        chunk_size = 1
                        
                    pages = chunk_list(songs, chunk_size = chunk_size)
                    current_page_index, current_index = divmod(navigation_index, chunk_size)
                    current_page = pages[current_page_index]
                    
                    details_table.title = "Page [{}/{}] (Total Songs: {})".format(current_page_index + 1, len(pages), len(songs))
                
                    for j in range(len(current_page)):
                        actual_index = j + current_page_index * chunk_size # the index of the song in 
                        song = current_page[j]
                        title = ":heartbeat: " + song[1] if song[2] else song[1] 
                        style_song = None
                        if is_navigating and current_index == j:
                            style_song = 'black on yellow'
                        details_table.add_row(str(actual_index + 1), title, format_sec(song[3]), style=style_song)
                        j += 1
            playlist_table.add_row(playlists[i]["name"], str(len(playlists[i]["songs"])), style = style)
        
        layout["library"]["playlist"].update(Panel(playlist_table, title = "playlist", border_style = "yellow" if selected_type == 1 else ""))
    
    album_table = Table(title = "{} Albums".format(len(albums)), box = box.SIMPLE_HEAD, expand = True)
    album_table.add_column("Name", style = 'yellow')
    album_table.add_column("# Songs", style = 'dim')
        
    for i in range(len(albums)):
        
        songs = albums[i]["songs"]
        
        style = None
        if selected_index == i and selected_type == 0:
            style = 'black on yellow'
            if songs != []:
                chunk_size = (console.height // 2) - 6 # This is the max no. of songs we can fit in the page
                
                if chunk_size < 1:
                    chunk_size = 1
                    
                pages = chunk_list(songs, chunk_size = chunk_size)
                current_page_index, current_index = divmod(navigation_index, chunk_size)
                current_page = pages[current_page_index]
                
                details_table.title = "Page [{}/{}] (Total Songs: {})".format(current_page_index + 1, len(pages), len(songs))
            
                for j in range(len(current_page)):
                    actual_index = j + current_page_index * chunk_size # the index of the song in 
                    song = current_page[j]
                    title = ":heartbeat: " + song[1] if song[2] else song[1] 
                    style_song = None
                    if is_navigating and current_index == j:
                        style_song = 'black on yellow'
                    if selected_index == 1: # recentlyplayed is selected.
                        details_table.add_row(str(actual_index + 1), title, format_sec(song[3]), str(song[4]), style=style_song)
                    else:
                        details_table.add_row(str(actual_index + 1), title, format_sec(song[3]), style=style_song)
                    j += 1
                
        album_table.add_row(albums[i]["name"], str(len(songs)), style = style)
    
    layout["library"]["album"].update(Panel(album_table, title = "Album", border_style = "yellow" if selected_type == 0 else ""))
    
    details_color = ""
    if is_navigating:
        details_color = "yellow"
    if details_table.row_count != 0:
        layout["details"].update(Panel(details_table, title = "details", border_style=details_color))
    else:
        layout["details"].update(Panel(Align.center("No songs for selected item.", vertical = "middle"), title = "details", border_style=details_color))
    return layout

def add_to_playlist_screen(playlist_id):
    cur.execute("SELECT playlist_name FROM playlists WHERE playlist_id=?", (playlist_id,))
    name = cur.fetchone()[0]
    
    selected_index = 0
    search_query = ''
    results = []
    selected_songs = []
    running = True
    while running:
        handle_events()
        time.sleep(0.25)
        
        search_query, re_search = handle_input(search_query)
        for key in pressed_keys:
            if key == "ctrl+s":
                running = False
                cur.execute("SELECT song_id FROM playlistsongs WHERE playlist_id=?", (playlist_id,))
                already_existing_songs = cur.fetchall()
                for song in selected_songs:
                    if not song[0] in already_existing_songs:
                        cur.execute("INSERT INTO playlistsongs (song_id, playlist_id) VALUES(?, ?)", (song[0], playlist_id))
                conn.commit()
            elif key == "enter" and results != []:
                if results[selected_index] not in selected_songs:
                    selected_songs.append(results[selected_index])
            elif key == "up":
                selected_index -= 1
            elif key == "down":
                selected_index += 1
                    
        pressed_keys.clear()
        if re_search:
           cur.execute("SELECT song_id, title, duration, liked, artist FROM songs WHERE title LIKE ? LIMIT 15", (search_query + '%',))
           results = cur.fetchall()

        selected_index = within_range(selected_index, 0, len(results) - 1)
        
        panel = make_search_layout(results, search_query, selected_index)
        details = []
        for i in range(len(selected_songs)):
            details.append("[dim]{}[/]. [yellow]{}[/]".format(i + 1, selected_songs[i][1]))
            
        layout = Group(
            Text.from_markup("The Following Songs Will Be Added To [yellow]{} (CTRL+S TO SAVE)[/]: \n ".format(name) + '\n '.join(details) + '\n'),
            panel
        )
        live.update(layout, refresh=True)
        
def library_screen():
    running = True
    selected_type = selected_index = navigation_index = 0 # album = 0, playlist = 1 for type
    is_navigating = False
    albums = get_library_albums()
    playlists = get_all_playlists()
    
    key_bindings = {"ctrl+r": "Return to home screen",
                    "ctrl+d": "Delete the selected song from playlist or the selected playlist.",
                    "ctrl+q": "Queue the seleted album / playlist / song.",
                    "ctrl+a": "Add song(s) to the selected playlist",
                    "ctrl+n": "Create a new playlist",
                    "Up/Down": "Navigate through albums / playlists",
                    "Left/Right": "Switch between album and playist.",
                    "Enter": "Toggle Navigating through the selected album / playlist"}
    
    while running:
        handle_events()
        time.sleep(0.25)
        
        for key in pressed_keys:
            if key == "ctrl+r":
                running = False
            elif key == "ctrl+i":
                show_commands(key_bindings)
            elif key == "enter":
                is_navigating = not is_navigating # "not True" = False, ...
            elif key == "ctrl+d" and selected_type == 1:
                if is_navigating: # Just remove the selected song
                    current_song = playlists[selected_index]["songs"]
                    if current_song != []:
                        current_song = current_song[navigation_index]
                        cur.execute("DELETE FROM playlistsongs WHERE song_id=? AND playlist_id=?", (current_song[0], playlists[selected_index]["id"]))
                else: # Delete the playlist + all the songs in it
                    cur.execute("DELETE FROM playlists WHERE playlist_id=?", (playlists[selected_index]["id"],))
                    cur.execute("DELETE FROM playlistsongs WHERE playlist_id=?", (playlists[selected_index]["id"],))
                conn.commit()
                playlists = get_all_playlists()
            elif key == "ctrl+q":
                if selected_type == 0: # albums
                    songs = albums[selected_index]["songs"]
                else:
                    songs = playlists[selected_index]["songs"]
                    
                if is_navigating:
                    song = songs[navigation_index]
                    queue_song(song[0])
                else:
                    for song in songs:
                        queue_song(song[0])
            elif key == "ctrl+a" and selected_type == 1 and not is_navigating and playlists != []:
                add_to_playlist_screen(playlists[selected_index]["id"])
                playlists = get_all_playlists()
            elif key == "up":
                if is_navigating:
                    navigation_index -= 1
                else:
                    selected_index -= 1
            elif key == "down":
                if is_navigating:
                    navigation_index += 1
                else:
                    selected_index += 1
            elif key == "ctrl+n":
                name = ''
                while True:
                    time.sleep(0.25)
                    name, changed = handle_input(name)
                    live.update(Text.from_markup("🔎 [yellow] Enter Playlist Name -> [/] {}|".format(name), justify = 'left'), refresh=True)
                    if "enter" in pressed_keys:
                        break
                    pressed_keys.clear()
                name = name.strip()
                if name != "":
                    create_playlist(name)
                    playlists = get_all_playlists()
            elif key == "right" or key == "left" and not is_navigating: # shud not change when navigating, causes index error due to different no of albums and playlists
                selected_type = not selected_type # not 0 = 1, not 1 = 0.
        
        pressed_keys.clear()
        
        t = albums if selected_type == 0 else playlists
        if t:
            if not is_navigating:
                selected_index = within_range(selected_index, 0, len(t) - 1)
            else:
                try:
                    navigation_index = within_range(navigation_index, 0, len(t[selected_index]["songs"]) - 1)
                except IndexError:
                    is_navigating = False # Exit navigation mode
                    selected_index = 0
        
        live.update(make_library_layout(albums, playlists, selected_type, selected_index, is_navigating, navigation_index), refresh = True)
        
def make_main_layout(selected_song = 0):
    if currently_playing == None:
        text = Align.center(
            Text("There is no song currently playing! (Press CTRL+I to view a list of commands)", justify = 'center'),
            vertical = 'middle'
        )
        playing_panel = Panel(text, title = 'Not Playing', style = 'red')
    else:
        title = ":heartbeat: " + currently_playing[1] if currently_playing[4] else currently_playing[1] # will add a heart if its liked
        text = Align.left(
            Text.from_markup("[yellow]{}[/]\n[white]on[/] [yellow]{}[/]\n[white]by[/] [yellow]{}[/]\n".format(title,  currently_playing[2], currently_playing[3])),
            vertical = 'middle'
        )
        status = "Paused" if paused else "Playing"
        current = pygame.mixer.music.get_pos() // 1000
        total = currently_playing[5]
        
        percent_completed = int((current / total)  * 100)
        progress = Text("{}/{}".format(format_sec(current), format_sec(total)))
        progress.align(align = "center", width = console.width)
        progress.stylize(style="black on yellow", start=0, end=int((percent_completed / 100) * console.width))
        
        playing_panel = Panel(Group(text, progress), title = Text.from_markup('[yellow]{} Loop {} | Shuffle {}'.format(status, loop, shuffle)), style = 'green' if currently_playing[4] else "red")
        
    if queue == []:
        queue_panel = Panel(
            Align.center(Text("There are no songs in the queue!", justify = 'center'), vertical = 'middle'),
            title = 'Queue', style = "magenta")
    else:
        chunk_size = (console.height - 14) # This is the max no. of songs we can fit in the page
        if chunk_size < 1:
            chunk_size = 1
        pages = chunk_list(queue, chunk_size = chunk_size)
        current_page_index, current_index = divmod(selected_song, chunk_size)
        current_page = pages[current_page_index]
        
        queue_table = Table(title = "Page [{}/{}] (Total Songs: {})".format(current_page_index + 1, len(pages), len(queue)), box = box.SIMPLE_HEAD, expand = True)
        queue_table.add_column("#", style = 'dim')
        queue_table.add_column("Name", style = 'yellow')
        queue_table.add_column("Artist", style = 'yellow')
        queue_table.add_column("Duration", style = 'dim')
    
        for i in range(len(current_page)):
            style = None
            if i == current_index:
                style = 'black on yellow'
            title = ":heartbeat: " + current_page[i][1] if current_page[i][4] else current_page[i][1] 
            queue_table.add_row(str(i + 1 + current_page_index * chunk_size), title, current_page[i][3], format_sec(current_page[i][5]), style = style)
        
        queue_panel = Panel(queue_table, title = 'Queue', style = 'magenta')

    return Group(playing_panel, queue_panel)

def home_screen():
    global live, loop, shuffle
    running = True
    
    key_bindings = {"ctrl+r": "Ends the program.", 
                    "ctrl+d": "Remove the selected song from queue.",
                    "ctrl+p": "Pause / Unpause current song", 
                    "ctrl+a": "Like the currently playing song", 
                    "ctrl+s": "Search for songs / albums.", 
                    "ctrl+l": "Open your library.", 
                    "ctrl+v": "Toggle loop.", 
                    "ctrl+w": "Toggle shuffle.", 
                    "ctrl+m": "Play the selected song in the queue.",
                    "Up/Down": "Navigate through the queue.", 
                    "Right": "Play next song."}
    
    with Live(make_main_layout(), console = console, auto_refresh = False, screen = True) as live_obj:
        live = live_obj
        selected_index = 0
        while running:
            handle_events()
            time.sleep(0.25)
            
            for key in pressed_keys:
                if key == "ctrl+r":
                    running = False
                elif key == "ctrl+d":
                    if queue != [] and len(queue) > selected_index:
                        queue.pop(selected_index)
                elif key == "ctrl+p":
                    pause_unpause()
                elif key == "ctrl+i":
                    show_commands(key_bindings)
                elif key == "ctrl+s":
                    search_screen()
                elif key == "ctrl+l":
                    library_screen()
                elif key == "ctrl+v":
                    loop = not loop
                elif key == "ctrl+w":
                    shuffle = not shuffle
                elif key == "ctrl+a" and currently_playing:
                    like_song(currently_playing[0])
                elif key == "ctrl+m":
                    queue.insert(0, queue.pop(selected_index)) # move the selected song to the start of the queue, and play next song (which will play the selected song)
                    play_next_song()
                elif key == "up":
                    selected_index -= 1
                elif key == "down":
                    selected_index += 1
                elif key == "right":
                    play_next_song()
            
            selected_index = within_range(selected_index, 0, len(queue) - 1)
            live.update(make_main_layout(selected_song = selected_index), refresh = True)
                
            pressed_keys.clear()
    keyboard.unhook_all()
            
home_screen()