import cv2
import numpy as np
from scipy.interpolate import splprep, splev
from scipy.optimize import root_scalar
import matplotlib.pyplot as plt
from scipy.integrate import quad
from math import sqrt
from skimage.morphology import skeletonize
import scipy.ndimage as ndi


def contours_lineaire(contours):      #destructif : contour est modifié!!!!
    x = [[] for _ in range(len(contours))]
    y = [[] for _ in range(len(contours))]
    resultat = [[] for _ in range(len(contours))]
    for j, contour in enumerate(contours):          #j numéro du contour
        x[j] = [0 for _ in range(len(contour))]
        y[j] = [0 for _ in range(len(contour))]
        resultat[j] = [[0,0] for _ in range(len(contour))]
        for i, point in enumerate(contour):     #i numéro du point dans le j-ième contour
            #récupération des coordonnées de tous les points du j-ième contour dans un meilleur format
            # print("Le point courant est ", point)
            x[j][i] = point[0][0]
            # print("J'ai modifié x[j][i]", x[j][i])
            y[j][i] = point[0][1]

        # Régression linéaire
        A = np.vstack([x[j], np.ones(len(x[j]))]).T
        a, b = np.linalg.lstsq(A, y[j], rcond=None)[0]

        for l, it_x in enumerate(x[j]):         # création des points de la forme [x, ax + b]
            #print("J'existe dans une boucle")
            resultat[j][l] = [it_x, a * it_x + b]
            #print("J'ai modifié contours[j][l]: ", contours[j][l])
    # print(contours)
    return resultat

# Definitions des fonctions
def norme_carre(vecteur):      #norme au carré d'un vecteur de dimension 2
    return(vecteur[0] ** 2 + vecteur[1] ** 2)

def approx_morceaux(points, epsilon):
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


def approx_equidist(contour, n):            # découpe en n portions de même longueur
    # Calculer les longueurs entre les points consécutifs
    #distances = np.sqrt(np.sum(np.diff(contour, axis=0) ** 2, axis=1))
    # print(contour)
    cumulative_lengths = [0 for _ in range(len(contour))]
    prec_point = contour[0]
    for i, point in enumerate(contour):
        # print("x :", point[0][0], "y : ", point[0][1])
        if i !=0:
            dx = point[0][0] - prec_point[0][0]
            dy = point[0][1] - prec_point[0][1]
            # print("dx : ", dx, "dy : ", dy)
            d = sqrt(dx * dx + 2 + dy * dy)
            # print("d : ", d)
            cumulative_lengths[i] = cumulative_lengths[i-1] + d
            # print("cumulative_lengths : ", cumulative_lengths[i])
        prec_point = point
    total_length = cumulative_lengths[-1]
    # Longueur de chaque segment
    segment_length = total_length / n

    # Trouver les positions des découpes
    cut_positions = np.linspace(0, total_length, n + 1)

    # Calculer les points correspondants aux découpes
    resulting_points = [contour[0] for _ in range(n)]  # Commencer par le premier point
    current_index = 0
    num_point = 0

    for target_length in cut_positions[1:]:
        while cumulative_lengths[current_index] < target_length:
            current_index += 1
            # print("Current index : ", current_index, "cumulative length : ", cumulative_lengths[current_index], "len contour", len(contour))
        # Interpolation linéaire entre deux points
        #p1 = contour[current_index - 1]
        p2 = contour[current_index]
        # t = (target_length - cumulative_lengths[current_index - 1]) / distances[current_index - 1]
        # new_point = (1 - t) * p1 + t * p2
        new_point = p2
        resulting_points[num_point] = new_point
        num_point += 1
    # Convertir en numpy array pour manipulation facile
    #resulting_points = np.array(resulting_points)
    return resulting_points

# Fonction pour calculer la longueur d'arc
def arc_length(u, tck):
    dx, dy = splev(u, tck, der=1)
    return np.sqrt(dx**2 + dy**2)

# Calculer la longueur totale de la spline
def compute_total_length(tck):
    length_total, _ = quad(arc_length, 0, 1, args=(tck,))
    return length_total

# Trouver les valeurs de u correspondant à des longueurs cibles
def find_uniform_segments(tck, n_segments):
    total_length = compute_total_length(tck)
    segment_length = total_length / n_segments

    # Trouver les u correspondant à k * segment_length
    u_values = [0]  # Le premier point est toujours u = 0

    def cumulative_length(u, target_length):
        length, _ = quad(arc_length, 0, u, args=(tck,))
        return length - target_length

    from scipy.optimize import root_scalar

    for k in range(1, n_segments):
        target_length = k * segment_length
        result = root_scalar(cumulative_length, bracket=[u_values[-1], 1], args=(target_length,), method='brentq')
        u_values.append(result.root)

    u_values.append(1)  # Le dernier point est toujours u = 1
    return u_values

