G21 ; Definir les unites en millimetres
G90 ; Positionnement absolu
G17 ; XY plan
G40 
G49 
G0 X1000 Y500
 
G0 Y448
G0 X607.9
G2 X607.9 Y448 I5 J5 
 
G2 X617.9 Y458 I5 J5 
 
M0 ; Mettre en pause le programme 
;MSG Lacher le bouton 
 
G0 X856.4 Y188.5
G0 X856.4 Y182.5
G2 X443.4 Y182.5 I-206.5 J1.5
G0 X443.4 Y188.5
 