import det_trace
import generer_pos_aig
if __name__ == '__main__':
    chemin = "horizon.png"
    lx, ly, longueurs, pmpg = det_trace.detection_trace(chemin, epsilon=0.01, afficher_im_init=False, afficher_squelette=False)
    generer_pos_aig.generer_pos_aiguilles(pmpg, 1, 0, 0, [50 for i in range(len(pmpg))],"figure.png", afficher_points_pre_scale=False)