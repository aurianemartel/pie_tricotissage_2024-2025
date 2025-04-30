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

        button_dict = {"width":20, "height":1, "font": ("Arial", 10, "normal")}
        grid_dict = {"padx":5, "pady":10}

        tk.Label(text="Tricotissage", font=("Arial", 20,"bold")).grid(row=0,column=0,columnspan=3)

        # Chargement image et detection des tracés

        cell0 = tk.Frame(window, **grid_dict)
        cell0.grid(column=0,row=1)
        tk.Label(cell0,text="Nom de projet",**button_dict).pack(pady=5)
        self.nom_projet_entry = tk.Entry(cell0)
        self.nom_projet_entry.pack(pady=5)
        tk.Button(cell0,text="Sélection image", command=self.load_image,**button_dict).pack(pady=5)
        # tk.Button(cell0,text="Détection du tracé",**button_dict).pack(pady=5)
        tk.Button(cell0,text="Détection du tracé", command=self.run_elodie1, **button_dict).pack(pady=5)
        
        self.canvas_width = 420
        self.canvas_height = 300
        self.margin = 0

        self.canvas = tk.Canvas(window, width=self.canvas_width, 
                                height=self.canvas_height)
        self.canvas.grid(column=1, row=1, columnspan=2, **grid_dict)

        # Édition des points
        self.cell3 = tk.Frame(window, **grid_dict)

        
        tk.Button(self.cell3,text="Positions aiguilles", command=self.run_elodie2, **button_dict).pack(pady=15)



        # Génération des Gcodes
        self.cell4 = tk.Frame(window, **grid_dict)
        self.cell4.grid_rowconfigure(0, weight=1)
        self.cell4.grid_rowconfigure(1, weight=0)
        self.cell4.grid_columnconfigure(0, weight=1)
        self.cell4.grid_columnconfigure(1, weight=1)
        self.cell4.grid_columnconfigure(2, weight=1)

        tk.Button(self.cell4, text="Générer Gcode tricotissage", 
                  command=lambda: self.create_file(tricotissage), 
                  **button_dict).grid(row=0,column=0,pady=5)
        tk.Button(self.cell4, text="Générer Gcode marquage", 
                  command=lambda: self.create_file(marquage), 
                  **button_dict).grid(row=0,column=1,pady=5)
        self.message = tk.Label(self.cell4, text="", fg="green")
        self.message.grid(row=1,column=0,pady=5)

        self.window.mainloop()


    def create_file(self, func):
        nom_fichier = self.nom_projet_entry.get() or "file.yaml"
        result = func(PATH_YAML + nom_fichier)  # Appelle la fonction en argument
        self.message.config(text=f"{result}", fg="green")
    
    def run_elodie1(self):
        lx, ly, longueurs, pmpg = elodie1(self.file_path, epsilon=0.01, 
                                          afficher_im_init=False, 
                                          afficher_squelette=False)
        self.cell3.grid(column=0, row=2, columnspan=3)
        print("Tracé detecté")
    
    def run_elodie2(self):
        self.cell4.grid(column=0, row=3, columnspan=3)
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


# Launch the app
Application(tk.Tk(), "Interface tricotissage")
