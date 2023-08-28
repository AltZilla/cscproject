import mysql.connector as mysql
import customtkinter as ctk

from PIL import Image

ctk.set_appearance_mode("Dark")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

# password = ctk.CTkInputDialog(title = "Login", text = "Enter password for `root` user").get_input() # this will make a window and ask user for password, and wait for a response

conn = mysql.connect(host='localhost', user='root', password='syedisdumb', database = 'project')

if conn.is_connected():
    cur = conn.cursor()
else:
    print("Failed to connect to MySQL server")
    exit() # this quits the program

root = ctk.CTk()
root.geometry("1100x580") # set the window dimensions in pixels

# configure grid layout (1x2)
root.grid_columnconfigure(0, weight=0)  # Column 0 (sidebar) won't expand
root.grid_columnconfigure(1, weight=1)  # Column 1 (main frame) will expand
root.grid_rowconfigure(0, weight=1)

# create sidebar frame
sidebar_frame = ctk.CTkFrame(root, width = 250, corner_radius=0)
sidebar_frame.grid(row=0, column=0, rowspan=1, sticky="nsew", padx = (0, 10))

def draw_sidebar_widgets():
    sidebar_frame.grid_rowconfigure(4, weight = 1)
    
    image = ctk.CTkImage(Image.open("assets/logo.png"), size=(26, 26))
    frame_label = ctk.CTkLabel(sidebar_frame, text="  No Name Yet", image=image,
                                        compound="left", font=ctk.CTkFont(size=15, weight="bold"))
    frame_label.grid(row=0, column=0, padx=20, pady=20)
    
draw_sidebar_widgets()

# create main frame
main_frame = ctk.CTkFrame(root, corner_radius=0)
main_frame.grid(row=0, column=1, rowspan=1, sticky="nsew")



root.mainloop() # This creates and opens the window