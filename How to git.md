# Description

## Setup : créer une nouvelle branche

git branch _nom de branche_    --> chacun a sa branche perso

## Commencer à travailler :

git checkout _nom de branche_  --> le travail est effectué sur une branche de dév perso
git merge main                 --> ajouter les changements du main dans la branche perso

## Fin de chaque période de travail :

git add -A .                    --> Prépare les modifs pour le commit
git commit -m "mon commentaire" --> Commenter ce qui a changé dans ce commit
git push                        --> Ajoute les modifs sur le git

....

## Insérer une partie fonctionnelle au main :

git merge main
_tester que tout fonctionne_

git push
git checkout main
git merge _nom de branche_
git push
git checkout _nom de branche_


