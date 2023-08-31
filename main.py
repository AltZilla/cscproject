import mysql.connector as mysql
import customtkinter as ctk
import pygame

from functools import partial

from PIL import Image

pygame.init()

ctk.set_appearance_mode("Dark")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

# password = ctk.CTkInputDialog(title = "Login", text = "Enter password for `root` user").get_input() # this will make a window and ask user for password, and wait for a response

conn = mysql.connect(host='localhost', user='root', password='sample', database = 'project')

if conn.is_connected():
    cur = conn.cursor()
else:
    print("Failed to connect to MySQL server")
    exit() # this quits the program

queue = [] # The first song will be the current playing song
search_results = []

root = ctk.CTk()
root.geometry("1100x580") # set the window dimensions in pixels

# configure grid layout (1x2)
root.grid_columnconfigure(0, weight=0)  # Column 0 (sidebar) won't expand
root.grid_columnconfigure(1, weight=1)  # Column 1 (main frame) will expand
root.grid_rowconfigure(0, weight=1)

# Tkinter Variables
search_var = ctk.StringVar()

# create sidebar frame
sidebar_frame = ctk.CTkFrame(root, width = 250, corner_radius=0)
sidebar_frame.grid(row=0, column=0, rowspan=1, sticky="nsew", padx = (0, 10))

def draw_sidebar_widgets():
    sidebar_frame.grid_rowconfigure(4, weight = 1)
    
    logo = ctk.CTkImage(Image.open("assets/logo.png"), size=(26, 26))
    frame_label = ctk.CTkLabel(sidebar_frame, text="  No Name Yet", image=logo,
                                        compound="left", font=ctk.CTkFont(size=15, weight="bold"))
    frame_label.grid(row=0, column=0, padx=20, pady=20)
    
    home_icon = ctk.CTkImage(Image.open("assets/home.png"), size=(26, 26))
    home_button = ctk.CTkButton(sidebar_frame, corner_radius=0, height=40, border_spacing=10, text="Home",
                                                   fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"),
                                                   image=home_icon, anchor="w", command = partial(change_tab, "home"))
    home_button.grid(row=1, column=0, sticky="ew")
    
    search_icon = ctk.CTkImage(Image.open("assets/search.png"), size=(26, 26))
    search_button = ctk.CTkButton(sidebar_frame, corner_radius=0, height=40, border_spacing=10, text="Search",
                                                   fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"),
                                                   image= search_icon, anchor="w", command = partial(change_tab, "search"))
    search_button.grid(row=2, column=0, sticky="ew")


# create main frame
main_frame = ctk.CTkFrame(root, corner_radius=0)
main_frame.grid(row=0, column=1, rowspan=1, sticky="nsew")

def draw_home_widgets():
    pass

def draw_search_widgets():
    global entry, album_results_frame, results_frame
    
    main_frame.grid_rowconfigure(0, weight = 0)
    main_frame.grid_rowconfigure(1, weight = 1)
    main_frame.grid_columnconfigure((0, 1), weight = 1)
    
    entry = ctk.CTkEntry(main_frame, placeholder_text="Search",
                         textvariable = search_var)
    entry.bind("<Return>", search) # This will call search() when return is pressed.
    entry.grid(row = 0, column = 0, columnspan=2, sticky = 'ew')
    
    # results_frame = ctk.CTkScrollableFrame(main_frame)
    # results_frame.grid(row = 1, column = 0, sticky = 'news', pady = 10)

    album_frame = ctk.CTkFrame(main_frame)
    album_frame.grid(row = 1, column = 0, sticky = 'news', pady = 10)
    
    text_label = ctk.CTkLabel(album_frame, text = 'Album', font = (26, 26))
    text_label.pack(pady = 15)
    
    album_results_frame = ctk.CTkFrame(album_frame)
    album_results_frame.pack(fill = 'x', padx = 20)
    
    songs_frame = ctk.CTkFrame(main_frame)
    songs_frame.grid(row = 1, column = 1, sticky = 'news', pady = 10)
    
    text_label = ctk.CTkLabel(songs_frame, text = 'Songs', font = (26, 26))
    text_label.pack(pady = 15)
    
    results_frame = ctk.CTkFrame(songs_frame)
    results_frame.pack(fill = 'x', padx = 20)
    
def change_tab(name):
    for widget in main_frame.winfo_children():
        widget.destroy()
    
    # show selected frame
    if name == "home":
        draw_home_widgets()
    elif name == "search":
        draw_search_widgets()
    
def search(event): # event is the keypress event, when "Enter" is clicked
    for widget in results_frame.winfo_children():
        widget.destroy()
    
    query = "SELECT * FROM songs WHERE title LIKE '%{}%'".format(search_var.get())
    cur.execute(query)
    results = cur.fetchall()
    
    for song_id, title, artist, liked, album, release_date, spotify_id in results[:8]:
        
        frame = ctk.CTkFrame(results_frame, fg_color='transparent')
        frame.pack(fill='x')  # Fill the x axis

        image_label = ctk.CTkLabel(frame, text='', image=ctk.CTkImage(Image.open('assets/logo.png'), size=(35, 35)))
        image_label.pack(side='left', padx=10, pady=5)

        song_details = ctk.CTkButton(frame, text=title + '\n' + artist, fg_color='transparent', command = partial(play_song, spotify_id))
        song_details.pack(side='left', padx = 1, fill = 'x', expand = True)

        duration_label = ctk.CTkButton(frame, width = 100, text='3:40', fg_color='transparent')
        duration_label.pack(side='right')

        
def play_song(filename):
    pygame.mixer.music.load('songs/' + filename + '.mp3')
    pygame.mixer.music.play()

draw_sidebar_widgets()
draw_home_widgets()

root.mainloop() # This creates and opens the window