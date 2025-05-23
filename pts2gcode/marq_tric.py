"""
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
"""

import yaml
import sys

# Paramètres
PATH_OUT = "../prgs_gcode/"  # Chemin de sortie des fichiers gcode
PATH_YAML = "../yaml_files/"  # Chemin de lecture des fichiers yaml

VERBOSE = False  # True pour les affichage de débuggage

# Taille de la zone de travail de la machine
MAX_Y = 355
MIN_Y = 0
MAX_Z = 675
MIN_Z = 0

# Paramètres de la position du crayon par rapport à la buse de tricotissage
ACTIVATE_OFFSET = True  # Désactiver pour vérfier que la buse est bien en face des points en lançant un marquage après avoir fait le marquage
OFFSET_Y = 26
OFFSET_Z = -56


def enTete(dim_y, dim_z, feed_rate=10000):
    return f"""G21 ; Definir les unites en millimetres
G90 ; Positionnement absolu
G19 ; YZ plan
G40
G49
F{feed_rate} ; Vitesse de déplacement, max=20000

"""


# Les 4 lignes suivantes permettent de faire le tour de la zone accessible
# À ajouter à l'en-tête ci-dessus si l'on veut vérifier la calibration du plateau lors du tricotissage et du marquage
"""
G0 Y{dim_y} Z0
G0 Y{dim_y} Z{dim_z}
G0 Y0 Z{dim_z}
G0 Y0 Z0

"""


# Fonctions de mouvement G-code


def G0(y, z):
    """Aller à (y,z) rapidement, par une ligne droite"""
    return f"G0 Y{y} Z{z}"


def G1(y, z):
    """Aller à (y,z) par une ligne droite à la vitesse donnée par le Feed Rate, réglable avec la commande F..."""
    return f"G1 Y{y} Z{z}"


def G2(yi, zi, yf, zf, cy, cz):
    """Aller à (yf,zf) en arc de cercle anti-horaire de centre (cy,cz), en partant de (yi,zi)"""
    return f"G2 Y{yf} Z{zf} J{cy-yi} K{cz-zi}"


def G3(yi, zi, yf, zf, cy, cz):
    """Aller à (yf,zf) en arc de cercle horaire de centre (cy,cz), en partant de (yi,zi)"""
    return f"G3 Y{yf} Z{zf} J{cy-yi} K{cz-zi}"


def G23(yi, zi, yf, zf, cy, cz, sens):
    """Retourne le résultat de G2 ou G3 selon le sens de rotation nécessaire"""
    if sens == -1:  # sens indirect
        return G2(yi, zi, yf, zf, cy, cz)
    elif sens == 1:  # sens direct
        return G3(yi, zi, yf, zf, cy, cz)
    else:
        raise ValueError("Problème : sens non valide")


## Marquage


def marquage(yamlFile, offset_y=None, offset_z=None):
    """
    Crée le fichier gcode de marquage associé au patron décrit dans le fichier yaml en argument.
    les valeurs d'offset_x et offset_y sont les décalages entre la position de la buse et celle du crayon.
    """
    if offset_y is None:
        offset_y = OFFSET_Y if ACTIVATE_OFFSET else 0
    if offset_z is None:
        offset_z = OFFSET_Z if ACTIVATE_OFFSET else 0

    with open(yamlFile, "r") as file:
        data = yaml.safe_load(file)
    with open(PATH_OUT + f"marq_{data['nom']}.gcode", "w") as marq:
        dim_y, dim_z = data["dimensions"]
        marq.write(enTete(dim_y, dim_z, 20000))
        marq.write("M5 S1000\n\n")  # Activer le moteur
        for i, groupe in enumerate(data["groupes"]):
            for j, point in enumerate(data["groupes"][groupe]):
                py, pz = point
                if (
                    py - offset_y > MAX_Y
                    or py - offset_y < MIN_Y
                    or pz - offset_z > MAX_Z
                    or pz - offset_z < MIN_Z
                ):
                    raise ValueError(
                        "Problème : coordonnées hors limites, avez vous pris en compte que le crayon est décalé par rapport à la buse ?"
                    )
                marq.write(G0(py - offset_y, pz - offset_z))
                if i == 0 and j == 0:
                    # Pour la première aiguille, on attend que le crayon soit installé
                    marq.write("\nM0\n")
                # Descendre et relever crayon
                marq.write("\nM3\nG4 P0.5 \nM5\nG4 P0.5 \n\n")
                if i == 0 and j == 0:
                    # Pour la première aiguille, on met ensuite la buse à l'endroit du marquage pour vérifier que le marquage est au bon endroit.
                    marq.write(G0(py, pz))
                    marq.write("\nM0\n")
        marq.write("G0 Y50 Z100\nG0 Y50 Z0\nG0 Y0 Z0\n")
    return f"Fichier marq_{data['nom']}.gcode généré avec succès"


