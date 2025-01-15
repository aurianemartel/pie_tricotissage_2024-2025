import matplotlib.pyplot as plt
import matplotlib.patches as patches
import json
import re
import sys

def parse_gcode(gcode):
    """Parse le G-code et retourne une liste de mouvements."""
    mouvements = []
    x, y = None, None  # Position initiale
    for ligne in gcode.splitlines():
        ligne = ligne.strip()
        if ligne.startswith('G0'):
            match = re.match(r'G0\s+X([\d.-]+)\s+Y([\d.-]+)', ligne)
            if match:
                new_x, new_y = float(match.group(1)), float(match.group(2))
                if x is not None:
                    mouvements.append({'type': 'G0', 'x1': x, 'y1': y, 'x2': new_x, 'y2': new_y})
                x, y = new_x, new_y
            else:
                match = re.match(r'G0\s+Y([\d.-]+)', ligne)
                if match:
                    new_y = float(match.group(1))
                    if y is not None:
                        mouvements.append({'type': 'G0', 'x1': x, 'y1': y, 'x2': x, 'y2': new_y})
                    y = new_y
                else:
                    match = re.match(r'G0\s+X([\d.-]+)', ligne)
                    if match:
                        new_x = float(match.group(1))
                        if x is not None:
                            mouvements.append({'type': 'G0', 'x1': x, 'y1': y, 'x2': new_x, 'y2': y})
                        x = new_x
                    else:
                        print("Ne matche pas G0 >> " + ligne)
        elif ligne.startswith('G2'):
            match = re.match(r'G2\s+X([\d.-]+)\s+Y([\d.-]+)\s+I([\d.-]+)\s+J([\d.-]+)', ligne)
            if match:
                new_x, new_y, i, j = map(float, match.groups())
                mouvements.append({'type': 'G2', 'x1': x, 'y1': y, 'x2': new_x, 'y2': new_y, 'i': i, 'j': j})
                x, y = new_x, new_y
            else:
                print("Ne matche pas >> G2" + ligne)
        elif ligne.startswith('G3'):
            match = re.match(r'G3\s+X([\d.-]+)\s+Y([\d.-]+)\s+I([\d.-]+)\s+J([\d.-]+)', ligne)
            if match:
                new_x, new_y, i, j = map(float, match.groups())
                mouvements.append({'type': 'G3', 'x1': x, 'y1': y, 'x2': new_x, 'y2': new_y, 'i': i, 'j': j})
                x, y = new_x, new_y
            else:
                print("Ne matche pas >> G2" + ligne)
    print(json.dumps(mouvements, indent=4, sort_keys=True))
    return mouvements

def plot_gcode(mouvements):
    """Trace les mouvements du G-code."""
    plt.figure(figsize=(10, 10))
    for mouvement in mouvements:
        if mouvement['type'] == 'G0':
            plt.plot([mouvement['x1'], mouvement['x2']], [mouvement['y1'], mouvement['y2']], 'b--', label='G0' if 'G0' not in plt.gca().get_legend_handles_labels()[1] else "") # bleu pointillé
        elif mouvement['type'] == 'G2': #Modifier sens de rotation pour G2
            centre_x = mouvement['x1'] + mouvement['i']
            centre_y = mouvement['y1'] + mouvement['j']
            rayon = ((mouvement['i'])**2 + (mouvement['j'])**2)**0.5
            start_angle = np.arctan2(mouvement['y2']-centre_y, mouvement['x2']-centre_x) * 180 / np.pi
            end_angle = np.arctan2(mouvement['y1']-centre_y, mouvement['x1']-centre_x) * 180 / np.pi
            if mouvement['x1'] == mouvement['x2'] and mouvement['y1'] == mouvement['y2']:
              plt.gca().add_patch(patches.Circle((centre_x, centre_y), rayon, fill=False, color='r', label='G2 Cercle' if 'G2 Cercle' not in plt.gca().get_legend_handles_labels()[1] else ""))
            else:
              plt.gca().add_patch(patches.Arc((centre_x, centre_y), 2*rayon, 2*rayon, theta1=start_angle, theta2=end_angle, color='r', label='G2 Arc' if 'G2 Arc' not in plt.gca().get_legend_handles_labels()[1] else "")) # rouge
        elif mouvement['type'] == 'G3':
            centre_x = mouvement['x1'] + mouvement['i']
            centre_y = mouvement['y1'] + mouvement['j']
            rayon = ((mouvement['i'])**2 + (mouvement['j'])**2)**0.5
            start_angle = np.arctan2(mouvement['y1']-centre_y, mouvement['x1']-centre_x) * 180 / np.pi
            end_angle = np.arctan2(mouvement['y2']-centre_y, mouvement['x2']-centre_x) * 180 / np.pi
            if mouvement['x1'] == mouvement['x2'] and mouvement['y1'] == mouvement['y2']:
              plt.gca().add_patch(patches.Circle((centre_x, centre_y), rayon, fill=False, color='r', label='G2 Cercle' if 'G2 Cercle' not in plt.gca().get_legend_handles_labels()[1] else ""))
            else:
              plt.gca().add_patch(patches.Arc((centre_x, centre_y), 2*rayon, 2*rayon, theta1=start_angle, theta2=end_angle, color='r', label='G2 Arc' if 'G2 Arc' not in plt.gca().get_legend_handles_labels()[1] else "")) # rouge
    
    plt.xlabel('X')
    plt.ylabel('Y')
    plt.title('Visualisation du G-code')
    plt.axis('equal') # Important pour que les cercles ne soient pas déformés
    plt.grid(True)
    plt.legend()
    plt.show()

import numpy as np

def lire_fichier_rapide(nom_fichier):
    with open(nom_fichier, 'r') as f:
        return f.read()

fichier_gcode = sys.argv[1]
contenu = lire_fichier_rapide(fichier_gcode)

mouvements = parse_gcode(contenu)
plot_gcode(mouvements)
