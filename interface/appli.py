import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
from PIL import Image, ImageTk

import sys

sys.path.append('../pts2gcode')
from marq_tric import tricotissage, marquage
from to_yaml import create_yaml_file

sys.path.append('../detpts')
from det_trace import detection_trace
from generer_pos_aig import generer_pos_aiguilles

# TODO Mettre variables globales dans fichier séparé avec package dotenv
PATH_YAML = "../yaml_files/"
PATH_OUT = "../prgs_gcode/"
PATH_FIGURES = "../figures/"

MIN_ZOOM = 0
MAX_ZOOM = 2
ZOOM_INTERVAL = 0.5
MAX_OFFSETX_RATE = 1
MAX_OFFSETY_RATE = 1

DIM_MAX_Y = 350
DIM_MAX_Z = 600

EPSILON_DEFAULT = 8
DEFAULT_PROJECT_NAME = "Test"

VERBOSE = True  # Affichages terminal de commande

class Application:
    def __init__(self, window, window_title):
        self.window = window
        self.window.title(window_title)

        # Configuration de l'affichage
        window.grid_rowconfigure(0, weight=1)
        window.grid_rowconfigure(1, weight=1)
        window.grid_rowconfigure(2, weight=1)
        window.grid_rowconfigure(3, weight=1)
        window.grid_rowconfigure(4, weight=1)
        window.grid_rowconfigure(5, weight=1)
        window.grid_rowconfigure(6, weight=1)
        window.grid_rowconfigure(7, weight=1)
        window.grid_rowconfigure(8, weight=1)
        window.grid_rowconfigure(9, weight=1)
        window.grid_columnconfigure(0, weight=1)
        window.grid_columnconfigure(1, weight=1)
        window.grid_columnconfigure(2, weight=1)
        window.grid_columnconfigure(3, weight=1)
        window.grid_columnconfigure(4, weight=1)
        window.grid_columnconfigure(5, weight=1)

        self.button_dict = {"width":20, "height":1, "font": ("Arial", 10, "normal")}
        self.text_dict = {"font": ("Arial", 10, "normal")}
        self.grid_dict = {"padx":5, "pady":10}

        tk.Label(text="Tricotissage", font=("Arial", 20,"bold")).grid(row=0,column=0,columnspan=3)

        # Chargement image et detection des tracés : affichage de départ

        cell0 = tk.Frame(window, **self.grid_dict)
        cell0.grid(row=1, column=0)
        tk.Label(cell0,text="Nom de projet",**self.text_dict).pack(pady=5)
        self.nom_projet_entry = tk.Entry(cell0)
        self.nom_projet_entry.pack(pady=5)
        self.nom_projet_entry.insert(0, DEFAULT_PROJECT_NAME) # Valeur par défaut
        tk.Button(cell0,text="Sélection image", command=self.load_image,**self.button_dict).pack(pady=5)

        # Il faut lancer la détection du tracé pour afficher la suite
        tk.Button(cell0,text="Détection du tracé", command=self.run_detection_trace, **self.button_dict).pack(pady=5)

        self.canvas_width = 420
        self.canvas_height = 300
        self.margin = 0

        self.canvas = tk.Canvas(window, width=self.canvas_width, height=self.canvas_height)
        self.canvas.grid(row=1, column=1, columnspan=2, **self.grid_dict)
        
        if VERBOSE:
            print("Lancement de l'application")
        
        self.window.mainloop()
    

    # Fonctions du parcours utilisateur

    def run_detection_trace(self):
        # Gestion nom du projet : obligatoire pour passer à la suite
        self.nom_projet = self.nom_projet_entry.get()
        if not self.nom_projet:
            self.Erreur_nom_projet = tk.Label(text="Veuillez entrer un nom de projet", fg="red")
            self.Erreur_nom_projet.grid(row=2, column=0, columnspan=3)
            return
        
        # TODO : vérification qu'une image a été choisie
        
        if hasattr(self, 'Erreur_nom_projet'): # Teste si c'est affighé
            self.Erreur_nom_projet.destroy()

        ttk.Separator(self.window,orient='horizontal').grid(row=2, column=0, columnspan=3, sticky="ew")

        # Détection du tracé
        lx, ly, longueurs, self.pmpg = detection_trace(self.file_path, epsilon=0.01, 
                                          afficher_im_init=False, 
                                          afficher_squelette=False)
        if VERBOSE:
            print(f"Tracé detecté, pmpg : {self.pmpg}")

        # Affichage des min et max pour x et y : donne une bonne idée de la position du dessin sur l'image
        self.xy_span = self.min_max_pmpg()
        x_min, x_max, y_min, y_max = self.xy_span
        self.text_xy = tk.Label(self.window, **self.text_dict, 
                text=f"x_min = {x_min}    x_max = {x_max}    y_min = {y_min}    y_max = {y_max}")
        self.text_xy.grid(row=3, column=0, columnspan=3)

        # Offsets et zoom : modification de la position et taille du dessin par rapport au repère intégré 
        tk.Label(self.window, text="Zoom :", **self.text_dict).grid(row=4, column=0)
        self.zoom = tk.Scale(self.window, from_=MIN_ZOOM, to=MAX_ZOOM, tickinterval=ZOOM_INTERVAL, 
                             command=self.set_x_y_zoom, resolution=0.01, length=self.canvas_width, 
                             orient="horizontal")
        self.zoom.set(1)
        self.zoom.grid(row=4, column=1, columnspan=2)

        tk.Label(self.window, text="Offset en x :", **self.text_dict).grid(row=5, column=0)
        self.offset_x = tk.Scale(self.window, from_=-1*x_min, to=MAX_OFFSETX_RATE*x_max, 
                                 tickinterval=(x_max-x_min)//5, command=self.set_x_offset, 
                                 length=self.canvas_width, orient="horizontal")
        self.offset_x.grid(row=5, column=1, columnspan=2)

        tk.Label(self.window, text="Offset en y :", **self.text_dict).grid(row=6, column=0)        
        self.offset_y = tk.Scale(self.window, from_=-1*y_min, to=MAX_OFFSETY_RATE*y_max, 
                                 tickinterval=(y_max-y_min)//5, command=self.set_y_offset, 
                                 length=self.canvas_width, orient="horizontal")
        self.offset_y.grid(row=6, column=1, columnspan=2)

        # Choix du nombre de point par groupe (global) et validation
        ttk.Separator(self.window,orient='horizontal').grid(row=7, column=0, columnspan=3, sticky="ew")
        tk.Label(self.window, text="Points par groupe", **self.text_dict).grid(row=8, column=0, pady=5)
        self.pts_per_group_entry = tk.Entry(self.window)
        self.pts_per_group_entry.grid(row=8, column=1)
        tk.Button(self.window,text="Positions aiguilles", command=self.run_generer_pose_aiguilles, 
                  **self.button_dict).grid(row=8, column=2)

    
    def run_generer_pose_aiguilles(self):
        # TODO : vérifier validité des valeurs min et max pour x et y
        # On vérifie qu'il y a un nombre de points par groupe fixé
        pts_per_group = self.pts_per_group_entry.get()
        if not pts_per_group:
            self.Erreur_pts_per_group = tk.Label(text="Veuillez choisir un nombre de points par groupe", fg="red")
            self.Erreur_pts_per_group.grid(row=9, column=0, columnspan=3)
            return
        
        if hasattr(self, 'Erreur_pts_per_group'):
            self.Erreur_pts_per_group.destroy()

        # Mise en place du canvas pour l'affichage des points générés
        self.canvas_plot = tk.Canvas(self.window, width=self.canvas_width, height=self.canvas_height)
        self.canvas_plot.grid(row=1, column=3, columnspan=3, **self.grid_dict)

        nb_groupes = len(self.pmpg)
        nb_pts_per_group = [int(pts_per_group) for i in range(nb_groupes)]

        # Génération des points où seront les aiguilles         (apg = aiguilles_par_groupe)
        # TODO : generer_pos_aiguilles fait de l'effet de bord sur son premier argument, à corriger 
        # (il faut faire la copie dans la fonction et ne pas avoir à la faire en dehors)
        pmpg_bis = self.pmpg.copy()
        apg_array, lg_min = generer_pos_aiguilles(pmpg_bis, float(self.zoom.get()), float(self.offset_x.get()), 
                                        float(self.offset_y.get()), nb_pts_per_group, self.nom_projet)
        self.apg = [[[point.tolist()[1], point.tolist()[0]] for point in row] for row in apg_array]    
        self.load_plot(PATH_FIGURES + self.nom_projet + ".png")
        if VERBOSE:
            print(f"Points déterminés, apg : {self.apg}")
        
        # TODO : édition du nombre de points par groupe, par groupe séparé avec affichage distance min points

        if len(self.apg) == 2 :
            self.run_to_yaml()
        else:
            # Boutton de création du fichier yaml
            tk.Button(self.window,text="Création yaml", command=self.run_to_yaml, **self.button_dict).grid(row=2, column=5, padx=10)


    def run_to_yaml(self):
        # Création du yaml
        if len(self.apg) == 2:
            # Premier cas : lien par défaut
            group_data = {
                "groupe1": self.apg[0],
                "groupe2": self.apg[1],
            }
            link_data = [["groupe1", "groupe2"]]        
        
        # TODO : plus de deux groupes : selection de liens
        self.yaml_filename = PATH_YAML + self.nom_projet + ".yaml"

        create_yaml_file(self.nom_projet, DIM_MAX_Y, DIM_MAX_Z, link_data, group_data, self.yaml_filename, EPSILON_DEFAULT)
        if VERBOSE:
            print(f"Fichier YAML généré : {self.yaml_filename}")

        # Affichage boutons de génération d'instructions
        self.show_buttons_gcode()
        
    
    def show_buttons_gcode(self):
        # Génération des Gcodes
        tk.Button(self.window, text="Générer Gcode marquage", 
                  command=lambda: self.create_file(marquage), 
                  **self.button_dict).grid(row=8,column=4,pady=5)
        tk.Button(self.window, text="Générer Gcode tricotissage", 
                  command=lambda: self.create_file(tricotissage), 
                  **self.button_dict).grid(row=8,column=5,pady=5)
        self.message = tk.Label(self.window, text="", fg="green")
        self.message.grid(row=9,column=3,columnspan=3,pady=5)


    # Fonctions auxiliaires

    def create_file(self, func):
        result = func(self.yaml_filename)  # Appelle la fonction en argument
        self.message.config(text=f"{result}", fg="green")
        if VERBOSE:
            print(result)
        # TODO : effacer message si une autre fonction est déclenchée


    def load_image(self):
        self.file_path = filedialog.askopenfilename()
        if not self.file_path:
            return

        self.new_img = Image.open(self.file_path)
        self.resized_img = self.resize_image_to_fit(self.new_img)
        self.pic = ImageTk.PhotoImage(self.resized_img)

        if hasattr(self, 'image_label'):
            self.image_label.destroy()

        self.image_label = tk.Label(image=self.pic)
        self.image_label.image = self.pic 

        center_x = self.canvas_width // 2
        center_y = self.canvas_height // 2
        self.canvas.create_window(center_x, center_y, window=self.image_label)
    
    def load_plot(self, filename):

        self.new_plot = Image.open(filename)
        self.resized_plot = ImageTk.PhotoImage(self.resize_image_to_fit(self.new_plot))

        if hasattr(self, 'plot_label'):
            self.plot_label.destroy()

        self.plot_label = tk.Label(image=self.resized_plot)
        self.plot_label.image = self.resized_plot 

        center_x = self.canvas_width // 2
        center_y = self.canvas_height // 2
        self.canvas_plot.create_window(center_x, center_y, window=self.plot_label)


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
        self.text_xy.configure(
            text=f"x_min = {x_min}    x_max = {x_max}    y_min = {y_min}    y_max = {y_max}")
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
        self.text_xy.configure(
            text=f"x_min = {x_min}    x_max = {x_max}    y_min = {y_min}    y_max = {y_max}")

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
        self.text_xy.configure(
            text=f"x_min = {x_min}    x_max = {x_max}    y_min = {y_min}    y_max = {y_max}")


# Launch the app
Application(tk.Tk(), "Interface tricotissage")
