import mysql.connector as mysql
import customtkinter as ctk

import sys

ctk.set_appearance_mode("Dark")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

password = ctk.CTkInputDialog(title = "Login", text = "Enter password for `root` user").get_input() # this will make a window and ask user for password, and wait for a response

conn = mysql.connect(host='localhost', user='root', password=password)

if not conn.is_connected():
    print("Failed to connect to MySQL server")
    sys.exit() # this quits the program
    
cur = conn.cursor()
cur.execute("CREATE DATABASE IF NOT EXISTS project") # Create the database if it doesnt exist
cur.execute("use project") # Move cursor to project database


root = ctk.CTk()
root.geometry("1100x580") # set the window dimensions in pixels


root.mainloop() # This creates and opens the window