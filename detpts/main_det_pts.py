import det_trace
import generer_pos_aig
if __name__ == '__main__':
    chemin = "4gpes.png"
    lx, ly, longueurs, pmpg = det_trace.detection_trace(chemin, epsilon=0.01, afficher_im_init=False, afficher_squelette=False)
    _, longueur_min = generer_pos_aig.generer_pos_aiguilles(pmpg, 1, 0, 0, [10 for i in range(len(pmpg))],"4gpes.png", afficher_points_pre_scale=False)
    #print(longueur_min)
