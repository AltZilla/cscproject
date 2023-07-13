import mysql.connector as mysql
import customtkinter as ctk

import sys

ctk.set_appearance_mode("Dark")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

conn = mysql.connect(host='localhost', user='root', password='syed', database='project')
if conn.is_connected():
    cursor = conn.cursor()
else:
    print("Failed to connect to MySQL server")
    sys.exit() # this quits the program

root = ctk.CTk()
root.geometry("1100x580") # set the window dimensions in pixels


root.mainloop() # This creates and opens the window