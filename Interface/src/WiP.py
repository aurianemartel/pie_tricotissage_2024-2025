import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk



class Application:
    def __init__(self, window, window_title):
        self.window = window
        self.window.title(window_title)



        self.window.mainloop()


# Launch the app
Application(tk.Tk(), "Interface tricotissage")
