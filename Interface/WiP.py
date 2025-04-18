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
        self.image_path = ""

        window.grid_rowconfigure(0, weight=0)
        window.grid_rowconfigure(1, weight=0)
        window.grid_rowconfigure(2, weight=0)
        window.grid_rowconfigure(3, weight=0)
        window.grid_rowconfigure(4, weight=0)
        window.grid_rowconfigure(5, weight=0)
        window.grid_rowconfigure(6, weight=0)
        window.grid_rowconfigure(7, weight=1)
        window.grid_rowconfigure(8, weight=0)
        window.grid_rowconfigure(9, weight=0)
        window.grid_columnconfigure(0, weight=1)
        window.grid_columnconfigure(1, weight=1)
        window.grid_columnconfigure(2, weight=1)

        button_dict = {"width":20, "height":1, "font": ("Arial", 10, "normal")}
        grid_dict = {"padx":5, "pady":10}

        tk.Label(text="Tricotissage", font=("Arial", 20,"bold")).grid(row=0,column=0,columnspan=3)

        # Chargement image et detection des tracés

        cell0 = tk.Frame(window, **grid_dict)
        cell0.grid(column=0,row=1)
        tk.Button(cell0,text="Sélection image", command=self.load_image,**button_dict).pack(pady=5)
        tk.Button(cell0,text="Détection du tracé",**button_dict).pack(pady=5)
        
        self.canvas_width = 420
        self.canvas_height = 300
        self.margin = 0

        self.canvas = tk.Canvas(window, width=self.canvas_width, 
                                height=self.canvas_height)
        self.canvas.grid(column=1, row=1, columnspan=2, **grid_dict)

        # Édition des points
        tk.Button(window,text="Positions aiguilles", **button_dict).grid(column= 0, row=2,pady=15)

        # Génération des Gcodes
        last_row = 9

        tk.Label(window,text="Enter yaml file name:").grid(column=0, row=last_row-2)
        tk.Entry(window).grid(column=1, row=last_row-2)
        tk.Button(window, text="Générer Gcode tricotissage", 
                  command=lambda: self.run_function(tricotissage), 
                  **button_dict).grid(column=0, row=last_row-1,pady=5)
        tk.Button(window, text="Générer Gcode marquage", 
                  command=lambda: self.run_function(marquage), 
                  **button_dict).grid(column=1, row=last_row-1)
        self.message = tk.Label(window, text="", fg="green")
        self.message.grid(column=0, row=last_row, columnspan=2)

        self.window.mainloop()


    def run_function(self, func):
        nom_fichier = self.entry.get() or "file.yaml"
        result = func(PATH_YAML + nom_fichier)  # Appelle la fonction en argument
        self.message.config(text=f"{result}", fg="green")
    

    def load_image(self):
        file_path = filedialog.askopenfilename()
        if not file_path:
            return

        self.new_img = Image.open(file_path)
        self.resized_img = self.resize_image_to_fit(self.new_img)
        self.pic = ImageTk.PhotoImage(self.resized_img)

        # Destroy previous label if it exists
        if hasattr(self, 'down_window_label'):
            self.down_window_label.destroy()

        self.down_window_label = tk.Label(image=self.pic)
        self.down_window_label.image = self.pic  # keep reference

        # Replace the old image window with a new centered one
        center_x = self.canvas_width // 2
        center_y = self.canvas_height // 2
        self.canvas.create_window(center_x, center_y, window=self.down_window_label)


    def resize_image_to_fit(self, image):
        max_width = self.canvas_width - self.margin
        max_height = self.canvas_height - self.margin

        img_width, img_height = image.size
        ratio = min(max_width / img_width, max_height / img_height)

        new_size = (int(img_width * ratio), int(img_height * ratio))
        return image.resize(new_size, Image.Resampling.LANCZOS)


# Launch the app
Application(tk.Tk(), "Interface tricotissage")
