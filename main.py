import mysql.connector as mysql
import pygame
import time
import keyboard
import random 

from rich.console import Console, Group
from rich.panel import Panel
from rich.live import Live
from rich.text import Text
from rich.align import Align
from rich.table import Table, box
from rich.layout import Layout

console = Console()

pygame.init()
pygame.mixer.music.set_endevent(45)

conn = mysql.connect(host='localhost', user='root', password='syedisdumb', database = 'project')

if conn.is_connected():
    cur = conn.cursor()
else:
    print("Failed to connect to MySQL server")
    exit() # this quits the program

currently_playing = None
queue = [] # This will have the structure [song_id, title, album, artist, liked, duration].
pressed_keys = []

paused = loop = shuffle = False

def handle_key_press(key):
    if keyboard.is_pressed("ctrl") and key.name != "ctrl":
        pressed_keys.append("ctrl+{}".format(key.name))
        
    elif key.name != "ctrl":
        pressed_keys.append(key.name)

keyboard.on_press(handle_key_press) # The handle_key_press(key) func will be called whenever a key is pressed. (key will be the key that was pressed.) 

def play_next_song():
    global currently_playing, paused
    paused = False
    
    if currently_playing:
        cur.execute("INSERT INTO recentlyplayed (song_id) VALUES({})".format(currently_playing[0])) # songs id
        conn.commit()
        
    if shuffle == True:
        random.shuffle(queue)
    if loop == True:
        queue.append(currently_playing)
    if queue != []:
        song_data = queue.pop(0) # Get the first song
        try:
            pygame.mixer.music.load('songs/' + str(song_data[0]) + '.mp3')
        except:
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
    query = "SELECT songs.title, albums.album_name, songs.artist, songs.liked, duration FROM albums, songs WHERE songs.album_id = albums.album_id AND songs.song_id = {}".format(song_id)
    cur.execute(query)

    title, album, artist, liked, duration = cur.fetchone()
    queue.append([song_id, title, album, artist, liked, duration])
    
    if currently_playing == None:
        play_next_song()
        
def like_song(song_id):
    # Check if the song is already liked
    cur.execute("SELECT liked FROM songs WHERE song_id = {}".format(song_id))
    result = cur.fetchone()

    liked = not result[0]  # Toggle the liked status
    cur.execute("UPDATE songs SET liked={} WHERE song_id={}".format(int(liked), song_id))
    conn.commit()
    
    if currently_playing and currently_playing[0] == song_id:
        currently_playing[4] = liked
    for data in queue:
        if data[0] == song_id:
            data[4] = liked
    return liked

def like_album(album_id):
    # Check if the album is already liked
    cur.execute("SELECT liked FROM albums WHERE album_id = {}".format(album_id))
    result = cur.fetchone()

    liked = not result[0]  # Toggle the liked status
    cur.execute("UPDATE albums SET liked={} WHERE album_id={}".format(int(liked), album_id))
    conn.commit()
    return liked
    
def format_sec(seconds):
    min, sec = divmod(seconds, 60)
    if sec < 10:
        sec = "0" + str(sec)
    return "{}:{}".format(min, sec)

def get_library_albums():
    cur.execute("SELECT songs.song_id, songs.title, albums.album_name, songs.artist FROM albums, songs WHERE songs.album_id = albums.album_id AND songs.liked = 1")
    liked_songs = cur.fetchall()
    
    cur.execute("SELECT songs.song_id, songs.title, albums.album_name, songs.artist, recentlyplayed.played_at FROM songs, albums, recentlyplayed WHERE songs.album_id = albums.album_id AND songs.song_id = recentlyplayed.song_id AND songs.liked = 1 ORDER BY recentlyplayed.played_at DESC LIMIT 10")
    recently_played = cur.fetchall()
    
    albums = [
            {'id': -2, 'name': "Liked Songs", "songs": liked_songs},
            {'id': -1, 'name': "Recently Played", "songs": recently_played}
        ]
    
    cur.execute("SELECT album_id, album_name FROM albums WHERE liked=1")
    details = cur.fetchall()
    for data in details:
        cur.execute("SELECT songs.song_id, songs.title, albums.album_name, songs.artist FROM albums, songs WHERE songs.album_id = albums.album_id AND albums.album_id={}".format(data[0]))
        songs = cur.fetchall()
        albums.append({'id': data[0], "name": data[1], "songs": songs})

    return albums

