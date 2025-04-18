import numpy as np
import matplotlib.pyplot as plt


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


def afficher_points(points_par_gpe):
    """
    Permet d'afficher l'output d'elodie1
    """
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