# Obtenir les points découpant la spline en n parties égales
def get_segment_points(tck, n_segments):
    u_values = find_uniform_segments(tck, n_segments)
    points = [splev(u, tck) for u in u_values]
    return points


#Gestion de la generation du Gcode
def points_ojectifs(p0, p1, p2, eps, b):
    #p0 est la position actuelle de l'aiguille
    #renvoie la coordonnée cible du point sur lequel devra se positionner la buse pour passer entre p1 et p2
    #b est n booléen qui vaut true si <milieu - p0, obj1> doit être positiif, false sinon
    x0 = p0[0]
    y0 = p0[1]
    x1 = p1[0]
    x2 = p2[0]
    y1 = p1[1]
    y2 = p2[1]
    milieu = ((x1 + x2 )/2, (y1 + y2) /2)
    norme_normale = sqrt((y2-y1) ** 2 + (x1 - x2) ** 2)
    normale_rescale = ((y2-y1) * eps /norme_normale, (x1-x2) * eps / norme_normale)
    obj_1 = milieu + normale_rescale
    obj_2 = milieu - normale_rescale
    produit_scalaire = obj_1[0] * (milieu[0] - x0) + (milieu[1] - y0) * obj_1[1]
    if (produit_scalaire > 0) != b:
        obj_1 = milieu - normale_rescale
        obj_2 = milieu + normale_rescale
    return (obj_1, obj_2)


def k_p_spline(points):
    # cf https://en.wikipedia.org/wiki/Spline_interpolation
    n = len(points)
    a = np.zeros((n, n))
    b = np.zeros((n,))

    #Coefficients liés à k0
    dx_0 = points[0][0] - points[0][0]
    dy_0 = points[0][1] - points[0][1]
    a[0][0] = 2 / dx_0
    a[1][0] = 1 / dx_0
    b[0] = 3 * dy_0 / (dx_0 ** 2)
    #print ( 3 * dy_0 / (dx_0 ** 2), "\n")
    #Coefficients liés à kn
    dx_n = points[n-1][0] - points[n-2][0]
    dy_n = points[n-1][1] - points[n-2][1]
    a[n-1][n-1] = 2 / dx_n
    a[n-1][n-2] = 1 / dx_n
    b[n-1] = 3 * dy_n / (dx_n ** 2)
    #print(3 * dy_n / (dx_n ** 2), "\n")
    #print("B une deuxième fois", b)
    for i, point in enumerate(points):
        if (i > 0) and (i < n-1):
            dx_i_g = points[i][0] - points[i-1][0]
            dx_i_d = points[i+1][0] - points[i][0]
            dy_i_g = points[i][1] - points[i-1][1]
            dy_i_d = points[i + 1][1] - points[i][1]
            a[i][i-1] = 1 / dx_i_g
            a[i][i] = 2 / dx_i_g + 2 / dx_i_d
            a[i][i+1] = 1 / dx_i_d
            b[i] = 3 * (dy_i_g / (dx_i_g ** 2) - dy_i_d / (dx_i_d ** 2))
            #print(3 * (dy_i_g / (dx_i_g ** 2) - dy_i_d / (dx_i_d ** 2)), "\n")
            #print("B une ", i+2,"ème fois", b)
    #print("Matrice A", a[0])
    #print("Matruice A bis", a[len(a) - 1])
    #print("vecteur B", b)
    k = np.linalg.solve(a, b)
    #print(k);
    return k


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


def follow_contour(skeleton, start):
    #obsolète, visited doit être commun à tous les starts pour éviter des contours redondants, cf skeleton2contours
    visited = set()
    stack = [start]
    contour = []

    while stack != []:
        x,y = stack.pop()
        if (x,y) not in visited:
            visited.add((x,y))
            contour.append((x, y))

            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                        ny = y+dy
                        nx = x + dx
                        if (nx, ny) not in visited and skeleton[nx, ny]:
                            stack.append((nx,ny))
    return contour

def skeleton2contours(skeleton):
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

def interpolate(contour):
    """Interpole une branche avec une spline lisse."""
    contour = np.array(contour)
    tck, _ = splprep([contour[:, 1], contour[:, 0]], s=2)  # Ajuste la courbe
    u_new = np.linspace(0, 1, len(contour) * 5)  # Plus de points pour lisser
    x_new, y_new = splev(u_new, tck)

    return np.array(x_new, y_new).T  # Retourne les points clés

