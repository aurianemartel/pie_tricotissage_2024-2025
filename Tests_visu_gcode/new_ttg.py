'''
Améliorations
-> Fichiers en commun marquage et tricotissage
-> Factoriser
-> Plusieurs fonctions

Fonctions :
- en-tête
- mouvements (G0, G2, G3)
- marquage
- tricotissage





Cas du conflit aiguille-fil
V1. Supposer que le tricotissage demandé est ok, afficher
V2. Vérifier si certains trajets posent problème (à 5mm d'une autre aiguille ou derrière)
V3. Proposer une résolution automatique : couper en plusieurs étapes
'''

import yaml
import sys


def enTete(dim_y, dim_z):
    return f'''G21 ; Definir les unites en millimetres
G90 ; Positionnement absolu
G19 ; YZ plan
G40
G49
G0 Y{dim_y} Z{dim_z}

'''

def G0(y, z): #Aller à (y,z) par une ligne droite
    return f"G0 Y{y} Z{z}\n"

def G2(yi, zi, yf, zf, cy, cz): #Aller à (y,z) en arc de cercle anti-horaire de centre (cy,cz)
    #Vérifier validité du cercle
    return f"G2...\n" #À écrire

def G3(y, z, cy, cz): #Aller à (y,z) en arc de cercle horaire de centre (cy,cz)
    #Vérifier validité du cercle
    return f"G3...\n" #À écrire


def marquage(yamlFile):
    with open(yamlFile,'r') as file:
        data = yaml.safe_load(file)
    with open(f"{data['nom']}.gcode",'w') as marq:
        dim_y, dim_z = data['dimensions']
        marq.write(enTete(dim_y,dim_z))
        for groupe in data['groupes']:
            for point in data['groupes'][groupe]:
                marq.write(G0(point[0], point[1]))
                marq.write("M0\n") #Pause
                #descendre et relever crayon
    print(f"Fichier {data['nom']}.gcode généré avec succès")


def tricotissage(yamlFile):
    #Ouverture fichier de données
    with open(yamlFile,'r') as file:
        data = yaml.safe_load(file)

    
    #Ouverture fichier gcode à écrire
    #Boucle sur les liens : entre quels groupes je tricotisse
        #Premier point : tour complet autour de l'aiguille
        #Boucles sur chaque groupe : entre quels points je tricotisse
        #Premier groupe du lien
            #Deuxième groupe du lien -> à déterminer
                #Aller vers un point (à côté) : G0
                #Contourner deux aiguilles : G2
                #Retour vers point suivant
            #Revenir vers point suivant
        #Dernier point : tour complet, transition entre groupes ?


if __name__ == "__main__":
    if sys.argv[1][0] == 'm':
        if len(sys.argv) > 2:
            yamlFile = sys.argv[1]
        else:
            yamlFile = "file.yaml"
        marquage(yamlFile)

