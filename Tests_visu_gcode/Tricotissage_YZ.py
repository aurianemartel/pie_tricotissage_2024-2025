#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
TO DO :
- modif axes XY en axes YZ
- supprimer fonction double buse
- passer df en dictionnaires
- charger yaml en dictionnaire

-> à partir du yaml, boucle sur "liens", puis boucles sur les groupes
-> fonctions pour générer G0 et G2, strings en f"...{}..." (fstrings)
'''

import pandas as pd
import sys

# Lire le fichier Excel 

if len(sys.argv) > 1:
    excel_file = sys.argv[1]
else:
    excel_file = "test-tricotissage.xlsx" 

df = pd.read_excel(excel_file)  

# Ouvrir un fichier pour ecrire le G-code 

output_file = f"{excel_file}.gcode"
dim_y, dim_z = 350, 650

with open(output_file, "w") as file: 
    # En-tete du fichier G-code  
    file.write(
f'''G21 ; Definir les unites en millimetres
G90 ; Positionnement absolu
G19 ; YZ plan
G40
G49
G0 Y{dim_y} Z{dim_z}


''') #ou dim_y et dim_z sont les dimensions de la surface de travail apres calibration

    position = 0 #position des buses pour les aiguilles  3 premieres colonnes
    position2 = 0 #position des buses pour les aiguilles 3 dernieres colonnes
    premiere = 0 #pour savoir si c'est la premiere aiguille

    # Parcourir les donnees du DataFrame 
    for index, row in df.iterrows(): 
        if index != len(df)-1 and index%2==0:
            # Parcourir les donnees deux lignes a la fois  
            ligne1 = df.iloc[index]
            ligne2 = df.iloc[index+1]
            combine = pd.concat([ligne1, ligne2])

            if not (pd.isnull(df.loc[index, 'COORD_X'])):    
                #on donne la position des buses pour le groupe d'aiguilles
                if (abs(combine[0]-combine[6])<abs(combine[1]-combine[7])): #Buses selon y, on doit tricotisser avec l'aiguille la plus basse 
                    file.write("M0 ; Mettre en pause le programme \n;MSG Maintenir le bouton enfonce \n") 
                    position = 1
            
                    # Generer la commande G-code appropriee pour cette aiguille 
                    if (combine[6]<combine[7]):
                        file.write("G0 X{}\n".format(combine[6] - 5 + 9.9)) #on se place en bas a gauche 
                        file.write("G0 Y{}\n".format(combine[7] - 5))
                    else : 
                        file.write("G0 Y{}\n".format(combine[7] - 5)) #on se place en bas a gauche 
                        file.write("G0 X{}\n".format(combine[6] - 5 + 9.9))
                        
                    # on memorise les coordonnees de l'aiguille utilisee
                    x = combine[6]
                    y = combine[7] 
                    z = combine[8]
                else : #aiguilles selon x
                    # Generer la commande G-code appropriee pour cette aiguille 
                    if (combine[0]<combine[1]):
                        file.write("G0 X{}\n".format(combine[0] - 5 + 9.9)) #on se place en bas a gauche de la premiere aiguille du groupe a contourner 
                        file.write("G0 Y{}\n".format(combine[1] - 5))
                    else : 
                        file.write("G0 Y{}\n".format(combine[1] - 5)) #on se place en bas a gauche de la premiere aiguille du groupe a contourner 
                        file.write("G0 X{}\n".format(combine[0] - 5 + 9.9))
                    
                    # on memorise les coordonnees de l'aiguille utilisee
                    x = combine[0] 
                    y = combine[1]
                    z = combine[2]
                
                #tour complet si premiere aiguille
                if (premiere==0):
                    file.write("G2 X{} Y{} I{} J{} \n \n".format(x-5+9.9, y-5, 5, 5)) 
                    file.write("G2 X{} Y{} I{} J{} \n \n".format(x+5+9.9, y+5, 5, 5)) 
                    premiere = 1
                else : 
                    file.write("G2 X{} Y{} I{} J{} \n \n".format(x+5+9.9, y+5, 5, 5))
                     
                # Recherche des autres aiguilles dans le meme groupe              
                same_group = df[df['ANGLE2'] == z]
                for index2, other_row in same_group.reset_index(drop=True).iterrows(): #indice pour la deuxieme aiguille
                    if index2 < len(same_group)-1:
                        # Recuperer les valeurs pour les autres aiguilles dans le meme groupe 
                        a_other = other_row['COORD_X2'] 
                        b_other = other_row['COORD_Y2']
                    
                        if not (pd.isnull(df.loc[index2, 'COORD_X2'])):
                            group1 = same_group.iloc[index2] 
                            group2 = same_group.iloc[index2+1] 
                            tableau = pd.concat([group1, group2])
                            
                            #Posititon des buses pour tricotisser l'aiguille des dernieres colonnes
                            if (abs(tableau[9]-a_other)>=abs(tableau[10]-b_other)):
                                position2 = 0
                                file.write("M0 ; Mettre en pause le programme \n;MSG Lacher le bouton \n \n")
                            else: 
                                position2 = 1
                                file.write("M0 ; Mettre en pause le programme \n;MSG Maintenir le bouton enfonce \n \n")
                            
                            if tableau[3]>=tableau[9]:
                                X1=tableau[3]
                                X2=tableau[9]
                            else :
                                X1=tableau[9]
                                X2=tableau[3]
                            
                            #Les buses arrivent par la gauche et les aiguilles sont selon y 
                            if (position2==1)and(x <= tableau[3])and(X1!=X2): 
                                file.write("G0 X{} Y{}\n".format(X2-abs((X1-X2)/2)+9.9, tableau[10]-abs((tableau[10]-tableau[4])/2)))
                                file.write("G0 X{} Y{}\n".format(X1+abs((X1-X2)/2)+9.9, tableau[10]-abs((tableau[10]-tableau[4])/2)))
                                file.write("G3 X{} Y{} I{} J{}\n".format(X1+abs((X1-X2)/2)+9.9, tableau[10]+abs((tableau[10]-tableau[4])/2), -abs((X1-X2)/2), abs((tableau[10]-tableau[4])/2)))
                                file.write("G0 X{} Y{}\n \n".format(X2-abs((X1-X2)/2)+9.9, tableau[10]+abs((tableau[10]-tableau[4])/2)))
                                
                            #Les buses arrivent par la gauche et les aiguilles sont selon y 
                            elif (position2==1)and(x <= tableau[3])and(X1==X2): 
                                file.write("G0 X{} Y{}\n".format(X2 - 5 + 9.9, tableau[10]-abs((tableau[10]-tableau[4])/2)))
                                file.write("G0 X{} Y{}\n".format(X1 + 5 + 9.9, tableau[10]-abs((tableau[10]-tableau[4])/2)))
                                file.write("G3 X{} Y{} I{} J{}\n".format(X1 + 5 + 9.9, tableau[10]+abs((tableau[10]-tableau[4])/2), -5, abs((tableau[10]-tableau[4])/2)))
                                file.write("G0 X{} Y{}\n \n".format(X2 - 5 + 9.9, tableau[10]+abs((tableau[10]-tableau[4])/2)))
                                           
                            #Les buses arrivent par la droite et les aiguilles sont selon y 
                            elif (position2==1)and(x > tableau[3])and(X1!=X2): 
                                file.write("G0 X{} Y{}\n".format(X1+abs((X1-X2)/2)+9.9, tableau[10]-abs((tableau[10]-tableau[4])/2)))
                                file.write("G0 X{} Y{}\n".format(X2-abs((X1-X2)/2)+9.9, tableau[10]-abs((tableau[10]-tableau[4])/2)))
                                file.write("G2 X{} Y{} I{} J{}\n".format(X2-abs((X1-X2)/2)+9.9, tableau[10]+abs((tableau[10]-tableau[4])/2), abs((X1-X2)/2), abs((tableau[10]-tableau[4])/2)))
                                file.write("G0 X{} Y{}\n \n".format(X1+abs((X1-X2)/2)+9.9, tableau[10]+abs((tableau[10]-tableau[4])/2)))
                                
                            #Les buses arrivent par la droite et les aiguilles sont selon y 
                            elif (position2==1)and(x > tableau[3])and(X1==X2): 
                                 file.write("G0 X{} Y{}\n".format(X1 + 5 + 9.9, tableau[10]-abs((tableau[10]-tableau[4])/2)))
                                 file.write("G0 X{} Y{}\n".format(X2 - 5 + 9.9, tableau[10]-abs((tableau[10]-tableau[4])/2)))
                                 file.write("G2 X{} Y{} I{} J{}\n"
                                            .format(X2 - 5 + 9.9, 
                                                    tableau[10]+abs((tableau[10]-tableau[4])/2), 
                                                    5, 
                                                    abs((tableau[10]-tableau[4])/2)))
                                 file.write("G0 X{} Y{}\n \n".format(X1 + 5 + 9.9, tableau[10]+abs((tableau[10]-tableau[4])/2)))
                           
                            if tableau[4]>=tableau[10]:
                                Y1=tableau[4]
                                Y2=tableau[10]
                            else :
                                Y1=tableau[10]
                                Y2=tableau[4]
                                
                            #Les buses arrivent par le bas et les aiguilles sont selon x
                            if (position2==0)and(y <= tableau[4])and(Y1!=Y2):
                               file.write("G0 X{} Y{}\n"
                                          .format(X1+abs((X1-X2)/2)+9.9, 
                                                  Y2-abs((tableau[10]-tableau[4])/2)))
                               file.write("G0 X{} Y{}\n".format(X1+abs((X1-X2)/2)+9.9, Y1+abs((tableau[10]-tableau[4])/2)))
                               file.write("G3 X{} Y{} I{} J{}\n".format(X1-abs((X1-X2)/2)+9.9, Y1+abs((tableau[10]-tableau[4])/2), -abs((X1-X2)/2), -abs((tableau[10]-tableau[4])/2)))
                               file.write("G0 X{} Y{}\n \n".format(X1-abs((X1-X2)/2)+9.9, Y2-abs((tableau[10]-tableau[4])/2)))
                               
                            #Les buses arrivent par le bas et les aiguilles sont selon x
                            elif (position2==0)and(y <= tableau[4])and(Y1==Y2):
                               file.write("G0 X{} Y{}\n".format(X1+abs((X1-X2)/2)+9.9, Y2 - 5))
                               file.write("G0 X{} Y{}\n".format(X1+abs((X1-X2)/2)+9.9, Y1 + 5))
                               file.write("G3 X{} Y{} I{} J{}\n".format(X1-abs((X1-X2)/2)+9.9, Y1 + 5, -abs((X1-X2)/2), -5))
                               file.write("G0 X{} Y{}\n \n".format(X1-abs((X1-X2)/2)+9.9, Y2 - 5))
                           
                            #Les buses arrivent par le haut et les aiguilles sont selon x
                            elif (position2==0)and(y > tableau[4])and(Y1!=Y2):
                                file.write("G0 X{} Y{}\n".format(X1+abs((X1-X2)/2)+9.9, Y1+abs((tableau[10]-tableau[4])/2)))
                                file.write("G0 X{} Y{}\n".format(X1+abs((X1-X2)/2)+9.9, Y2-abs((tableau[10]-tableau[4])/2)))
                                file.write("G2 X{} Y{} I{} J{}\n"
                                           .format(X1-abs((X1-X2)/2)+9.9,
                                                   Y2-abs((tableau[10]-tableau[4])/2), 
                                                   -abs((X1-X2)/2), 
                                                   abs((tableau[10]-tableau[4])/2)))
                                file.write("G0 X{} Y{}\n \n".format(X1-abs((X1-X2)/2)+9.9, Y1+abs((tableau[10]-tableau[4])/2)))
                                
                            #Les buses arrivent par le haut et les aiguilles sont selon x
                            elif (position2==0)and(y > tableau[4])and(Y1==Y2):
                                file.write("G0 X{} Y{}\n".format(X1+abs((X1-X2)/2)+9.9, Y1 + 5))
                                file.write("G0 X{} Y{}\n".format(X1+abs((X1-X2)/2)+9.9, Y2 - 5))
                                file.write("G2 X{} Y{} I{} J{}\n".format(X1-abs((X1-X2)/2)+9.9, Y2 - 5, -abs((X1-X2)/2), 5))
                                file.write("G0 X{} Y{}\n \n".format(X1-abs((X1-X2)/2)+9.9, Y1 + 5))
                               
                            #on remet les buses a la position de base pour revenir a la premiere aiguille
                            if position == 0:
                                file.write("M0 ; Mettre en pause le programme \n;MSG Lacher le bouton \n \n")
                            else: 
                                file.write("M0 ; Mettre en pause le programme \n;MSG Maintenir le bouton enfonce \n \n")
                                
                            file.write("G0 X{} Y{}\n".format(x - 5 + 9.9, y - 5)) #il faut faire le tour de cette aiguille 
                            file.write("G2 X{} Y{} I{} J{}\n \n".format(x-5 + 9.9, y-5, 5, 5))
                     
                file.write(";MSG Decouper le fil \n \n")
                file.write(f"G0 X{dim_y} Y{dim_z}\n \n") #ou x et y sont les dimensions de la surface de travail apres calibration
    
print("Fichier G-code genere avec succes.") 
