# PIE Tricotissage 2024-2025

#### Membres de l'équipe 

- Mohamed Salim Ben Noomen
- Pierre Bordeau
- Élodie De Brito
- Auriane Martel
- Adrien Scarfoglière

## Présentation

Ce PIE consiste en l'amélioration d'une machine de tricotissage existante. La machine est pilotée avec une carte Arduino Nano sur laquelle tourne une version légèrement modifiée de [Grbl](https://github.com/gnea/grbl).

Nous avons entièrement réécrit les programmes permettant de générer le GCode à envoyer à la machine. Les programmes Python permettent de générer à partir d'une image un schéma de tricotissage (position des aiguilles des différents groupes), puis de générer les programmes GCode de marquage et de tricotissage.

Les Programmes GCode peuvent être envoyés à la machine via le logiciel [UGS](https://winder.github.io/ugs_website/).

## Architecture du dépôt 

- `src/` : Contient le code source du projet
- `detpts/` : Contient les fonctions de détections de points afin de placer les aiguilles
- `yaml_files/` : Contient les fichiers correspondant aux schémas de tricotissage, au format YAML
- `prgs_gcode/` : Contient les fichiers GCode à envoyer à la machine
- `grbl/` : Contient les codes sources Grbl modifiés pour la machine (notamment pour l'ajout du servomoteur pour le marquage). Ce dossier doit être copié dans le répertoire des librairies d'Arduino IDE pour ensuite être envoyé à l'Arduino s'il s'agit d'une nouvelle carte Arduino.
- Le fichier `TODO` contient les paramètres de la machine, à envoyer à l'Arduino via UGS s'il s'agit d'une nouvelle carte Arduino.