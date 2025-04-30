import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk

import sys

sys.path.append('../src')
from marq_tric import tricotissage, marquage

sys.path.append('../detpts')
from elodie1 import elodie1

PATH_YAML = "../yaml_files/"
PATH_OUT = "../prgs_gcode/"

MIN_ZOOM = 0
MAX_ZOOM = 2
ZOOM_INTERVAL = 0.5
MAX_OFFSETX_RATE = 1
MAX_OFFSETY_RATE = 1

class Application:
    def __init__(self, window, window_title):
        self.window = window
        self.window.title(window_title)
        self.image_path = ""

        window.grid_rowconfigure(0, weight=0)
        window.grid_rowconfigure(1, weight=0)
        window.grid_rowconfigure(2, weight=0)
        window.grid_rowconfigure(3, weight=0)
        window.grid_rowconfigure(4, weight=1)
        window.grid_columnconfigure(0, weight=1)
        window.grid_columnconfigure(1, weight=1)
        window.grid_columnconfigure(2, weight=1)

        self.button_dict = {"width":20, "height":1, "font": ("Arial", 10, "normal")}
        self.text_dict = {"font": ("Arial", 10, "normal")}
        self.grid_dict = {"padx":5, "pady":10}

        tk.Label(text="Tricotissage", font=("Arial", 20,"bold")).grid(row=0,column=0,columnspan=3)

        # Chargement image et detection des tracés

        cell0 = tk.Frame(window, **self.grid_dict)
        cell0.grid(row=1, column=0)
        tk.Label(cell0,text="Nom de projet",**self.text_dict).pack(pady=5)
        self.nom_projet_entry = tk.Entry(cell0)
        self.nom_projet_entry.pack(pady=5)
        tk.Button(cell0,text="Sélection image", command=self.load_image,**self.button_dict).pack(pady=5)
        # tk.Button(cell0,text="Détection du tracé",**self.button_dict).pack(pady=5)
        tk.Button(cell0,text="Détection du tracé", command=self.run_elodie1, **self.button_dict).pack(pady=5)
        
        self.canvas_width = 420
        self.canvas_height = 300
        self.margin = 0

        self.canvas = tk.Canvas(window, width=self.canvas_width, height=self.canvas_height)
        self.canvas.grid(row=1, column=1, columnspan=2, **self.grid_dict)

        # Édition des points
        

        # Génération des Gcodes
        self.cell5 = tk.Frame(window, **self.grid_dict)
        self.cell5.grid_rowconfigure(0, weight=1)
        self.cell5.grid_rowconfigure(1, weight=0)
        self.cell5.grid_columnconfigure(0, weight=1)
        self.cell5.grid_columnconfigure(1, weight=1)
        self.cell5.grid_columnconfigure(2, weight=1)

        tk.Button(self.cell5, text="Générer Gcode tricotissage", 
                  command=lambda: self.create_file(tricotissage), 
                  **self.button_dict).grid(row=0,column=0,pady=5)
        tk.Button(self.cell5, text="Générer Gcode marquage", 
                  command=lambda: self.create_file(marquage), 
                  **self.button_dict).grid(row=0,column=1,pady=5)
        self.message = tk.Label(self.cell5, text="", fg="green")
        self.message.grid(row=1,column=0,pady=5)

        self.window.mainloop()


    def create_file(self, func):
        nom_fichier = self.nom_projet_entry.get() or "file.yaml"
        result = func(PATH_YAML + nom_fichier)  # Appelle la fonction en argument
        self.message.config(text=f"{result}", fg="green")
    
    def run_elodie1(self):
        lx, ly, longueurs, self.pmpg = elodie1(self.file_path, epsilon=0.01, 
                                          afficher_im_init=False, 
                                          afficher_squelette=False)
        
        self.show_edit_points()
        print("Tracé detecté")
    
    def show_edit_points(self):

        self.xy_span = self.min_max_pmpg()
        x_min, x_max, y_min, y_max = self.xy_span
        self.text_xy = tk.Label(self.window, 
                                  text=f"x_min = {x_min}    x_max = {x_max}    y_min = {y_min}    y_max = {y_max}", 
                                  **self.text_dict)
        self.text_xy.grid(row=2, column=0, columnspan=3)

        tk.Label(self.window, text="Zoom :", **self.text_dict).grid(row=3, column=0)
        self.zoom = tk.Scale(self.window, from_=MIN_ZOOM, to=MAX_ZOOM, tickinterval=ZOOM_INTERVAL, 
                             command=self.set_x_y_zoom, resolution=0.01, length=self.canvas_width, 
                             orient="horizontal")
        self.zoom.set(1)
        self.zoom.grid(row=3, column=1, columnspan=2)

        tk.Label(self.window, text="Offset en x :", **self.text_dict).grid(row=4, column=0)
        self.offset_x = tk.Scale(self.window, from_=-1*x_min, to=MAX_OFFSETX_RATE*x_max, tickinterval=(x_max-x_min)//5, 
                                 command=self.set_x_offset, length=self.canvas_width, orient="horizontal")
        self.offset_x.grid(row=4, column=1, columnspan=2)

        tk.Label(self.window, text="Offset en y :", **self.text_dict).grid(row=5, column=0)        
        self.offset_y = tk.Scale(self.window, from_=-1*y_min, to=MAX_OFFSETY_RATE*y_max, tickinterval=(y_max-y_min)//5, 
                                 command=self.set_y_offset, length=self.canvas_width, orient="horizontal")
        self.offset_y.grid(row=5, column=1, columnspan=2)


        # tk.Button(self.cell3,text="Positions aiguilles", 
        #           command=self.run_elodie2, **self.button_dict).grid(row=2, column=0)

    
    def run_elodie2(self):
        self.cell5.grid(column=0, row=4, columnspan=3)
        print("Points déterminés")

    def load_image(self):
        self.file_path = filedialog.askopenfilename()
        if not self.file_path:
            return

        self.new_img = Image.open(self.file_path)
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
    
    def min_max_pmpg(self):
        x_min, x_max, y_min, y_max = 10000, 0, 10000, 0
        for i in range(len(self.pmpg)):
            for j in range(len(self.pmpg[i])):
                x = self.pmpg[i][j][0]
                y = self.pmpg[i][j][1]
                if x < x_min:
                    x_min = x
                if x > x_max:
                    x_max = x
                if y < y_min:
                    y_min = y
                if y > y_max:
                    y_max = y
        return x_min, x_max, y_min, y_max
    
    def set_x_y_zoom(self, val):
        x_min, x_max, y_min, y_max = self.xy_span
        zoom_val = float(val)
        offset_x_val = self.offset_x.get()
        offset_y_val = self.offset_y.get()
        x_min = int(zoom_val*x_min) + offset_x_val
        x_max = int(zoom_val*x_max) + offset_x_val
        y_min = int(zoom_val*y_min) + offset_y_val
        y_max = int(zoom_val*y_max) + offset_y_val
        self.text_xy.configure(text=f"x_min = {x_min}    x_max = {x_max}    y_min = {y_min}    y_max = {y_max}")
        self.offset_x.configure(from_=-1*x_min, to=MAX_OFFSETX_RATE*x_max, tickinterval=(x_max-x_min)//5)
        self.offset_y.configure(from_=-1*y_min, to=MAX_OFFSETY_RATE*y_max, tickinterval=(y_max-y_min)//5)
    
    def set_x_offset(self, val):
        x_min, x_max, y_min, y_max = self.xy_span
        zoom_val = self.zoom.get()
        offset_x_val = int(val)
        offset_y_val = self.offset_y.get()
        x_min = int(zoom_val*x_min) + offset_x_val
        x_max = int(zoom_val*x_max) + offset_x_val
        y_min = int(zoom_val*y_min) + offset_y_val
        y_max = int(zoom_val*y_max) + offset_y_val
        # self.xy_span = x_min, x_max, y_min, y_max
        self.text_xy.configure(text=f"x_min = {x_min}    x_max = {x_max}    y_min = {y_min}    y_max = {y_max}")

    def set_y_offset(self, val):
        x_min, x_max, y_min, y_max = self.xy_span
        zoom_val = self.zoom.get()
        offset_x_val = self.offset_x.get()
        offset_y_val = int(val)
        x_min = int(zoom_val*x_min) + offset_x_val
        x_max = int(zoom_val*x_max) + offset_x_val
        y_min = int(zoom_val*y_min) + offset_y_val
        y_max = int(zoom_val*y_max) + offset_y_val
        # self.xy_span = x_min, x_max, y_min, y_max
        self.text_xy.configure(text=f"x_min = {x_min}    x_max = {x_max}    y_min = {y_min}    y_max = {y_max}")


# Launch the app
Application(tk.Tk(), "Interface tricotissage")