def plot_interpolate_contours(skeleton):
    contours = skeleton2contours(skeleton)
    for contour in contours:
        x_new, y_new = interpolate(contour)
        plt.plot(x_new, y_new, color="red")  # Trace les courbes interpolées
    plt.show()

def longueur_approx_morceaux(points):
    # si points a été obtenu à partir de approx_morceaux, renvoie la somme des longueurs des morceaux
    longueur = 0
    for i, point in enumerate(points):
        actuel = np.array(point)  # converti un tuple en np.array, qui supporte la soustraction
        if i > 0:
            longueur += np.linalg.norm(actuel - prec)
        prec = actuel
    return longueur

def raffiner_approx_affine(points, n):
    #si points a été obtenu à partir de approx_morceaux, permet de placer n points équidistants sur la forme approximée
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

def plot_aiguilles(skeleton, n, epsilon):
    # Plot les aiguilles avec n points par groupe (n fixe, idetique pour chaque groupe)
    contours = skeleton2contours(skeleton)
    for contour in contours:
        points = approx_morceaux(contour,epsilon)
        points_raffines = raffiner_approx_affine(points,n)
        #print(points_raffines)
        x = np.array([])
        y = np.array([])
        i = 0
        while i < len(points_raffines) - 1:
            x = np.append(x,points_raffines[i])
            y = np.append(y, points_raffines[i+1])
            i+=2
        plt.scatter(x, y, color="red")  # Points rouges
        plt.plot(x, y, linestyle="dashed", color="blue")  # Relie les points

    plt.xlabel("X")
    plt.ylabel("Y")
    plt.axis("equal")
    plt.title("Positions aiguilles")
    plt.grid()
    plt.show()


def plot_aiguilles_pondere(skeleton, ntot, epsilon):
    # Plot les aiguilles avec ntot aiguilles en tout par groupe, le nombre d'aiguilles d'un groupe dépend de sa longueur
    #De par les arrondis, il est possible que le nombre d'aiguilles total légèrement différent de ntot
    contours = skeleton2contours(skeleton)
    longueur_totale = 0
    contour_simplifie = []
    longueurs = []
    for contour in contours:
        #print("Je regarde un contour")
        points = approx_morceaux(contour, epsilon)
        contour_simplifie.append(points)
        l_contour = longueur_approx_morceaux(points)
        longueur_totale += l_contour
        longueurs.append(l_contour)
    for i, points in enumerate(contour_simplifie):
        """print(i)
        print(longueurs[i])
        print(longueur_totale)
        print(longueurs[i] / longueur_totale)
        print(ntot)
        print(round(ntot * (longueurs[i] / longueur_totale)))"""
        points_raffines = raffiner_approx_affine(points, round(ntot * (longueurs[i] / longueur_totale)))
        # print(points_raffines)
        x = np.array([])
        y = np.array([])
        i = 0
        while i < len(points_raffines) - 1:
            x = np.append(x, points_raffines[i])
            y = np.append(y, points_raffines[i + 1])
            i += 2
        plt.scatter(x, y, color="red")  # Points rouges
        plt.plot(x, y, linestyle="dashed", color="blue")  # Relie les points
        print(points_raffines)
    plt.xlabel("X")
    plt.ylabel("Y")
    plt.axis("equal")
    plt.title("Positions aiguilles pondéré")
    plt.grid()
    plt.show()

def plot_aiguilles_longueur(skeleton, l, epsilon):
    #Affiche la position des aiguilles avec un espacement d'au moins l entre les aiguilles (aussi proche que possible)
    contours = skeleton2contours(skeleton)
    for contour in contours:
        points = approx_morceaux(contour, epsilon)
        longueur = longueur_approx_morceaux(points)
        points_raffines = raffiner_approx_affine(points, int(longueur / l))
        print(int(longueur / l ))
        # print(points_raffines)
        x = np.array([])
        y = np.array([])
        i = 0
        while i < len(points_raffines) - 1:
            x = np.append(x, points_raffines[i])
            y = np.append(y, points_raffines[i + 1])
            i += 2
        plt.scatter(x, y, color="red")  # Points rouges
        plt.plot(x, y, linestyle="dashed", color="blue")  # Relie les points

    plt.xlabel("X")
    plt.ylabel("Y")
    plt.axis("equal")
    plt.title("Positions aiguilles")
    plt.grid()
    plt.show()

#Début du main


