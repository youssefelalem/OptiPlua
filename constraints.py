import pandas as pd

# C6 — Types de salles considérés comme 'laboratoire'
TYPES_LABO = {'Labo_Science', 'Labo_Informatique', 'Laboratoire'}

def verifier_contraintes(id_prof, id_salle, id_classe, creneau,
                         heures_prof, indispo_prof,
                         max_heures_prof,
                         occupations_prof, occupations_salle, occupations_classe):
    """
    Retourne (True, '') si le placement est valide, sinon (False, raison).
    Contraintes vérifiées :
      C1 - Prof déjà occupé à ce créneau
      C2 - Salle déjà réservée à ce créneau
      C3 - Classe déjà assignée à ce créneau
      C4 - Créneau dans les indisponibilités du prof
      C5 - Limite d'heures hebdomadaires dépassée
    """
    if creneau in occupations_prof.get(id_prof, set()):
        return False, 'C1_prof_occupe'
    if creneau in occupations_salle.get(id_salle, set()):
        return False, 'C2_salle_occupee'
    if creneau in occupations_classe.get(id_classe, set()):
        return False, 'C3_classe_occupee'
    if creneau in indispo_prof:
        return False, 'C4_indispo'
    if heures_prof.get(id_prof, 0) >= max_heures_prof:
        return False, 'C5_max_heures'
    return True, ''

def calculer_score_emploi(df_emploi):
    """
    Calcule la qualité d'un emploi du temps (0-100) avec normalisation.
    Pénalités :
    - Trous enseignants : -2 pts par heure de gap sur une même journée.
    - Sous-utilisation : -1.5 pts par séance si taux de remplissage < 40%.
    Logique : Score = 100 * (1 - (penalité_totale / (nb_seances * 3)))
    """
    total_seances = len(df_emploi)
    if total_seances == 0: return 0.0, {}

    penalite_trous = 0
    penalite_salles = 0

    # 1. Calcul des trous (Gaps) pour les enseignants
    df_temp = df_emploi.copy()
    # On s'assure que les colonnes Heure_Debut et Heure_Fin sont bien parsées
    df_temp['H_Debut_Int'] = df_temp['Heure_Debut'].apply(lambda x: int(x.split(':')[0]))
    df_temp['H_Fin_Int']   = df_temp['Heure_Fin'].apply(lambda x: int(x.split(':')[0]))

    for (id_prof, jour), group in df_temp.groupby(['ID_Enseignant', 'Jour']):
        group = group.sort_values('H_Debut_Int')
        slots = group.to_dict('records')
        
        for i in range(len(slots) - 1):
            fin_actuelle = slots[i]['H_Fin_Int']
            debut_suivante = slots[i+1]['H_Debut_Int']
            gap = debut_suivante - fin_actuelle
            if gap > 0:
                penalite_trous += gap * 2

    # 2. Calcul de la sous-utilisation des salles
    df_temp['Taux_Remplissage'] = df_temp['Nb_Etudiants'] / df_temp['Capacite_Salle']
    nb_sous_util = len(df_temp[df_temp['Taux_Remplissage'] < 0.4])
    penalite_salles = nb_sous_util * 1.5

    # 3. Normalisation
    penalite_totale = penalite_trous + penalite_salles
    max_penalite_tolerable = total_seances * 3.0
    
    score_final = max(0.0, 100.0 * (1 - (penalite_totale / max_penalite_tolerable)))
    score_final = round(score_final, 2)
    
    details = {
        'score_final': score_final,
        'penalite_trous': penalite_trous,
        'penalite_salles': penalite_salles,
        'nb_sous_util': nb_sous_util,
        'total_seances': total_seances
    }
    return score_final, details
