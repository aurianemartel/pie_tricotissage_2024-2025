"""Etant donnée les différents groupes approximés par des droites par morceaux et le nombre d'aiguilles pour chacun
des groupes, ainsi que des paramètres pour rescale la figure, renvoie la position des aiguilles"""

"""REGARDER raffiner_approx_affine2"""
import numpy as np
from main import longueur_approx_morceaux
from main import raffiner_approx_affine
import matplotlib.pyplot as plt

def raffiner_approx_affine2(points, n):
    """si points a été obtenu à partir de approx_morceaux, permet de placer n points équidistants sur la forme
    approximée; appelée par plot_aiguille,
    renvoie un tableau de points, traite un seul groupe à la fois"""
    longueur = 0
    for i, point in enumerate(points):
        actuel = np.array(point)     #converti un tuple en np.array, qui supporte la soustraction
        if i > 0:
            longueur += np.linalg.norm(actuel - prec)
        prec = actuel
    longueur = longueur_approx_morceaux(points)         #longueur totale du contour
    longueur_segment = longueur / (n-1)             #longueur entre deux aiguilles consécutives
    longueur_restante = longueur_segment
    actuel = np.array(points[0])
    actuel = actuel.astype(np.float64)       #pour pouvoir gérer des opérations faisant intervenir des flottants
    #print(actuel.dtype)
    suivant = np.array(points[1])
    suivant = suivant.astype(np.float64)       #pour pouvoir gérer des opérations faisant intervenir des flottants
    i = 1       #numéro du point suivant
    direction = (suivant - actuel) / np.linalg.norm(suivant - actuel)
    nouveaux_points = [actuel]
    j = 1           #nombre d'aiguilles placées
    #while i <= len(points) - 1:
    #print("longueur_segment : ", longueur_segment, "\n")
    #print("longueur : ", longueur, "\n")
    while j < n - 1:
        #print("i: ", i, "j : ", j, "debug_longueur_utilisee:", debug_longueur_utilisee, "longueur : ", longueur, "longueur_restante", longueur_restante, "longueur suivant-actuel : ", np.linalg.norm(actuel - suivant) )
        #print("Dans le gros while", "j : ", j)
        #print("i, j raffiner approx affine : ", i, j)
        if (np.linalg.norm(actuel - suivant) >= longueur_restante):   #on a la place de rajouter un point sur ce morceau
            #print("Dans le if")
            actuel += longueur_restante * direction
            longueur_restante = longueur_segment
            #print(actuel)
            nouveaux_points.append(actuel)
            j += 1
            #print(nouveaux_points)
        else:           #pas la place de rajouter un point sur le morceau
            #print("Dans le else")
            i += 1  #on passe au morceau suivant
            if i < len(points) - 1:     #il reste encore au moins un morceau
                longueur_restante -= np.linalg.norm(actuel - suivant)
                #print(suivant.dtype)
                #print("suivant (=actuel), points[i] : ", suivant, points[i])
                actuel = suivant
                suivant = points[i]
                suivant = suivant.astype(np.float64)
                #print("suivant, actuel : ", suivant, actuel)
                while (np.linalg.norm(suivant - actuel) == 0) and i < (len(points) - 1):
                    #JE NE COMPRENDS PAS POURQUOI MAIS DE MANIERE NON DETERMINISTE, DES POINTS SUCCESSIFS SONT PARFOIS
                    #IDENTIQUES
                    #print("Dans le while", "i :", i, "len(points) : ", len(points))
                    i+=1
                    actuel = suivant
                    suivant = points[i]
                    suivant = suivant.astype(np.float64)
                #print("suivant, actuel : ", suivant, actuel)
                #print("Hors du while")
                direction = (suivant - actuel) / np.linalg.norm(suivant - actuel)
    if np.linalg.norm(suivant - actuel) != 0:  #on force l'ajout du dernier point
        nouveaux_points.append(points[-1])
    #print("Nouveaux_points : ", nouveaux_points)
    return nouveaux_points


def pos_aiguilles(points_morceaux_par_gpe, n):
    """Renvoie la position des aiguilles avec n points par groupe (n tableau, peu différer pour chaque groupe)
    sous la forme d'un tableau tab tel que tab[i] """
    #aiguilles_par_gpe = [[] for _ in range(len(points_morceaux_par_gpe))]
    aiguilles_par_gpe = []
    for i, points in enumerate(points_morceaux_par_gpe):
        aiguilles_par_gpe.append(raffiner_approx_affine2(points,n[i]))
        """points_raffines = raffiner_approx_affine2(points,n[i])
        #print(points_raffines)
        j = 0
        while j < len(points_raffines) - 2:
            print("i pos_aiguilles : ", i)
            print("len points_raffines : ", len(points_raffines))
            print("len aiguilles_par_gpe : ", len(aiguilles_par_gpe))
            aiguilles_par_gpe[i] = (aiguilles_par_gpe[i]).append((points_raffines[j], points_raffines[j+1]))
            j += 2
        """
    #print(aiguilles_par_gpe)
    return aiguilles_par_gpe

def rescale(points_morceaux_par_gpe, scale_factor, offset_x, offset_y):
    """Destructif, points_morceaux_par_gpe est modifié"""
    for points in points_morceaux_par_gpe:
        for point in points:
            point[0] = scale_factor * (point[0] + offset_x)
            point[1] = scale_factor * (point[1] + offset_y)



def afficher_points(points_par_gpe):
    for i_gpe in range(len(points_par_gpe)):
        j = 0
        #print("aiguilles_par_gpe : ", points_par_gpe)
        for point in points_par_gpe[i_gpe]:
            x = point[0]
            y = point[1]
            plt.scatter(x, y, color="red")  # Points rouges
            plt.plot(x, y, linestyle="dashed", color="blue")  # Relie les points

    plt.xlabel("X")
    plt.ylabel("Y")
    plt.axis("equal")
    plt.title("Positions aiguilles")
    plt.grid()
    plt.show()

def afficher_aiguilles(aiguilles_par_gpe):
    for i in range(len(aiguilles_par_gpe)):
        for j in range(len(aiguilles_par_gpe[i])):
            x = aiguilles_par_gpe[i][j][0]
            y = aiguilles_par_gpe[i][j][1]
            plt.scatter(x, y, color="red")  # Points rouges
            plt.plot(x, y, linestyle="dashed", color="blue")  # Relie les points

    plt.xlabel("X")
    plt.ylabel("Y")
    plt.axis("equal")
    plt.title("Positions aiguilles")
    plt.grid()
    plt.show()


def elodie2(points_morceaux_par_gpe, scale_factor, offset_x, offset_y, n):
    """
    Entrée :
        -points_morceaux_par_gpe : output de elodie1 : coordonnées des points de l'approximation du contour en
            droite par morceaux
        -scale_factor : facteur de zoom de la figure
            Exemple : scale factor = 2 donnera des points deux fois plus espacés
        -offset_x : indique le décalage en x (première coordonnée) : ajouté tel quel AVANT le zoom
        -offset_y : idem sur y (deuxième coordonée)
        -n : liste d'entiers : n[i] est le nombre d'aiguilles du groupe i
    """
    #afficher_points(points_morceaux_par_gpe)
    rescale(points_morceaux_par_gpe, scale_factor, offset_x, offset_y)
    #afficher_points(points_morceaux_par_gpe)
    #print("SCALING")
    #afficher_points(points_morceaux_par_gpe)
    #print("rescale effectue")
    aiguilles_par_gpe = pos_aiguilles(points_morceaux_par_gpe, n)
    afficher_aiguilles(aiguilles_par_gpe)
    return aiguilles_par_gpe