def get_all_playlists():
    playlists = []
    cur.execute("SELECT playlist_id, playlist_name FROM playlists")
    details = cur.fetchall()
    for data in details:
        cur.execute("SELECT songs.song_id, songs.title, albums.album_name, songs.artist FROM albums, songs WHERE songs.album_id = albums.album_id AND playlist_id={}".format(data[0]))
        songs = cur.fetchall()
        playlists.append({'id': data[0], "name": data[1], "songs": songs})

    return playlists

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

    panel = Panel.fit(table, title="Command List (Press ENTER to exit)") # This will make the panel the size of the table
    live.update(Align.center(panel), refresh = True)
    keyboard.wait("enter")
    
def make_main_layout(selected_song = 0):
    if currently_playing == None:
        text = Align.center(
            Text("There is no song currently playing!", justify = 'center'),
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
            title = 'Queue', style = 'magenta')
    else:
        queue_table = Table(title = "{} songs queued!".format(len(queue)), box = box.SIMPLE_HEAD, expand = True)
        queue_table.add_column("#", style = 'dim')
        queue_table.add_column("Name", style = 'yellow')
        queue_table.add_column("Duration", style = 'dim')
        
        for i in range(len(queue)):
            style = None
            if i == selected_song:
                style = 'black on yellow'
            title = ":heartbeat: " + queue[i][1] if queue[i][4] else queue[i][1] 
            queue_table.add_row(str(i + 1), title, format_sec(queue[i][5]), style = style)
        
        queue_panel = Panel(queue_table, title = 'Queue', style = 'magenta')

    return Group(playing_panel, queue_panel)
            
def make_search_layout(songs, query, selected_index = 0, selected_type = 0):
    search_table = Table(title = "Search Results ({})".format("songs" if selected_type == 0 else "albums"), box = box.SIMPLE_HEAD, expand = True)
    search_table.add_column("#", style = 'dim')
    search_table.add_column("Name", style = 'yellow')
    search_table.add_column("Duration", style = 'dim')
        
    for i in range(len(songs)):
        style = None
        if i == selected_index:
            style = 'black on yellow'
        title = ":heartbeat: " + songs[i][1] if songs[i][3] else songs[i][1] 
        search_table.add_row(str(i + 1), title, format_sec(songs[i][2]), style = style)

    if songs == []:
        search_query_text = Text.from_markup("🔎 [yellow] Searching For: [/] {}|".format(query), justify = 'left')
    else:
        search_query_text = Text.from_markup("🔎 [yellow] Searching For: [/] {}|[dim]{}[/]".format(query, songs[selected_index][1][len(query):]), justify = 'left')
    
    layout = Group(
        search_table,
        search_query_text
    )
    return layout
     
def search_screen():
    pressed_keys.append('backspace') # Mimic backspace to show search results initially
    search_query = ""
    selected_index = search_type = 0 # 0 for songs, 1 for album search
    results = [] # Structure: [song_id, title, duration, liked]
    log = []
    
    running = True
    
    key_bindings = {"ctrl+r": "Returns to the home screen.", "ctrl+l": "Like the selected song / album.", "ctrl+t":"Toggle between ", "Up/Down": "Navigate through searched songs / albums.", "Enter": "Queue a song / album"}
    
    while running:
        handle_events()
        
        re_search = False
        time.sleep(0.25)
        
        for char in pressed_keys:
            if char == "ctrl+r":
                running = False
            elif char == "ctrl+i":
                show_commands(key_bindings)
            elif char == 'backspace':
                search_query = search_query[:-1]
                re_search = True
            elif len(char) == 1 and char.isalpha():
                search_query += char
                re_search = True
            elif char == "space":
                search_query += " "
                re_search = True
            elif char == "up":
                selected_index -= 1
            elif char == "down":
                selected_index += 1
            elif char == "ctrl+t":
                search_type = not search_type
                re_search = True
            elif char == "enter" and results != []:
                if search_type == 0:
                    queue_song(results[selected_index][0])
                    log.append("Added [green]{}[/] to the queue.".format(results[selected_index][1]))
                else:
                    cur.execute("SELECT song_id FROM songs WHERE album_id={}".format(results[selected_index][0]))
                    for song_id in cur.fetchall():
                        queue_song(song_id[0])
                    play_next_song()
                    log.append("Added album [green]{}[/] to the queue.".format(results[selected_index][1]))
            elif char == "ctrl+l":
                if search_type == 0:
                    like_song(results[selected_index][0])
                else:
                    like_album(results[selected_index][0])
                re_search = True
        pressed_keys.clear()
        
        if re_search == True:
            if search_type == 0:
                query = "SELECT song_id, title, duration, liked FROM songs WHERE title LIKE '{}%' LIMIT 15".format(search_query) # Selects a max of 15 songs
            else:
                query = "SELECT album_id, album_name, SUM(duration), albums.liked FROM songs NATURAL JOIN albums WHERE album_name LIKE '{}%' GROUP BY album_id LIMIT 15".format(search_query) # Selects a max of 15 albums
            cur.execute(query)
            results = cur.fetchall()
        
        selected_index = within_range(selected_index, 0, len(results) - 1)
        panel = make_search_layout(results, search_query, selected_index = selected_index, selected_type=search_type)
        
        layout = Group(
            Text.from_markup('\n'.join(log[-4:])), # Last 4 logs,
            panel
        )
        live.update(layout, refresh = True)
        
