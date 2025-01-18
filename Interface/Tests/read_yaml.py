
import yaml

# Ouvrir et lire le fichier YAML
with open('ex_points.yaml','r') as file:
    data = yaml.safe_load(file)

# Afficher contenu du fichier YAML
print(data)

# Récupération des points
for p in data['groupes']['groupe1']:
    print(f"x={p[0]}, y={p[1]}")

# Impression des groupes de points pour chaque lien
for l in data['liens']:
    print(data["groupes"][l[0]])
    print(data["groupes"][l[1]])