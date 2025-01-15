#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import pandas as pd 

# Lire le fichier Excel 

excel_file = "chemin_d'acces_a_l'Excel" 

df = pd.read_excel(excel_file) 

# Ouvrir un fichier pour ecrire le G-code 

output_file = "marquage.gcode" 

with open(output_file, "w") as file: 

    # En-tete du fichier G-code  

    file.write("G21 ; Definir les unites en millimetres\n")  

    file.write("G90 ; Positionnement absolu\n") 

    file.write("G17 ; XY plan\n") 
    
    file.write("G40\nG49\n") 

    file.write("G0 X0 Y0\n \n") #position de depart


    # Parcourir les donnees du DataFrame 

    for index, row in df.iterrows(): 

        # Recuperer les valeurs des colonnes X, Y, Z 

        x = row['COORD_X']  

        y = row['COORD_Y'] 

        z = row['ANGLE'] 

        a = row['COORD_X2'] 

        b = row['COORD_Y2'] 

        c = row['ANGLE2'] 

        # Generer la commande G-code appropriee 

            if not (pd.isnull(df.loc[index, 'COORD_X'])):

            file.write(f"G1 X{x} Y{y}\nM0 ; Mettre en pause le programme\n;MSG Appuyer sur le bouton jusqu'a ce que la position soit marquee\n")
        
        if not (pd.isnull(df.loc[index, 'COORD_X2'])):
            
            file.write(f"G1 X{a} Y{b}\nM0 ; Mettre en pause le programme\n;MSG Appuyer sur le bouton jusqu'a ce que la position soit marquee\n") 
            
    file.write("G0 X0 Y0\n") #position de fin

print("Fichier G-code genere avec succes.") 