n_points_par_groupe = 10    #nombre d'aiguilles par groupe, pour plot_aiguilles
n_points_tot = 12           #nombre d'aiguilles totales, pour plot_aiguilles_pondere
epsilon = 0.1            #tolérance dans approx_morceaux; esp grand = calcul rapide mais découpe moins précise
longueur_plt_aig_l = 12            #espacement entre les aiguilles pour plot_aiguilles_longueur
afficher_squelette = True
afficher_im_init = True
afficher_contours = True
afficher_splines = True

# Charger l'image
image_pre_sym = cv2.imread("C:\\Users\\debri\\OneDrive\\Bureau\\ENSTA\\PIE\\premier_jet_python\\image.png", cv2.IMREAD_GRAYSCALE)
image = np.flipud(image_pre_sym) #la position des aiguilles apparaît inversée en y sinon
image = np.transpose(image)
# Afficher l'image originale
if afficher_im_init:
    plt.imshow(image_pre_sym, cmap='gray')
    plt.title("Image d'origine")
    plt.show()

#squeletonize
invert = cv2.bitwise_not(image)   #noir devient blanc et vice-versa
skeleton = skeletonize(invert)
plot_aiguilles(skeleton, n_points_par_groupe, epsilon)
plot_aiguilles_pondere(skeleton, n_points_tot, epsilon)
plot_aiguilles_longueur(skeleton, longueur_plt_aig_l, epsilon)
#fin de ce qui est utile



#plot_interpolate_contours(skeleton)
#print(skeleton)

if afficher_squelette:
    # display results
    fig, axes = plt.subplots(nrows=1, ncols=2, figsize=(8, 4), sharex=True, sharey=True)

    ax = axes.ravel()

    ax[0].imshow(image, cmap=plt.cm.gray)
    ax[0].axis('off')
    ax[0].set_title('original', fontsize=20)

    ax[1].imshow(skeleton, cmap=plt.cm.gray)
    ax[1].axis('off')
    ax[1].set_title('skeleton', fontsize=20)

# Appliquer un filtre gaussien et binariser l'image

# blurred = cv2.GaussianBlur(image, (5, 5), 0)
# _, binary = cv2.threshold(blurred, 127, 255, cv2.THRESH_BINARY)
#binary = (skeleton * 255).astype(np.uint8)

# Afficher l'image binaire après seuil
# plt.imshow(binary, cmap='gray')
# plt.title("Image Binaire après seuil")
# plt.show()

