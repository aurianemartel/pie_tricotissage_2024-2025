'''
Fonctions :
- en-tête
- mouvements (G0, G2, G3)
- marquage
- tricotissage
# TODO : décrire les fonctions importantes


Cas du conflit aiguille-fil
V1. Supposer que le tricotissage demandé est ok, afficher
V2. Vérifier si certains trajets posent problème (à 5mm d'une autre aiguille ou derrière)
V3. Proposer une résolution automatique : couper en plusieurs étapes
'''

import yaml
import sys

PATH_OUT = "../prgs_gcode/"
PATH_YAML = "../yaml_files/"
EPSILON = 20         # Distance aux aiguilles des points de passages, en y et en z

def enTete(dim_y, dim_z):
    return f'''G21 ; Definir les unites en millimetres
G90 ; Positionnement absolu
G19 ; YZ plan
G40
G49
F10000

G0 Y0 Z0

'''


'''
G0 Y{dim_y} Z0
G0 Y{dim_y} Z{dim_z}
G0 Y0 Z{dim_z}
G0 Y0 Z0

'''

'''
Fonctions de mouvement
'''

def G0(y, z): #Aller à (y,z) rapidement, par une ligne droite
    return f"G0 Y{y} Z{z}"

def G1(y, z): #Aller à (y,z) par une ligne droite à la vitesse donnée par F
    return f"G1 Y{y} Z{z}"

def G2(yi,zi,yf,zf,cy,cz): #Aller à (y,z) en arc de cercle anti-horaire de centre (cy,cz)
    return f"G2 Y{yf} Z{zf} J{cy-yi} K{cz-zi}"

def G3(yi,zi,yf,zf,cy,cz): #Aller à (y,z) en arc de cercle horaire de centre (cy,cz)
    return f"G3 Y{yf} Z{zf} J{cy-yi} K{cz-zi}"

def G23(yi,zi,yf,zf,cy,cz,sens):
    """Retourne le résultat de G2 ou G3 selon le sens de rotation nécessaire"""
    if sens == -1: # sens indirect
        return G2(yi,zi,yf,zf,cy,cz)
    elif sens == 1: # sens direct
        return G3(yi,zi,yf,zf,cy,cz)
    else :
        print("Problème : sens non valide")
        return ""


'''
Marquage
'''

def marquage(yamlFile):
    """
    Crée le fichier gcode de marquage associé au patron décrit dans le fichier yaml en argument.
    """
    with open(yamlFile,'r') as file:
        data = yaml.safe_load(file)
    with open(PATH_OUT + f"marq_{data['nom']}.gcode",'w') as marq:
        dim_y, dim_z = data['dimensions']
        marq.write(enTete(dim_y,dim_z))
        #marq.write("M5 S1000\n\n")
        for groupe in data['groupes']:
            for point in data['groupes'][groupe]:
                marq.write(G0(point[0], point[1]))
                #marq.write("M3\nG4 P1 \nM5\n\n") #descendre et relever crayon
                marq.write("\nM0\n\n")
    print(f"Fichier marq_{data['nom']}.gcode généré avec succès")

'''
Tricotissage
'''

def parcours(groupe1, groupe2):
    """
    Décrit le parcours du fil autour des aiguilles

    Points = liste de deux coordonnnées décrivant la position d'une aiguille

    Args :
        groupe1 (list): liste de points
        groupe2 (list): liste de points
    
    Returns :
        list: liste de points
        """
    l1 = len(groupe1)
    l2 = len(groupe2)

    # initialisation : on se place au premier point du parcours
    prc = [groupe1[0]]

    for i in range(l1-1):
        # on est déjà en groupe1[i], pas besoin d'y aller
        prc.append(groupe2[0])
        prc.append(groupe2[1])
        prc.append(groupe1[i+1])

        # boucle sur les autres i
        for j in range(1,l2-1):
            prc.append(groupe1[i])
            prc.append(groupe2[j])
            prc.append(groupe2[j+1])
            prc.append(groupe1[i+1])
    return prc


def vect(pt1,pt2):
    return [pt2[0]-pt1[0],pt2[1]-pt1[1]]