# Tricotissage


# Fonctions utilitaires pour la détection d'intersection de segments
def orientation(p, q, r):
    """
    Détermine l'orientation des points ordonnés (p, q, r).
    Retourne:
    0 --> p, q, r sont colinéaires
    1 --> Sens horaire
    -1 --> Sens anti-horaire
    """
    # val = (qy - py) * (rz - qz) - (qz - pz) * (ry - qy)
    # p = [py, pz], q = [qy, qz], r = [ry, rz]
    val = (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
    if val == 0:
        return 0  # Colinéaire
    return 1 if val > 0 else -1  # Horaire ou Anti-horaire (dépend de l'axe Z)


def dans_segment(p, q, r):
    """
    Étant donné trois points colinéaires p, q, r, la fonction vérifie si
    le point q se trouve sur le segment 'pr'.
    """
    if (
        q[0] <= max(p[0], r[0])
        and q[0] >= min(p[0], r[0])
        and q[1] <= max(p[1], r[1])
        and q[1] >= min(p[1], r[1])
    ):
        return True
    return False


def segments_intersection(p1, q1, p2, q2):
    """
    Vérifie si le segment p1q1 intersecte le segment p2q2.
    p1, q1: extrémités du premier segment.
    p2, q2: extrémités du deuxième segment.
    """
    # Trouver les quatre orientations nécessaires pour les cas généraux et spéciaux
    o1 = orientation(p1, q1, p2)
    o2 = orientation(p1, q1, q2)
    o3 = orientation(p2, q2, p1)
    o4 = orientation(p2, q2, q1)

    # Cas général
    # Si (p1, q1, p2) et (p1, q1, q2) ont des orientations différentes ET
    # (p2, q2, p1) et (p2, q2, q1) ont des orientations différentes.
    if o1 != 0 and o2 != 0 and o3 != 0 and o4 != 0:
        if o1 != o2 and o3 != o4:
            return True
    # Cas spéciaux (colinéarité)
    # o1 == 0 signifie que p1, q1, p2 sont colinéaires.
    # on_segment(p1, p2, q1) vérifie si p2 est sur le segment p1q1.
    # Normalement on n'a pas de cas spéciaux en pratique, car si les segments sont colinéaire,
    # le schéma n'est tout simplement pas tricotissable.
    elif o1 == 0 and dans_segment(p1, p2, q1):
        return True
    # p1, q1, q2 sont colinéaires et q2 est sur le segment p1q1
    elif o2 == 0 and dans_segment(p1, q2, q1):
        return True
    # p2, q2, p1 sont colinéaires et p1 est sur le segment p2q2
    elif o3 == 0 and dans_segment(p2, p1, q2):
        return True
    # p2, q2, q1 sont colinéaires et q1 est sur le segment p2q2
    elif o4 == 0 and dans_segment(p2, q1, q2):
        return True

    return False  # Ne se croisent pas


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

    # On doit vérifieer que le tricotissage ne se "croise" pas, sinon on a des problèmes
    # car on ne tourne pas toujouts dans le même sens lors du parcours et cela crée un schéma "bizarre"
    # en plus de causer des problèmes lors des évitements de collisions

    if segments_intersection(groupe1[0], groupe2[0], groupe1[-1], groupe2[-1]):
        # On retourne le groupe 2
        groupe2 = groupe2[::-1]
        print("RETOURNEMENT DU GROUPE 2")
        if segments_intersection(groupe1[0], groupe2[0], groupe1[-1], groupe2[-1]):
            # Le problème n'a pas disparu, sûrement que le schéma n'est pas tricotissable
            raise ValueError(
                "Probleme, le schéma est inhabituel, êtes vous sur que le groupe 1 n'intersecte pas le groupe 2 ?"
            )

    for i in range(l1 - 1):
        # on est déjà en groupe1[i], pas besoin d'y aller
        prc.append(groupe2[0])
        prc.append(groupe2[1])
        prc.append(groupe1[i + 1])

        # boucle sur les autres i
        for j in range(1, l2 - 1):
            prc.append(groupe1[i])
            prc.append(groupe2[j])
            prc.append(groupe2[j + 1])
            prc.append(groupe1[i + 1])
    return prc


def vect(pt1, pt2):
    """Retourne le vecteur entre pt1 et pt2"""
    return [pt2[0] - pt1[0], pt2[1] - pt1[1]]


def norme(u):
    """Retourne la norme du vecteur u"""
    return (u[0] ** 2 + u[1] ** 2) ** 0.5


def sens_arc(u, v):
    """
    Retourne le sens de l'arc de cercle entre les vecteurs u et v, soit -1 soit 1
    Pour un parcours classique, le sens est toujours le même quand on tourne autour d'aiguilles
    Quand on évite une aiguille sur un segment droit, le sens est logiquement l'opposé du sens associé au reste du parcours.
    """
    if u[0] * v[1] - u[1] * v[0] > 0:
        sens = 1  # sens direct
    elif u[0] * v[1] - u[1] * v[0] < 0:
        sens = -1  # sens indirect
    else:
        # TODO : mettre à -1 ou 1 de manière arbitraire ? Mais comme le sens est toujours le même lors du parcours, on pourrait gérer le cas en ne prenant pas juste le sens en compte quand il est indéfini
        sens = 0
        print("Problème : vecteurs colinéaires\n")
    return sens


def cercle_intersection(c, r, p1, p2):
    """
    Détermine s'il y a intersection entre une droite (définie par p1 et p2) et un cercle (défini par son centre c et son rayon r).
    Retourne un booléen indiquant s'il y a intersection et une liste des points d'intersection.
    """
    # Vecteur directeur de la droite normalisé
    d = vect(p1, p2)
    d_norm = norme(d)
    d = [d[0] / d_norm, d[1] / d_norm]

    # Vecteur allant du centre du cercle au premier point
    f = vect(c, p1)

    # Equation quadratique
    a = 1
    b = 2 * (d[0] * f[0] + d[1] * f[1])
    c_val = f[0] ** 2 + f[1] ** 2 - r**2

    discriminant = b**2 - 4 * a * c_val

    if discriminant < 0:
        # Pas d'intersection
        return False, []

    # Calculer les solutions
    t1 = (-b + discriminant**0.5) / (2 * a)
    t2 = (-b - discriminant**0.5) / (2 * a)

    # Vérifier si les intersections sont sur le segment
    segment_length = norme(vect(p1, p2))
    intersections = []

    # Calculer les points d'intersection
    if 0 <= t1 <= segment_length:
        intersection1 = [p1[0] + t1 * d[0], p1[1] + t1 * d[1]]
        intersections.append(intersection1)

    if (
        0 <= t2 <= segment_length and discriminant > 0
    ):  # Éviter les doublons si discriminant = 0
        intersection2 = [p1[0] + t2 * d[0], p1[1] + t2 * d[1]]
        intersections.append(intersection2)

    return len(intersections) > 0, intersections


def premiere_intersection(
    p1, p2, aiguille_actuelle, aiguille_arrivee, liste_aiguilles, epsilon
):
    """
    Détermine s'il y a intersection entre le segment [p1, p2] et les aiguilles.
    Retourne un booléen indiquant s'il y a intersection, l'aiguille d'intersection et la liste des points d'intersection.
    """
    intersection_trouvee = False
    aiguille_intersection = None
    intersections = []
    min_distance = float("inf")
    for aiguille in liste_aiguilles:
        if aiguille != aiguille_actuelle and aiguille != aiguille_arrivee:
            resultat, resultat_intersections = cercle_intersection(
                aiguille, epsilon, p1, p2
            )
            if resultat:
                distance = min(
                    [
                        norme(vect(p1, resultat_intersections[i]))
                        for i in range(len(resultat_intersections))
                    ]
                )
                if intersection_trouvee == False or distance < min_distance:
                    intersection_trouvee = True
                    min_distance = distance
                    aiguille_intersection = aiguille
                    intersections = resultat_intersections
    if intersection_trouvee and VERBOSE:  # Affichage pour le débuggage
        print(
            f"je suis le segment {p1} -> {p2}, de l'aiguille {aiguille_actuelle} à l'aiguille {aiguille_arrivee}"
        )
        print(f"Intersection trouvée avec {aiguille_intersection} en {intersections}")
        print(f"Distance : {min_distance}")
    if min_distance < 0.0001:
        # La résolution est impossible car des cercles d'aiguilles se touchent
        raise ValueError(
            f"Epsilon = {epsilon} trop grand, pas assez d'espace entre les aiguilles"
        )
    return intersection_trouvee, aiguille_intersection, intersections


def pointsPassage(pt1, pt2, pt3, epsilon):
    """Retourne les points par lesquels passer pour contourner pt2 vers pt3,
    et le sens de l'arc de cercle entre ces points"""
    assert (pt1 != pt2) & (pt1 != pt3) & (pt2 != pt3)
    u = vect(pt1, pt2)
    v = vect(pt2, pt3)
    sens = sens_arc(
        u, v
    )  # Ce sens est normalement toujours le même le long de notre parcours
    pp1 = [
        pt2[0] + sens * epsilon * u[1] / norme(u),
        pt2[1] + sens * (-1) * epsilon * u[0] / norme(u),
    ]
    pp2 = [
        pt2[0] + sens * epsilon * v[1] / norme(v),
        pt2[1] + sens * (-1) * epsilon * v[0] / norme(v),
    ]
    return pp1, pp2, sens


def evitement_aiguilles_ligne_droite(
    pp_start, pp_end, aiguille_start, aiguille_end, liste_aiguilles, epsilon, sens
):
    """
    Renvoie les commandes G-code pour aller de pp_start à pp_end en contournant les aiguilles sur le trajet
    i est l'indice de l'aiguille actuelle dans le parcours prc
    sens est le sens de parcours, pas celui du contournement
    """
    commandes = ""

    intersection_trouvee, aiguille_intersection, intersections = premiere_intersection(
        pp_start, pp_end, aiguille_start, aiguille_end, liste_aiguilles, epsilon
    )

    while intersection_trouvee:
        # Tant qu'on ne peut pas aller tout droit jusqu'à l'aiguille suivante, on fait des contounements
        if len(intersections) == 1:
            # 1 seul point d'intersection avec le cercle
            pp_intersection = intersections[0]
        else:  # il y a deux points d'intersection avec le cercle
            vect_ancienchemin = vect(pp_start, pp_end)
            vect_ancienchemin = [
                vect_ancienchemin[0] / norme(vect_ancienchemin),
                vect_ancienchemin[1] / norme(vect_ancienchemin),
            ]
            vect_orth = [-sens * vect_ancienchemin[1], sens * vect_ancienchemin[0]]
            # On calcule le point de passage
            pp_intersection = [
                aiguille_intersection[0] + epsilon * vect_orth[0],
                aiguille_intersection[1] + epsilon * vect_orth[1],
            ]

            # Pas sur que la partie suivante soit nécessaire, car normalement comme on tourne toujours dans le même
            # sens (et que ce sense est enregistré dans la variable sens), on sait toujours dans quel "sens" doit aler le vecteur orthogonal
            sens_contournement = sens_arc(
                vect(pp_start, pp_intersection), vect(pp_intersection, pp_end)
            )
            if sens_contournement == sens:
                # On prend le point opposé sur le cercle
                if VERBOSE:
                    print("CHANGEMENT DE SENS DU VECTEUR ORTHOGONAL")
                pp_intersection = [
                    aiguille_intersection[0] - epsilon * vect_orth[0],
                    aiguille_intersection[1] - epsilon * vect_orth[1],
                ]

        commandes += evitement_aiguilles_ligne_droite(
            pp_start,
            pp_intersection,
            aiguille_start,
            aiguille_intersection,
            liste_aiguilles,
            epsilon,
            sens,
        )
        # On enregistre le point de passage et on cherche la prochaine intersection (normalement il n'y en a pas , la partie est elle utile ?)
        commandes += f"{G1(pp_intersection[0],pp_intersection[1])}\n"

        pp_start = pp_intersection
        aiguille_start = aiguille_intersection
        intersection_trouvee, aiguille_intersection, intersections = (
            premiere_intersection(
                pp_start,
                pp_end,
                aiguille_start,
                aiguille_end,
                liste_aiguilles,
                epsilon,
            )
        )
    return commandes


def trace(prc, epsilon, liste_aiguilles):
    """
    Renvoie la suite de commandes G-code correspondant au tricotissage en suivant le parcours prc
    On a des cercles de sécurité de rayon epsilon autour de chaque aiguille
    """
    chemin = ""

    # Initialiser le tricotissage : cercle autour de la première aiguille
    pp1, pp2, sens = pointsPassage(
        prc[3], prc[0], prc[1], epsilon
    )  # TODO : s'adapte mal si on change le type de parcours
    chemin += evitement_aiguilles_ligne_droite(
        [0, 0], pp2, [0, 0], [0, 0], liste_aiguilles, 0.99 * epsilon, sens
    )
    chemin += f"{G1(pp2[0],pp2[1])}\nM0\n\n{G23(pp2[0],pp2[1],pp2[0],pp2[1],prc[0][0],prc[0][1],sens)}\n"

    # Boucle sur le parcours
    l = len(prc)
    for i in range(l - 2):
        p_prec = pp2
        pp1, pp2, sens = pointsPassage(prc[i], prc[i + 1], prc[i + 2], epsilon)

        # On va en ligne droite jusqu'à l'aiguille suivante, en faisant des contournements si nécessaire
        chemin += evitement_aiguilles_ligne_droite(
            p_prec, pp1, prc[i], prc[i + 1], liste_aiguilles, epsilon, sens
        )

        # On a fini de traiter les contournement, on peut aller à l'aiguille suivante et faire le tour
        chemin += f"{G1(pp1[0],pp1[1])}\n{G23(pp1[0],pp1[1],pp2[0],pp2[1],prc[i+1][0],prc[i+1][1],sens)}\n\n"

    # Finaliser le tricotissage : gestion du dernier point
    u = vect(prc[l - 4], prc[l - 1])
    v = vect(prc[l - 2], prc[l - 1])
    pp1 = [
        prc[l - 1][0] + epsilon * u[0] / norme(u),
        prc[l - 1][1] + epsilon * u[1] / norme(u),
    ]
    sens = sens_arc(u, v)
    chemin += f"{G1(pp1[0],pp1[1])}\n{G23(pp1[0],pp1[1],pp1[0],pp1[1],prc[l-1][0],prc[l-1][1],sens)}\n"
    return chemin


def tricotissage(yamlFile):
    """
    Crée le fichier gcode de tricotissage associé au patron décrit dans le fichier yaml en argument.
    """
    # Récupération des données
    with open(yamlFile, "r") as file:
        data = yaml.safe_load(file)
    dim_y, dim_z = data["dimensions"]
    epsilon = data["epsilon"]

    # On récupère toutes les aiguilles
    liste_aiguilles = []
    for groupe in data["groupes"]:
        for aiguille in data["groupes"][groupe]:
            if aiguille not in liste_aiguilles:
                # On ne garde pas les doublons (si deux aiguilles dans des groupes différents ont la même position)
                liste_aiguilles.append(aiguille)

    with open(PATH_OUT + f"tric_{data['nom']}.gcode", "w") as tric:
        tric.write(enTete(dim_y, dim_z))
        tric.write("G1 Y0 Z0\n")  # Position de départ

        for lien in data["liens"]:
            # Création du parcours de tricotissage
            prc = parcours(data["groupes"][lien[0]], data["groupes"][lien[1]])
            tric.write(trace(prc, epsilon, liste_aiguilles))

    return f"Fichier tric_{data['nom']}.gcode généré avec succès"


# Main

if __name__ == "__main__":
    VERBOSE = True
    if len(sys.argv) > 1:
        if sys.argv[1][0] == "m":
            if len(sys.argv) > 2:
                yamlFile = PATH_YAML + sys.argv[2]
            else:
                yamlFile = PATH_YAML + "file.yaml"
            print(marquage(yamlFile))
        elif sys.argv[1][0] == "t":
            if len(sys.argv) > 2:
                yamlFile = PATH_YAML + sys.argv[2]
            else:
                yamlFile = PATH_YAML + "file.yaml"
            print(tricotissage(yamlFile))
    else:
        print("Please provide command and file\n")