def make_library_layout(albums, playlists, selected_type = 0, selected_song=0):
    layout = Layout()
    layout.split_column(
        Layout(name = "library"),
        Layout(name = "details")
    )
    layout["library"].split_row(
        Layout(name = "album", ratio = (2 if selected_type == 0 else 1)),
        Layout(name = "playlist", ratio = (2 if selected_type == 1 else 1))
    )
    
    if playlists == []:
        layout['library']['playlist'].update(Panel("No Liked Playlists.", title = "Playlist"))
    else:
        playlist_table = Table(title = "{} Playlists".format(len(playlists)), box = box.SIMPLE_HEAD, expand = True)
        playlist_table.add_column("Name", style = 'yellow')
        playlist_table.add_column("# Songs", style = 'dim')
            
        for i in range(len(playlists)):
            style = None
            if i == selected_song and selected_type == 1:
                style = 'black on yellow'
            playlist_table.add_row(playlists[i]["name"], str(len(playlists[i]["songs"])), style = style)
        
        layout["library"]["playlist"].update(Panel(playlist_table, title = "playlist"))
    
    album_table = Table(title = "{} Albums".format(len(albums)), box = box.SIMPLE_HEAD, expand = True)
    album_table.add_column("Name", style = 'yellow')
    album_table.add_column("# Songs", style = 'dim')
        
    for i in range(len(albums)):
        style = None
        if i == selected_song and selected_type == 0:
            style = 'black on yellow'
        album_table.add_row(albums[i]["name"], str(len(albums[i]["songs"])), style = style)
    
    layout["library"]["album"].update(Panel(album_table, title = "Album"))
    
    return layout

def library_screen():
    running = True
    selected_type = selected_song = 0 # album = 0, playlist = 1
    albums = get_library_albums()
    playlists = get_all_playlists()
    
    while running:
        handle_events()
        time.sleep(0.25)
        
        for key in pressed_keys:
            if key == "ctrl+r":
                running = False
            elif key == "right" or key == "left":
                selected_type = not selected_type # not 0 = 1, not 1 = 0.
        
        pressed_keys.clear()
        
        live.update(make_library_layout(albums, playlists, selected_type, selected_song), refresh = True)
        
def home_screen():
    global live, loop, shuffle
    running = True
    
    key_bindings = {"ctrl+q": "Ends the program.", "ctrl+p": "Pause / Unpause current song", "ctrl+a": "Like the currently playing song", "ctrl+s": "Search for songs / albums.", "ctrl+l": "Open your library.", "ctrl+v": "Toggle loop.", "ctrl+w": "Toggle shuffle.", "Up/Down": "Navigate through the queue.", "Right/Left": "Play previous / next song."}
    with Live(make_main_layout(), console = console, auto_refresh = False, screen = True) as live:
        
        selected_index = 0
        while running:
            handle_events()
            time.sleep(0.25)
            
            for key in pressed_keys:
                if key == "ctrl+q":
                    running = False
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
                elif key == "up":
                    selected_index -= 1
                elif key == "down":
                    selected_index += 1
                elif key == "right":
                    play_next_song()
            
            selected_index = within_range(selected_index, 0, len(queue) - 1)
            live.update(make_main_layout(selected_song = selected_index), refresh = True)
                
            pressed_keys.clear()
            
home_screen()