def norme(u):
    return (u[0]**2+u[1]**2)**.5

def sens_arc(u,v):
    if u[0]*v[1]-u[1]*v[0] > 0:
        sens = 1 # sens direct
    elif u[0]*v[1]-u[1]*v[0] < 0:
        sens = -1 # sens indirect
    else :
        sens = 0
        print("Problème : vecteurs colinéaires\n")
    return sens


def pointsPassage(pt1, pt2, pt3, epsilon):
    """Retourne les points par lesquels passer pour contourner pt2 vers pt3, 
        et le sens de l'arc de cercle entre ces points"""
    assert (pt1 != pt2) & (pt1 != pt3) & (pt2 != pt3)
    
    u = vect(pt1,pt2)
    v = vect(pt2,pt3)
    sens = sens_arc(u,v)

    #pp2 = [pt2[0] + epsilon*u[0]/norme(u), pt2[1] + epsilon*u[1]/norme(u)]
    #pp1 = [pt2[0] - epsilon*v[0]/norme(v), pt2[1] - epsilon*v[1]/norme(v)]

    pp1 = [pt2[0] + sens*(-1)*epsilon*u[1]/norme(u), pt2[1] + sens*epsilon*u[0]/norme(u)]
    pp2 = [pt2[0] + sens*(-1)*epsilon*v[1]/norme(v), pt2[1] + sens*epsilon*v[0]/norme(v)]

    return pp1, pp2, sens

def trace(prc, epsilon):
    chemin = ""
    # Initialiser le tricotissage : cercle autour de la première aiguille
    u = vect(prc[3],prc[0])
    v = vect(prc[0],prc[1])
    pp1 = [prc[0][0] + epsilon*u[0]/norme(u), prc[0][1] + epsilon*u[1]/norme(u)]
    sens = sens_arc(u,v)
    chemin += f'''{G0(pp1[0],pp1[1])}
M0

{G23(pp1[0],pp1[1],pp1[0],pp1[1],prc[0][0],prc[0][1],sens)}
'''
    # Boucle sur le parcours
    l = len(prc)
    for i in range(l-2):
        pp1, pp2, sens = pointsPassage(prc[i],prc[i+1],prc[i+2], epsilon)
        chemin += f'''{G1(pp1[0],pp1[1])}
{G23(pp1[0],pp1[1],pp2[0],pp2[1],prc[i+1][0],prc[i+1][1],sens)}

'''        
    #Finaliser le tricotissage : gestion du dernier point
    u = vect(prc[l-4],prc[l-1])
    v = vect(prc[l-2],prc[l-1])
    pp1 = [prc[l-1][0] + epsilon*u[0]/norme(u), prc[l-1][1] + epsilon*u[1]/norme(u)]
    sens = sens_arc(u,v)
    chemin += f'''{G1(pp1[0],pp1[1])}
{G23(pp1[0],pp1[1],pp1[0],pp1[1],prc[l-1][0],prc[l-1][1],sens)}
'''
    return chemin

def tricotissage(yamlFile):
    # Récupération des données
    with open(yamlFile,'r') as file:
        data = yaml.safe_load(file)
    dim_y, dim_z = data['dimensions']
    epsilon = data['epsilon']
    
    with open(PATH_OUT + f"tric_{data['nom']}.gcode",'w') as tric:
        tric.write(enTete(dim_y,dim_z))

        for lien in data['liens']:
            # Création du parcours de tricotissage
            prc = parcours(data["groupes"][lien[0]],data["groupes"][lien[1]])
            tric.write(trace(prc, epsilon))

    print(f"Fichier tric_{data['nom']}.gcode généré avec succès")

'''
Main
'''

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1][0] == 'm':
            if len(sys.argv) > 2:
                yamlFile = PATH_YAML + sys.argv[2]
            else:
                yamlFile = PATH_YAML + "file.yaml"
            marquage(yamlFile)
        elif sys.argv[1][0] == 't':
            if len(sys.argv) > 2:
                yamlFile = PATH_YAML + sys.argv[2]
            else:
                yamlFile = PATH_YAML + "file.yaml"
            tricotissage(yamlFile)
    else :
        print("Please provide command and file\n")