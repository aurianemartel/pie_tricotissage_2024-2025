import elodie1
import elodie2
if __name__ == '__main__':
    #print_hi('PyCharm')
    chemin = "C:\\Users\\debri\\OneDrive\\Bureau\\ENSTA\\PIE\\premier_jet_python\\image.png"
    lx, ly, longueurs, pmpg = elodie1.elodie1(chemin, epsilon=0.01, afficher_im_init=False, afficher_squelette=False)
    print("elodie1 terminée")
    elodie2.elodie2(pmpg, 0.25, -100, -100, [10 for i in range(len(pmpg))], afficher_points_pre_scale=False)
    #elodie2.elodie2(pmpg, 2, 0, 0, [50, 10], afficher_points_pre_scale=False)