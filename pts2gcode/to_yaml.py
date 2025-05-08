import yaml
import math


def create_yaml_file(nom, dim_y, dim_z, liens, groupes, filepath, epsilon=None):
    """
    Crée un fichier YAML à partir des données fournies. Les groupes sont données sous la forme d'un dictionnaire contenant des listes, les clés sont les noms des groupes

    nom (str): nom du schéma
    dim_y et dim_z : dimensions de la zone de dessin
    liens (list): Une liste de listes, chaque sous-liste contenant deux noms de groupes à lier.
    groupes (dict): Un dictionnaire où les clés sont les noms des groupes et les valeurs sont des listes de points [x,y].
    filepath (str): chemin du fichier de sortie
    epsilon : rayon du cercle autour des aiguilles, peut être généré automatiquement

    """
    if epsilon is None:
        liste_aiguilles = []
        for groupe in groupes:
            for aiguille in groupes[groupe]:
                if aiguille not in liste_aiguilles:
                    # On ne garde pas les doublons (si deux aiguilles dans des groupes différents ont la même position)
                    liste_aiguilles.append(aiguille)

        min_dist = float("inf")
        for i in range(len(liste_aiguilles)):
            for j in range(i + 1, len(liste_aiguilles)):
                p1 = liste_aiguilles[i]
                p2 = liste_aiguilles[j]
                dist = (p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2
                if dist < min_dist:
                    min_dist = dist
        epsilon = min(30, math.sqrt(min_dist) / 2.5)
        print(f"epsilon calculé : {epsilon}")

    data = {
        "nom": nom,
        "dimensions": [dim_y, dim_z],
        "epsilon": epsilon,
        "liens": liens,
        "groupes": groupes,
    }
    with open(filepath, "w") as outfile:
        yaml.dump(data, outfile, default_flow_style=None, sort_keys=False)


# Exemple d'utilisation pour générer un fichier similaire à lignes_paralleles.yaml
if __name__ == "__main__":
    nom_config = "test"
    dim_y, dim_z = 300, 400
    eps = 10
    group_data = {
        "ligne_haut": [[x, 50] for x in range(50, 321, 30)],
        "ligne_bas": [[x, 110] for x in range(50, 321, 30)],
    }
    link_data = [["ligne_haut", "ligne_bas"]]
    output_path = "lignes_paralleles_genere.yaml"

    create_yaml_file(nom_config, dim_y, dim_z, link_data, group_data, output_path)
    print(f"Fichier YAML généré : {output_path}")
