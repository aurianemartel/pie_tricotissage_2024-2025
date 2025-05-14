import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
from PIL import Image, ImageTk

import sys

sys.path.append('../pts2gcode')
from marq_tric import tricotissage, marquage
from marq_tric import OFFSET_Y as OFFSET_Y_BUSE
from marq_tric import OFFSET_Z as OFFSET_Z_BUSE
from to_yaml import create_yaml_file

sys.path.append('../detpts')
from det_trace import detection_trace
from generer_pos_aig import generer_pos_aiguilles

PATH_YAML = "../yaml_files/"
PATH_OUT = "../prgs_gcode/"
PATH_FIGURES = "../figures/"

MIN_ZOOM = 0
MAX_ZOOM = 2
ZOOM_INTERVAL = 0.5
MAX_OFFSETX_RATE = 1
MAX_OFFSETY_RATE = 1
MAX_PTS_PER_GROUP = 100

DIM_MAX_Y = 350
DIM_MAX_Z = 600

DEFAULT_PROJECT_NAME = "Nom_Projet"
EPSILON_MAX = 40

VERBOSE = True  # Affichages terminal de commande

class Application:
    def __init__(self, window, window_title):
        self.window = window
        self.window.title(window_title)

        # Configuration de l'affichage
        for i in range(12):
            window.grid_rowconfigure(i, weight=1)
        for i in range(7):
            window.grid_columnconfigure(i, weight=1)

        self.button_dict = {"width":20, "height":1, "font": ("Arial", 10, "normal")}
        self.text_dict = {"font": ("Arial", 10, "normal")}
        self.grid_dict = {"padx":5, "pady":10}

        tk.Label(text="Tricotissage", font=("Arial", 20,"bold")).grid(row=0,column=0,columnspan=7)

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

        self.canvas_width = 400
        self.canvas_height = 250
        self.margin = 0

        self.canvas = tk.Canvas(window, width=self.canvas_width, height=self.canvas_height)
        self.canvas.grid(row=1, column=1, columnspan=2, **self.grid_dict)
        
        if VERBOSE:
            print("Lancement de l'application")
        
        self.window.mainloop()
    

    # Fonctions du parcours utilisateur

    def run_detection_trace(self):
        # Gestion nom du projet et image : obligatoires pour passer à la suite
        self.nom_projet = self.nom_projet_entry.get()

        if not self.nom_projet:
            if not hasattr(self, 'Erreur_nom_projet'):
                self.Erreur_nom_projet = tk.Label(text="Veuillez entrer un nom de projet", fg="red")
                self.Erreur_nom_projet.grid(row=2, column=0, columnspan=3)
            return
        
        if hasattr(self, 'Erreur_nom_projet'): # Teste si c'est affiché
            self.Erreur_nom_projet.destroy()


        if (not hasattr(self, 'file_path')) or (not self.file_path):
            if not hasattr(self, 'Erreur_image'):
                self.Erreur_image = tk.Label(text="Veuillez choisir une image", fg="red")
                self.Erreur_image.grid(row=2, column=0, columnspan=3)
            return 

        if hasattr(self, 'Erreur_image'):
            self.Erreur_image.destroy()
        
        ttk.Separator(self.window,orient='horizontal').grid(row=2, column=0, columnspan=3, sticky="ew", pady=5)

        # Détection du tracé
        lx, ly, self.lgs_groups, self.pmpg = detection_trace(self.file_path, epsilon=0.01, 
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

        ttk.Separator(self.window,orient='horizontal').grid(row=7, column=0, columnspan=3, sticky="ew", pady=5)

        # Choix du nombre de point par groupe et validation
        self.nb_groupes = len(self.pmpg)
        self.nb_pts_per_group = [-1] * self.nb_groupes

        tk.Label(self.window, text="Nombre d'aiguilles par groupe", **self.text_dict).grid(row=8, column=0, pady=5)
        
        tk.Label(self.window, text="Groupe : ", **self.text_dict, justify='right').grid(row=8, column=1, pady=5, sticky="e")
        ids_groupes = list(range(1, self.nb_groupes+1)) + ["Tous"]
        self.cb_choix_groupe = ttk.Combobox(self.window, values=ids_groupes)
        self.cb_choix_groupe.grid(row=8, column=2, pady=5)

        tk.Label(self.window, text="Nombre d'aiguilles : ", **self.text_dict).grid(row=9, column=0, pady=5)
        pts_per_group_scale = tk.Scale(self.window, from_=0, to=MAX_PTS_PER_GROUP, tickinterval=MAX_PTS_PER_GROUP//5,
                                       command=self.set_nb_pts_group, length=self.canvas_width, orient="horizontal")
        pts_per_group_scale.grid(row=9, column=1, columnspan=2)

        tk.Label(self.window, text="Dist. entre les aiguilles : ", **self.text_dict).grid(row=10, column=0, pady=5)
        self.print_nb_pts_per_group = tk.Label(self.window, text="", **self.text_dict)
        self.print_nb_pts_per_group.grid(row=10, column=1, pady=5)

        tk.Button(self.window,text="Déterminer positions", command=self.run_generer_pos_aiguilles, 
                  **self.button_dict).grid(row=10, column=2)

    
    def run_generer_pos_aiguilles(self):

        zoom = float(self.zoom.get())
        offset_x = float(self.offset_x.get())
        offset_y = float(self.offset_y.get())

        x_min, x_max, y_min, y_max = self.xy_span
        x_min = zoom*x_min + offset_x
        x_max = zoom*x_max + offset_x
        y_min = zoom*y_min + offset_y
        y_max = zoom*y_max + offset_y

        # On vérifie validité des valeurs présentes en x et y
        if (x_min < max(OFFSET_Z_BUSE, 0)) or (y_min < max(OFFSET_Y_BUSE, 0)) \
        or (x_max>DIM_MAX_Z+OFFSET_Z_BUSE) or (y_max>DIM_MAX_Y+OFFSET_Y_BUSE):
            if not hasattr(self, 'Erreur_dims'):
                self.Erreur_dims = tk.Label(text=
"""Présence de valeurs non valables en x ou y,
attention aux dimensions max et à l'offset dû au décalage feutre - buse""", fg="red")
                self.Erreur_dims.grid(row=11, column=0, columnspan=3)
            return
        
        if hasattr(self, 'Erreur_dims'):
            self.Erreur_dims.destroy()
        
        if hasattr(self, 'Erreur_pts_per_group'):
            self.Erreur_pts_per_group.destroy()

        for i in range(self.nb_groupes):
            if self.nb_pts_per_group[i]<2:
                self.Erreur_pts_per_group = tk.Label(text=f"Le nombre d'aiguilles du groupe {i+1} doit être supérieur ou égal à 2", fg="red")
                self.Erreur_pts_per_group.grid(row=11, column=0, columnspan=3)
                return
        
        # Séparation entre parties gauche et droite
        ttk.Separator(self.window,orient='vertical').grid(row=1, column=3, rowspan=10, sticky="sn", padx=10)

        # Mise en place du canvas pour l'affichage des points générés
        self.canvas_plot = tk.Canvas(self.window, width=self.canvas_width, height=self.canvas_height)
        self.canvas_plot.grid(row=1, column=4, columnspan=3, **self.grid_dict)


        # Génération des points où seront les aiguilles         (apg = aiguilles_par_groupe)

        pmpg_bis = self.pmpg.copy()
        apg_array, lg_min = generer_pos_aiguilles(pmpg_bis, float(self.zoom.get()), float(self.offset_x.get()), 
                                        float(self.offset_y.get()), self.nb_pts_per_group, self.nom_projet)
        self.apg = [[[point.tolist()[1], point.tolist()[0]] for point in row] for row in apg_array]    
        # self.epsilon = min(EPSILON_MAX, lg_min/2) # Finalement, on prend le epslion généré par create_yaml_file
        self.load_plot(PATH_FIGURES + self.nom_projet + ".png")
        if VERBOSE:
            print(f"Points déterminés, apg : {self.apg}")
        
        # Gestion des liens 
        self.liste_liens = []

        tk.Label(self.window, text="Groupes tricotissés entre eux", 
                 font=("Arial", 12, "bold")).grid(row=2, column=4, columnspan=3, pady=5, padx=5)
        self.cell_liens = tk.Frame(self.window, **self.grid_dict)
        self.cell_liens.grid(row=3, column=4, columnspan=3, pady=5, padx=20, sticky="nesw")

        tk.Label(self.window, text="Ajouter deux groupes à tricotisser", 
                 font=("Arial", 12, "bold")).grid(row=4, column=4, columnspan=3, pady=5, padx=20)
        ids_groupes = list(range(1, self.nb_groupes+1))
        self.cb_choix_lien_1 = ttk.Combobox(self.window, values=ids_groupes, width=10)
        self.cb_choix_lien_1.grid(row=5, column=4, pady=5)
        self.cb_choix_lien_2 = ttk.Combobox(self.window, values=ids_groupes, width=10)
        self.cb_choix_lien_2.grid(row=5, column=5, pady=5)
        tk.Button(self.window, text="Ajouter", command=self.ajouter_lien, 
                  **self.button_dict).grid(row=5, column=6)

        if len(self.apg) == 2 :
            self.liste_liens.append(["groupe1", "groupe2"])
            #self.print_liste_liens.configure(text="- groupe1 et groupe2")
            tk.Label(self.cell_liens, text="- groupe 1 et groupe 2", justify='left', **self.text_dict).pack(anchor='w')
            self.run_to_yaml()
        
        # Boutton de création du fichier yaml
        tk.Button(self.window,text="Création yaml", command=self.run_to_yaml, **self.button_dict).grid(row=6, column=6, padx=10)


    def run_to_yaml(self):
        # Création du yaml  

        if len(self.liste_liens) == 0:
            if not hasattr(self, 'Erreur_liste_liens_vide'):
                self.Erreur_liste_liens_vide = tk.Label(text="Pas de tricotissage prévu", fg="red")
                self.Erreur_liste_liens_vide.grid(row=7, column=4, columnspan=3)
            return
        
        if hasattr(self, 'Erreur_liste_liens_vide'):
            self.Erreur_liste_liens_vide.destroy()
        
        group_data = {f"groupe{i+1}": self.apg[i] for i in range(self.nb_groupes)}        
        self.yaml_filename = PATH_YAML + self.nom_projet + ".yaml"

        create_yaml_file(self.nom_projet, DIM_MAX_Y, DIM_MAX_Z, self.liste_liens, group_data, self.yaml_filename)
        
        if VERBOSE:
            print(f"Fichier YAML généré : {self.yaml_filename}")

        tk.Label(text=f"Fichier {self.yaml_filename} généré avec succès", fg="green").grid(row=7, column=4, columnspan=3)

        # Affichage boutons de génération d'instructions
        self.show_buttons_gcode()
        
    
    def show_buttons_gcode(self):
        # Génération des Gcodes
        tk.Button(self.window, text="Générer Gcode marquage", 
                  command=lambda: self.create_file(marquage), 
                  **self.button_dict).grid(row=10,column=4,pady=5, columnspan=2)
        tk.Button(self.window, text="Générer Gcode tricotissage", 
                  command=lambda: self.create_file(tricotissage), 
                  **self.button_dict).grid(row=10,column=6,pady=5)
        self.message = tk.Label(self.window, text="", fg="green")
        self.message.grid(row=11,column=4,columnspan=3,pady=5)


    # Fonctions auxiliaires

    def create_file(self, func):
        result = func(self.yaml_filename)  # Appelle la fonction en argument
        self.message.config(text=f"{result}", fg="green")
        if VERBOSE:
            print(result)

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
        self.text_xy.configure(
            text=f"x_min = {x_min}    x_max = {x_max}    y_min = {y_min}    y_max = {y_max}")

    def set_nb_pts_group(self, val):
        '''
        Cette méthode permet de sélectionner le nombre d'aiguilles d'un groupe, ou de tous, via un slider. 
        Elle affiche aussi la distance entre les aiguilles (minimale si pour tous les groupes)'''

        num_groupe = self.cb_choix_groupe.get()
        nb_pts = int(val)
        if num_groupe == "Tous":
            for i in range(self.nb_groupes):
                self.nb_pts_per_group[i] = nb_pts
            self.print_nb_pts_per_group.configure(text=f"{ round( float(self.lgs_groups[0]) / nb_pts, 2 ) }")

            if VERBOSE:
                print(f"Même nombre d'aiguilles pour tous les groupes : {nb_pts} aiguilles")
        
        else:
            num_groupe = int(num_groupe)-1
            self.nb_pts_per_group[int(num_groupe)] = nb_pts
            self.print_nb_pts_per_group.configure(text=f"{ round( float(self.lgs_groups[num_groupe]) / nb_pts, 2 ) }")

            if VERBOSE:
                print(f"Nombre d'aiguilles pour groupe {num_groupe} : {nb_pts} aiguilles")
    
    def ajouter_lien(self):
        groupe_fst = self.cb_choix_lien_1.get()
        groupe_snd = self.cb_choix_lien_2.get()

        if hasattr(self, 'Erreur_mauvais_lien'):
            self.Erreur_mauvais_lien.destroy()
        
        if (not groupe_fst) or (not groupe_snd) or (groupe_fst == groupe_snd):
            self.Erreur_mauvais_lien = tk.Label(text="Lien non valide", fg="red")
            self.Erreur_mauvais_lien.grid(row=7, column=4, columnspan=3)
            return

        groupe_fst = int(groupe_fst)
        groupe_snd = int(groupe_snd)

        self.liste_liens.append([f"groupe{groupe_fst}", f"groupe{groupe_snd}"])
        # self.print_liste_liens.configure(text=f"- groupe{groupe_fst} et groupe{groupe_snd}")
        tk.Label(self.cell_liens, text=f"- groupe {groupe_fst} et groupe {groupe_snd}", justify='left', 
                 **self.text_dict).pack(anchor='w')

# Launch the app
Application(tk.Tk(), "Interface tricotissage")
