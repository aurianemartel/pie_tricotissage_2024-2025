# This is a sample Python script.

# Press Maj+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

import cv2
import numpy as np
import scipy.ndimage as ndi     #convolution : permet de déterminer les extrémités du squelette
import matplotlib.pyplot as plt
from skimage.morphology import skeletonize
from auxiliaires import longueur_approx_morceaux

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
    image_pre_sym = cv2.imread(image_init, cv2.IMREAD_GRAYSCALE)
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


# See PyCharm help at https://www.jetbrains.com/help/pycharm/
