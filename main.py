import mysql.connector as mysql
import pygame
import time
import keyboard

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

conn = mysql.connect(host='localhost', user='root', password='sample', database = 'project')

if conn.is_connected():
    cur = conn.cursor()
else:
    print("Failed to connect to MySQL server")
    exit() # this quits the program

queue = []
pressed_keys = []

keyboard.on_press(lambda key: pressed_keys.append(key.name))

def play_queued_song():
    song_data = queue[0]
    pygame.mixer.music.load('songs/' + song_data[3] + '.mp3')
    pygame.mixer.music.play()

def queue_song(song_id):
    query = "SELECT title, album, artist FROM songs where spotify_id = '{}'".format(song_id)
    cur.execute(query)

    title, album, artist = cur.fetchone()
    queue.append([title, album, artist, song_id])
    
    if len(queue) == 1:
        play_queued_song()
        
def handle_events():
    for event in pygame.event.get():
        if event.type == 45:
            queue.pop(0)
            play_queued_song()
        
    
def make_main_layout(selected_song = 0):
    if queue == []:
        text = Align.center(
            Text("There is no song currently playing!", justify = 'center'),
            vertical = 'middle'
        )
        playing_panel = Panel(text, title = 'Not Playing', style = 'red')
    else:
        song_data = queue[0]
        text = Align.left(
            Text.from_markup("[red]{}[/]\non {}\nby {}".format(song_data[0], song_data[1], song_data[2])),
            vertical = 'middle'
        )
        playing_panel = Panel(text, title = 'Now Playing {}'.format(pygame.mixer.music.get_pos()), style = 'red')
        
    if queue[1:] == []:
        queue_panel = Panel(
            Align.center(Text("There are no songs in the queue!", justify = 'center'), vertical = 'middle'),
            title = 'Queue', style = 'magenta')
    else:
        queue_table = Table(title = "Search Results", box = box.SIMPLE_HEAD, expand = True)
        queue_table.add_column("#", style = 'dim')
        queue_table.add_column("Name", style = 'yellow')
        queue_table.add_column("Duration", style = 'dim')
        
        for i in range(len(queue)):
            style = None
            if i == selected_song:
                style = 'on yellow'
            queue_table.add_row(str(i), queue[i][0], "3:00", style = style)
        
        queue_panel = Panel(queue_table, title = 'Queue', style = 'magenta')

    return Group(playing_panel, queue_panel)
                
def search_screen():
    pressed_keys.clear()
    search_query = ""
    selected_index = 0
    results = []
    
    while True:
        handle_events()
        
        re_search = False
        time.sleep(0.25)
        
        for char in pressed_keys:
            if char == 'backspace':
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
            elif char == "enter" and results != []:
                queue_song(results[selected_index][1])
                console.print("Added [green]{}[/] to the queue!".format(results[selected_index][0]))
                
        if 'ctrl' in pressed_keys:
            break
                
        pressed_keys.clear()
    
        
        if re_search == True:
            query = "SELECT title, spotify_id FROM songs WHERE title LIKE '{}%' LIMIT 15".format(search_query)
            cur.execute(query)
            results = cur.fetchall()
        
        if selected_index < 0:
            selected_index = len(results) - 1
        elif selected_index > len(results) - 1:
            selected_index = 0
            
        search_table = Table(title = "Search Results", box = box.SIMPLE_HEAD, expand = True)
        search_table.add_column("#", style = 'dim')
        search_table.add_column("Name", style = 'yellow')
        search_table.add_column("Duration", style = 'dim')
            
        for i in range(len(results)):
            style = None
            if i == selected_index:
                style = 'on yellow'
            search_table.add_row(str(i), results[i][0], "3:00", style = style)
        

        if results == []:
            search_query_text = Text.from_markup("🔎 [yellow] Searching For: [/] {}|".format(search_query), justify = 'left')
        else:
            search_query_text = Text.from_markup("🔎 [yellow] Searching For: [/] {}|[dim]{}[/]".format(search_query, results[selected_index][0][len(search_query):]), justify = 'left')
       
        layout = Group(
            search_table,
            search_query_text
        )
        
        live.update(layout, refresh=True)
    console.clear()
        
def main_loop():
    global live
    
    with Live(make_main_layout(), console = console, auto_refresh = False) as live:
        while True:
            
            handle_events()
            
            live.update(make_main_layout(), refresh = True)
            time.sleep(0.25)
            
            for key in pressed_keys:
                if key == "s":
                    search_screen()
                if key == "right":
                    pygame.mixer.music.stop()
                    play_queued_song()
            
                
            pressed_keys.clear()
            
main_loop()