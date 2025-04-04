import numpy as np
from main import longueur_approx_morceaux

def raffiner_approx_affine(points, n):
    """si points a été obtenu à partir de approx_morceaux, permet de placer n points équidistants sur la forme
    approximée; appelée par plot_aiguille"""
    longueur = 0
    for i, point in enumerate(points):
        actuel = np.array(point)     #converti un tuple en np.array, qui supporte la soustraction
        if i > 0:
            longueur += np.linalg.norm(actuel - prec)
        prec = actuel
    longueur = longueur_approx_morceaux(points)
    longueur_segment = longueur / (n-1)
    longueur_restante = longueur_segment
    actuel = np.array(points[0])
    actuel = actuel.astype(np.float64)       #pour pouvoir gérer des opérations faisant intervenir des flottants
    #print(actuel.dtype)
    suivant = np.array(points[1])
    suivant = suivant.astype(np.float64)       #pour pouvoir gérer des opérations faisant intervenir des flottants
    i = 1       #numéro du point suivant
    direction = (suivant - actuel) / np.linalg.norm(suivant - actuel)
    nouveaux_points = [actuel]
    j = 1           #on a déjà placé une aiguilles, au point de départ
    while j < n:
        if (np.linalg.norm(actuel - suivant) >= longueur_restante):   #on a la place de rajouter un point sur ce morceau
            actuel += longueur_restante * direction
            longueur_restante = longueur_segment
            #print(actuel)
            nouveaux_points = np.append(nouveaux_points, actuel)
            j += 1
            #print(nouveaux_points)
        else:           #pas la place de rajouter un point sur le morceau
            i += 1  #on passe au morceau suivant
            if i < len(points) - 1:     #il reste encore au moins un morceau
                longueur_restante -= np.linalg.norm(actuel - suivant)
                #print(suivant.dtype)
                actuel = suivant
                suivant = points[i]
                suivant = suivant.astype(np.float64)
                direction = (suivant - actuel) / np.linalg.norm(suivant - actuel)
    return nouveaux_points


def pos_aiguilles(points_morceaux_par_gpe, n):
    """Renvoie la position des aiguilles avec n points par groupe (n tableau, peu différer pour chaque groupe)
    sous la forme d'un tableau tab tel que tab[i] """
    aiguilles_par_gpe = [[] for _ in range(len(points_morceaux_par_gpe))]
    for i, points in enumerate(points_morceaux_par_gpe):
        points_raffines = raffiner_approx_affine(points,n[i])
        #print(points_raffines)
        i = 0
        while i < len(points_raffines) - 1:
            aiguilles_par_gpe[i] = np.append(aiguilles_par_gpe[i], (points_raffines[i], points_raffines[i+1]))
            i += 2
    return aiguilles_par_gpe

def rescale(points_morceaux_par_gpe, scale_factor, offset_x, offset_y):
    """Destructif, points_morceaux_par_gpe est modifié"""
    for points in points_morceaux_par_gpe:
        for point in points:
            point[0] = point[0] * scale_factor + offset_x
            point[1] = point[0] * scale_factor + offset_y

def elodie2(points_morceaux_par_gpe, scale_factor, offset_x,offset_y, n):
    rescale(points_morceaux_par_gpe, scale_factor, offset_x, offset_y)
    return pos_aiguilles(points_morceaux_par_gpe, n)
