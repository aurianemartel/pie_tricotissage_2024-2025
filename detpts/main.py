# This is a sample Python script.

# Press Maj+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

import elodie2
import cv2
import numpy as np
import scipy.ndimage as ndi     #convolution : permet de déterminer les extrémités du squelette
import matplotlib.pyplot as plt
from skimage.morphology import skeletonize

def norme_carre(vecteur):      #norme au carré d'un vecteur de dimension 2
    return(vecteur[0] ** 2 + vecteur[1] ** 2)

def approx_morceaux(points, epsilon):
        """ points désigne la liste des points d'un contour (de la forme [x,y])
        renvoie une nouvelle liste de points qui sont les extrémités des segments de l'apporximation par morceaux"""
        start, end = np.array(points[0]), np.array(points[-1])
        #print("Start, end", start, end)
        line_vec = end - start
        line_len = np.linalg.norm(line_vec)
        line_unitvec = line_vec / line_len if line_len != 0 else line_vec

        distances = np.abs(np.cross(points - start, line_unitvec))
        max_distance_idx = np.argmax(distances)
        max_distance = distances[max_distance_idx]

        if max_distance < epsilon:
            return np.array([start, end])

        left = approx_morceaux(points[:max_distance_idx + 1], epsilon)
        right = approx_morceaux(points[max_distance_idx:], epsilon)
        return np.vstack((left[:-1], right))

def trouve_starts(skeleton):
    """Identifie les extrémités et intersections d'un squelette."""
    structure = np.array([[1, 1, 1],
                          [1, 10, 1],
                          [1, 1, 1]])

    neighbors = ndi.convolve(skeleton.astype(int), structure, mode='constant', cval=0) - 10
    endpoints = np.argwhere((skeleton == 1) & (neighbors == 1))  # 1 voisin = extrémité
    #intersections = np.argwhere((skeleton == 1) & (neighbors >= 3))  # 3+ voisins = intersection

    starts = set(map(tuple, endpoints))
    return list(starts)


def skeleton2contours(skeleton):
    """Renvoie contours (liste des contours) à partir de skeleton via un parcours à partir des extrémités détectées par
    trouve_starts"""
    starts = trouve_starts(skeleton)
    contours = []
    visited = set()
    for start in starts:
        stack = [start]
        contour = []

        while stack != []:
            x, y = stack.pop()
            if (x, y) not in visited:
                visited.add((x, y))
                contour.append((x, y))

                for dx in [-1, 0, 1]:
                    for dy in [-1, 0, 1]:
                        ny = y + dy
                        nx = x + dx
                        if (nx, ny) not in visited and skeleton[nx, ny]:
                            stack.append((nx, ny))
        if contour != []:
            contours.append(contour)
    return contours

def longueur_approx_morceaux(points):
    """si points a été obtenu à partir de approx_morceaux, renvoie la somme des longueurs des morceaux, qui approxime
    la longueur du contour d'origine"""
    longueur = 0
    for i, point in enumerate(points):
        actuel = np.array(point)  # converti un tuple en np.array, qui supporte la soustraction
        if i > 0:
            longueur += np.linalg.norm(actuel - prec)
        prec = actuel
    return longueur



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
    while i < len(points):
        if (np.linalg.norm(actuel - suivant) >= longueur_restante):   #on a la place de rajouter un point sur ce morceau
            actuel += longueur_restante * direction
            longueur_restante = longueur_segment
            #print(actuel)
            nouveaux_points = np.append(nouveaux_points, actuel)
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

def pos_aiguilles(skeleton, n, epsilon):
    """Renvoie la position des aiguilles avec n points par groupe (n fixe, idetique pour chaque groupe)"""
    contours = skeleton2contours(skeleton)
    aiguilles_par_gpe = [[] for _ in range(len(contours))]
    for i, contour in enumerate(contours):
        points = approx_morceaux(contour,epsilon)
        points_raffines = raffiner_approx_affine(points,n[i])
        #print(points_raffines)
        i = 0
        while i < len(points_raffines) - 1:
            aiguilles_par_gpe[i] = np.append(aiguilles_par_gpe[i], (points_raffines[i], points_raffines[i+1]))
            i += 2
    return aiguilles_par_gpe


def plot_aiguilles_pondere(skeleton, ntot, epsilon):
    """Plot les aiguilles avec ntot aiguilles en tout par groupe, le nombre d'aiguilles d'un groupe dépend de sa
    longueur; de par les arrondis, il est possible que le nombre d'aiguilles total légèrement différent de ntot"""
    contours = skeleton2contours(skeleton)
    longueur_totale = 0
    contour_simplifie = []
    longueurs = []
    aiguilles_par_gpe = [[] for _ in range(len(contours))]
    for contour in contours:
        points = approx_morceaux(contour, epsilon)
        contour_simplifie.append(points)
        l_contour = longueur_approx_morceaux(points)
        longueur_totale += l_contour
        longueurs.append(l_contour)
    for i, points in enumerate(contour_simplifie):
        points_raffines = raffiner_approx_affine(points, round(ntot * (longueurs[i] / longueur_totale)))
        # print(points_raffines)
        x = np.array([])
        y = np.array([])
        j = 0
        while j < len(points_raffines) - 1:
            x = np.append(x, points_raffines[j])
            y = np.append(y, points_raffines[j + 1])
            j += 2
            aiguilles_par_gpe[i] = np.append(aiguilles_par_gpe, (x, y))
        print("plot aiguilles pondere , (x, y)", (x,y))
    return aiguilles_par_gpe

