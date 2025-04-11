import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk

import sys
sys.path.append('../src')
from marq_tric import tricotissage, marquage

PATH_YAML = "../yaml_files/"
PATH_OUT = "../prgs_gcode/"

class Application:
    def __init__(self, window, window_title):
        self.window = window
        self.window.title(window_title)

        self.label = tk.Label(text="Enter yaml file name:")
        self.label.pack(pady=5)

        self.entry = tk.Entry()
        self.entry.pack(pady=5)

        # Buttons for different functions
        tk.Button(text="Générer Gcode tricotissage", command=lambda: self.run_function(tricotissage)).pack(pady=2)
        tk.Button(text="Générer Gcode marquage", command=lambda: self.run_function(marquage)).pack(pady=2)

        self.message = tk.Label(text="", fg="green")
        self.message.pack(pady=10)


        self.window.mainloop()

    def run_function(self, func):
        nom_fichier = self.entry.get() or "file.yaml"
        result = func(PATH_YAML + nom_fichier)  # Appelle la fonction en argument
        self.message.config(text=f"{result}", fg="green")


# Launch the app
Application(tk.Tk(), "Interface tricotissage")
