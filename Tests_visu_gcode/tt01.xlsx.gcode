G21 ; Definir les unites en millimetres
G90 ; Positionnement absolu
G17 ; XY plan
G40 
G49 
G0 X1000 Y500
 
G0 X254.9
G0 Y393.0
G2 X254.9 Y393.0 I5 J5 
 
G2 X264.9 Y403.0 I5 J5 
 
M0 ; Mettre en pause le programme 
;MSG Lacher le bouton 
 
G0 X538.9 Y210.5
G0 X538.9 Y204.5
G2 X426.9 Y204.5 I-56.0 J1.5
G0 X426.9 Y210.5
 
M0 ; Mettre en pause le programme 
;MSG Lacher le bouton 
 
G0 X254.9 Y393.0
G2 X254.9 Y393.0 I5 J5
 
M0 ; Mettre en pause le programme 
;MSG Lacher le bouton 
 
G0 X425.9 Y211.0
G0 X425.9 Y201.0
G2 X315.9 Y201.0 I-55.0 J5
G0 X315.9 Y211.0
 
M0 ; Mettre en pause le programme 
;MSG Lacher le bouton 
 
G0 X254.9 Y393.0
G2 X254.9 Y393.0 I5 J5
 
;MSG Decouper le fil 
 
G0 X1000 Y500
 