#inverted_image = cv2.bitwise_not(binary)             #inversion du noir et du blanc
"""
# Détection des contours
contours, _ = cv2.findContours(binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

# debug 1 : contours avant la linéarisation
if afficher_contours:
    print(f"Nombre de contours détectés début: {len(contours)}")
    for i, contour in enumerate(contours):
        # Dessiner le contour sur une copie de l'image
        contour_image = cv2.drawContours(np.zeros_like(image), [contour], -1, (255, 255, 255), 1)
        plt.imshow(contour_image, cmap='gray')
        plt.title(f"Contour {i}")
        plt.show()



# contours = contours_lineaire(vieux_contours)

# approximation par segment de droites

#decoupe_par_morceaux = [0 for i in range(len(contours) - 1)]      # points de la découpe par morceaux en segments
#for i, contour in enumerate(contours):
    #if i != 0:
        #decoupe_par_morceaux[i-1] = approx_morceaux(contour, epsilon)

if afficher_splines:
# Créer un graphique pour afficher les résultats
    plt.figure(figsize=(8, 8))

x_aiguilles = [[0 for j in range(n_points_par_groupe)] for i in range(len(contours))]
y_aiguilles = [[0 for j in range(n_points_par_groupe)] for i in range(len(contours))]

# Pour l'affichage des splines interpolées
point_par_spline = 100
x_splines = [0 for _ in range(point_par_spline)]
y_splines = [0 for _ in range(point_par_spline)]
# Itérer sur tous les contours détectés
for i, contour in enumerate(contours):
    # print("J'existe avec un i = ", i)
    if i>=0:        #on n'ignore plus le fond
        #print("Contour :", contour)
        # Simplifier chaque contour
        #               epsilon = 0.01 * cv2.arcLength(contour, True)
        #               simplified_contour = cv2.approxPolyDP(contour, epsilon, True)
        # print("J'existe!")

        # Vérifier la forme de simplified_contour
        # if True | (simplified_contour.shape[0] > 1):  # Pour éviter les contours trop petits
        if True:            #pour l'indentation
            # print("J'existe encore!")
            # Extraire les coordonnées x et y des points simplifiés
            IL Y AVAIT TROIS GUILLEMETS x = contour[:, 0, 0]
            y = contour[:, 0, 1]

            # Approximation par spline
            tck, u = splprep([x, y], s=0)
            segment_points = get_segment_points(tck, n_points_par_groupe - 1)       #pour compenser un +1 qq part

            IL Y AVAIT TROIS GUILLEMETS
            points_equidist = approx_equidist(contour, n_points_par_groupe)
            # print(points_equidist, "\n", points_equidist[0], points_equidist[0][1])
            # k_p = k_p_spline(points_equidist)


            #print(k_p)
            # print(points_equidist)
            j = 0
            seuil = 1300
            #seuil = 0
            ecart_min = seuil * 2
            dx = 0
            dy = 0
            for point in points_equidist:
                # print(i)
                for k in range(j):
                    dx = point[0][0] - x_aiguilles[i][k]
                    dy = point[0][1] - y_aiguilles[i][k]
                    ecart = dx ** 2 + dy ** 2
                    if ecart < ecart_min:
                        ecart_min = ecart
                    #print(dx, dy)
                if (j == 0) or ecart_min >= seuil:
                    x_aiguilles[i][j] = point[0][0] # abscisse du j ième point du groupe i
                    y_aiguilles[i][j] = point[0][1]       # ordonnée du j-ième point du groupe i
                    j += 1
                #else:
                    #print(ecart_min)
            #Visualisation splines calculées
            IL Y AVAIT TROIS GUILLEMETS
            for j in range(len(points_equidist) - 1):
                x1 = points_equidist[j][0]
                x2 = points_equidist[j + 1][0]
                y1 = points_equidist[j][1]
                y2 = points_equidist[j + 1][1]
                for i in range(point_par_spline - 1):
                    x_splines[i] = x1 + i * 1/point_par_spline * (x2 - x1)
                    t_x = (1 - (x_splines[i]- x1) / (x2 - x1))
                    a = k_p[j] * (x2 - x1) - (y2 - y1)
                    b = - k_p[j+1] * (x2- x1) + (y2 - y1)
                    y_splines[i] = (1 - t_x) * y1 + t_x * y2 + t_x * (1- t_x) * ((1-t_x) * a + t_x * b)
            IL Y AVAIT TROIS GUILLEMETS ICI
            # Générer les points de la spline
            IL Y AVAIT TROIS GUILLEMETS ICI
            if afficher_splines:
                spline_points = splev(np.linspace(0, 1, 100), tck)
                plt.plot(spline_points[0], spline_points[1], '-', label='Spline approximée')
            IL Y AVAIT TROIS GUILLEMETS ICI
            # Affichage des résultats
            # plt.plot(decoupe_par_morceaux[0], decoupe_par_morceaux[1], 'x', label = 'Découpe par morceaux')
            #plt.plot(x, y, 'o', label='Contour simplifié')

IL Y AVAIT TROIS GUILLEMETS ICI


# print("Je suis libre")
#point_decoupe = [[(x_decoupe[g][i], y_decoupe[g][i]) for i in range(len(x_decoupe))] for g in range(2)] #g : num du grpe
#print("x_decoupe", x_decoupe)
#print("y_decoupe", y_decoupe)
#print("decoupe par morceaux:", decoupe_par_morceaux)
# debug
#print("Nombre de contours détectés :", {len(contours)})

# Affichage de la légende et du graphique
#plt.legend()
#plt.show()

#Affichage des segments entre les deux groupes
# Création de la figure et des axes
IL Y AVAIT TROIS GUILLEMETS
fig, ax = plt.subplots()

# Dessiner tous les segments possibles entre list1 et list2
for i in range(len(x_aiguilles[0])):      # parcours des somets du groupe 1
    for j in range(len(x_aiguilles[1])):       # parcours des sommets du groupe 2
        # Tracer une ligne entre point1 (de list1) et point2 (de list2)
        #print("Coucou")
        #ax.plot([x_aiguilles[0][i], x_aiguilles[1][j]], [y_aiguilles[0][i], y_aiguilles[1][j]], 'k-', lw=0.5)
        ax.plot(x_splines[i], y_splines[i], 'k-', lw=0.5)


# Ajouter des points pour visualiser les deux listes
ax.scatter(x_aiguilles[0][:], y_aiguilles[0][:], color='blue', label='Points du groupe 1')
ax.scatter(x_aiguilles[1][:], y_aiguilles[1][:], color='red', label='Points du groupe 2')

# Étiquettes et titre
ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_title('Segments entre deux listes de points')

# Ajouter une légende
ax.legend()

# Afficher la fenêtre avec matplotlib
plt.show()
"""