def pos_aiguilles_longueur(skeleton, l, epsilon):
    """Affiche la position des aiguilles avec un espacement d'au moins l entre les aiguilles
    (aussi proche que possible)"""
    contours = skeleton2contours(skeleton)
    aiguilles_par_gpe = [[] for _ in range(len(contours))]
    for contour in contours:
        points = approx_morceaux(contour, epsilon)
        longueur = longueur_approx_morceaux(points)
        points_raffines = raffiner_approx_affine(points, int(longueur / l))
        print("int (longueur / l) : ", int(longueur / l ))
        # print(points_raffines)
        x = np.array([])
        y = np.array([])
        i = 0
        while i < len(points_raffines) - 1:
            x = np.append(x, points_raffines[i])
            y = np.append(y, points_raffines[i + 1])
            aiguilles_par_gpe[i] = np.append(aiguilles_par_gpe, (x, y))
            i += 2
    return aiguilles_par_gpe

def dimension(points_morceaux_par_gpe):
    """Renvoie le plus grand écrat en x et le plus grand écart en y parmi tous les points de tous les groupes
    Dans l'idée, points_morceaux_par_gpe est une liste de listes de points, chaque liste de points correspondant
    aux positions des modifications de pente de l'approximaton par morceau du groupe en question"""
    x_min = points_morceaux_par_gpe[0][0][0]
    x_max = x_min
    y_max = points_morceaux_par_gpe[0][0][1]
    y_min = y_max
    for points in points_morceaux_par_gpe:
        for point in points:
            x = point[0]
            y = point[1]
            if x < x_min:
                x_min = x
            if x > x_max:
                x_max = x
            if y < y_min:
                y_min = y
            if y > y_max:
                y_max = y
    return (x_max - x_min, y_max - y_min)



def elodie1(image_init, epsilon = 0.1, afficher_squelette = False, afficher_contours = False, afficher_im_init = False,
            afficher_splines = False):
    """
        Entrée:
        -image_init : chemin d'accès à l'image
        -epsilon : tolérance dans approx_morceaux; eps grand = caccul rapide mais découpe moins précise
        Renvoie :
        -l'écart maximal en x
        -l'écart maximal en y
        -la liste des longueurs de chaque contour (enfin, de leur approximation par morceaux
        -la liste des points de changements de pente de l'approximation, pour chaque groupe
    """
    # Charger l'image
    image_pre_sym = cv2.imread("C:\\Users\\debri\\OneDrive\\Bureau\\ENSTA\\PIE\\premier_jet_python\\image.png",
                               cv2.IMREAD_GRAYSCALE)
    image = np.flipud(image_pre_sym)  # la position des aiguilles apparaît inversée en y sinon
    image = np.transpose(image)
    # Afficher l'image originale
    if afficher_im_init:
        plt.imshow(image_pre_sym, cmap='gray')
        plt.title("Image d'origine")
        plt.show()
    # squeletonize
    invert = cv2.bitwise_not(image)  # noir devient blanc et vice-versa
    skeleton = skeletonize(invert)

    if afficher_squelette:
        # display results
        fig, axes = plt.subplots(nrows=1, ncols=2, figsize=(8, 4))  # plus de sharex/sharey

        ax = axes.ravel()

        ax[0].imshow(image, cmap=plt.cm.gray)
        ax[0].axis('off')
        ax[0].set_title('original', fontsize=20)

        ax[1].imshow(skeleton, cmap=plt.cm.gray)
        ax[1].axis('off')
        ax[1].set_title('skeleton', fontsize=20)

        plt.tight_layout()
        plt.show()

    contours = skeleton2contours(skeleton)
    points_morceaux_par_gpe = [[] for _ in range(len(contours))]
    longueurs = []
    for i, contour in enumerate(contours):
        points_morceaux_par_gpe[i] = approx_morceaux(contour, epsilon)
        longueurs.append(longueur_approx_morceaux((points_morceaux_par_gpe[i])))
    lx, ly = dimension(points_morceaux_par_gpe)
    #print("lx, ly, longueurs, pmpg : ", lx, ly, longueurs, points_morceaux_par_gpe)
    return lx, ly, longueurs, points_morceaux_par_gpe

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    #print_hi('PyCharm')
    chemin = "C:\\Users\\debri\\OneDrive\\Bureau\\ENSTA\\PIE\\premier_jet_python\\image.png"
    lx, ly, longueurs, pmpg = elodie1(chemin, epsilon=0.1, afficher_im_init=True, afficher_squelette=True)
    elodie2.elodie2(pmpg, 0.5, 0, 0, [20, 10])

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
