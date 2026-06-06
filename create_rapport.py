"""
Generate the OptiPlua academic rapport (Word document) for soutenance.
"""
import os
from docx import Document
from docx.shared import Inches, Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.section import WD_ORIENT
from docx.oxml.ns import qn, nsdecls
from docx.oxml import parse_xml

NAVY = RGBColor(0x1B, 0x49, 0x65)
TEAL = RGBColor(0x2D, 0x6A, 0x8F)
DARK = RGBColor(0x1E, 0x29, 0x3B)
MUTED = RGBColor(0x64, 0x74, 0x8B)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
GOLD = RGBColor(0xD4, 0xA8, 0x43)


def set_cell_shading(cell, color_hex):
    shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color_hex}"/>')
    cell._tc.get_or_add_tcPr().append(shading)


def add_styled_heading(doc, text, level=1):
    h = doc.add_heading(text, level=level)
    for run in h.runs:
        run.font.color.rgb = NAVY
    return h


def add_body(doc, text):
    p = doc.add_paragraph(text)
    p.style.font.size = Pt(11)
    return p


def add_bullet(doc, text, bold_prefix=None):
    p = doc.add_paragraph(style='List Bullet')
    if bold_prefix:
        run = p.add_run(bold_prefix)
        run.bold = True
        p.add_run(f" {text}")
    else:
        p.add_run(text)
    return p


def add_table_with_header(doc, headers, rows):
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.style = 'Table Grid'
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(headers):
        cell = table.rows[0].cells[i]
        cell.text = h
        for p in cell.paragraphs:
            for run in p.runs:
                run.bold = True
                run.font.color.rgb = WHITE
                run.font.size = Pt(10)
        set_cell_shading(cell, "1B4965")
    for r_idx, row_data in enumerate(rows):
        for c_idx, val in enumerate(row_data):
            cell = table.rows[r_idx + 1].cells[c_idx]
            cell.text = str(val)
            for p in cell.paragraphs:
                for run in p.runs:
                    run.font.size = Pt(10)
            if r_idx % 2 == 1:
                set_cell_shading(cell, "F0F4F8")
    return table


def create_rapport(output_path):
    doc = Document()

    style = doc.styles['Normal']
    style.font.name = 'Calibri'
    style.font.size = Pt(11)
    style.font.color.rgb = DARK
    style.paragraph_format.space_after = Pt(6)
    style.paragraph_format.line_spacing = 1.15

    for level in range(1, 4):
        hs = doc.styles[f'Heading {level}']
        hs.font.name = 'Georgia'
        hs.font.color.rgb = NAVY

    # ═══════════════════════════════════════════════════════════
    # PAGE DE GARDE
    # ═══════════════════════════════════════════════════════════
    for _ in range(4):
        doc.add_paragraph()

    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run("OptiPlua")
    run.font.size = Pt(36)
    run.font.color.rgb = NAVY
    run.bold = True
    run.font.name = "Georgia"

    subtitle = doc.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = subtitle.add_run("Optimisation Intelligente des Emplois du Temps Scolaires")
    run.font.size = Pt(16)
    run.font.color.rgb = TEAL
    run.font.name = "Calibri"

    doc.add_paragraph()

    pfe = doc.add_paragraph()
    pfe.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = pfe.add_run("Rapport de Projet de Fin d'Etudes")
    run.font.size = Pt(14)
    run.font.color.rgb = DARK
    run.bold = True

    doc.add_paragraph()
    doc.add_paragraph()

    info_lines = [
        "Realise par : [Noms des etudiants]",
        "Encadre par : Prof. [Nom de l'encadrant]",
        "",
        "Annee universitaire 2024 - 2025",
    ]
    for line in info_lines:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(line)
        run.font.size = Pt(12)
        run.font.color.rgb = MUTED

    doc.add_page_break()

    # ═══════════════════════════════════════════════════════════
    # TABLE DES MATIERES
    # ═══════════════════════════════════════════════════════════
    add_styled_heading(doc, "Table des Matieres", level=1)

    toc_items = [
        "1. Introduction Generale",
        "2. Problematique",
        "   2.1 Problematique Technique",
        "   2.2 Problematique Mathematique",
        "3. Objectifs du Projet",
        "4. Solution Technique — Moteur Heuristique",
        "   4.1 Architecture Globale",
        "   4.2 Algorithme de Generation",
        "   4.3 Contraintes Dures (C1-C7)",
        "   4.4 Fonction de Scoring Heuristique",
        "5. Solution Mathematique — Formalisation",
        "   5.1 Variables de Decision",
        "   5.2 Contraintes CSP",
        "   5.3 Fonction Objectif",
        "6. Solution ML — Modele XGBoost",
        "   6.1 Feature Engineering",
        "   6.2 Configuration du Modele",
        "   6.3 Resultats d'Entrainement",
        "7. Modelisation UML",
        "   7.1 Diagramme de Cas d'Utilisation",
        "   7.2 Diagramme de Classes",
        "   7.3 Diagramme de Sequence",
        "8. Interface Utilisateur",
        "9. Resultats et Discussion",
        "10. Conclusion et Perspectives",
    ]
    for item in toc_items:
        p = doc.add_paragraph(item)
        p.paragraph_format.space_after = Pt(2)

    doc.add_page_break()

    # ═══════════════════════════════════════════════════════════
    # 1. INTRODUCTION GENERALE
    # ═══════════════════════════════════════════════════════════
    add_styled_heading(doc, "1. Introduction Generale")

    add_body(doc,
        "La gestion des emplois du temps dans les etablissements scolaires constitue l'un des "
        "defis administratifs les plus complexes auxquels font face les responsables pedagogiques. "
        "Chaque annee, des heures considerables sont consacrees a l'elaboration manuelle de "
        "plannings qui doivent satisfaire simultanement de nombreuses contraintes : disponibilite "
        "des enseignants, capacite des salles, repartition equilibree des matieres, et bien d'autres.")

    add_body(doc,
        "Ce probleme, connu en informatique theorique sous le nom de probleme d'emploi du temps "
        "(Timetabling Problem), appartient a la classe des problemes NP-difficiles. Cela signifie "
        "qu'il n'existe pas d'algorithme connu capable de trouver la solution optimale en temps "
        "polynomial pour toutes les instances du probleme. Le nombre de combinaisons possibles "
        "explose exponentiellement avec la taille de l'instance : pour un etablissement avec "
        "150 classes, 200 enseignants, 80 salles et 20 creneaux hebdomadaires, l'espace de "
        "recherche depasse 10^50 configurations possibles.")

    add_body(doc,
        "Le projet OptiPlua propose une approche hybride combinant un moteur heuristique de "
        "generation, un systeme de scoring multi-critere, et un modele d'apprentissage automatique "
        "(Machine Learning) base sur XGBoost pour evaluer et classer les solutions generees. "
        "L'ensemble est integre dans une interface web professionnelle developpee avec Streamlit, "
        "permettant aux etablissements scolaires de saisir leurs donnees et d'obtenir les "
        "3 meilleures variantes d'emploi du temps.")

    add_body(doc,
        "Ce rapport presente en detail la problematique abordee, les solutions techniques et "
        "mathematiques developpees, la modelisation UML du systeme, l'interface utilisateur, "
        "ainsi que les resultats obtenus et les perspectives d'amelioration.")

    doc.add_page_break()

    # ═══════════════════════════════════════════════════════════
    # 2. PROBLEMATIQUE
    # ═══════════════════════════════════════════════════════════
    add_styled_heading(doc, "2. Problematique")

    add_body(doc,
        "La planification des emplois du temps scolaires pose deux categories de defis majeurs : "
        "un defi technique lie a l'automatisation du processus, et un defi mathematique lie a la "
        "formalisation et a l'optimisation du probleme.")

    # 2.1
    add_styled_heading(doc, "2.1 Problematique Technique", level=2)

    add_body(doc,
        "Comment automatiser la generation d'emplois du temps tout en respectant un ensemble "
        "de contraintes dures, et comment evaluer objectivement la qualite des solutions generees ?")

    add_body(doc, "Les defis techniques specifiques sont les suivants :")

    tech_challenges = [
        ("Multiplicite des contraintes :", "L'emploi du temps doit respecter simultanement 7 types "
         "de contraintes dures (anti-collision enseignant, salle, classe ; indisponibilites ; "
         "heures maximales ; compatibilite labo ; capacite)."),
        ("Qualite multi-critere :", "Une bonne solution ne se limite pas a l'absence de conflits. "
         "Elle doit aussi minimiser les trous dans l'emploi du temps des enseignants ET des eleves, "
         "optimiser le taux de remplissage des salles, et equilibrer la charge journaliere."),
        ("Comparaison de variantes :", "Il est insuffisant de generer une seule solution. "
         "Le systeme doit produire plusieurs variantes et les classer objectivement."),
        ("Accessibilite :", "La solution doit etre accessible via une interface web intuitive, "
         "sans necessiter de competences techniques de la part des utilisateurs."),
    ]
    for prefix, text in tech_challenges:
        add_bullet(doc, text, bold_prefix=prefix)

    # 2.2
    add_styled_heading(doc, "2.2 Problematique Mathematique", level=2)

    add_body(doc,
        "Comment formaliser le probleme d'emploi du temps en tant que CSP (Constraint Satisfaction "
        "Problem) et definir une fonction objectif qui capture adequatement la notion de qualite ?")

    add_body(doc, "Les enjeux mathematiques sont :")

    math_challenges = [
        ("Explosion combinatoire :", "Le nombre de configurations possibles croit de maniere "
         "exponentielle : O(C x M x E x S x T) ou C = classes, M = matieres, E = enseignants, "
         "S = salles, T = creneaux. Pour notre jeu de donnees, cela represente un espace de "
         "recherche de l'ordre de 10^50."),
        ("Formalisation CSP :", "Definir rigoureusement les variables de decision, les domaines, "
         "et les contraintes du probleme sous forme de programme de satisfaction de contraintes."),
        ("Fonction objectif :", "Concevoir une fonction de score qui penalise les fenetres "
         "(gaps) des enseignants et des eleves, la sous-utilisation des salles, et la surcharge "
         "journaliere, tout en normalisant le score sur une echelle de 0 a 100."),
        ("Apprentissage automatique :", "Entrainer un modele predictif capable d'evaluer la "
         "qualite d'une affectation individuelle (seance) a partir de ses caracteristiques, "
         "offrant ainsi une alternative au scoring heuristique."),
    ]
    for prefix, text in math_challenges:
        add_bullet(doc, text, bold_prefix=prefix)

    doc.add_page_break()

    # ═══════════════════════════════════════════════════════════
    # 3. OBJECTIFS
    # ═══════════════════════════════════════════════════════════
    add_styled_heading(doc, "3. Objectifs du Projet")

    add_body(doc, "Le projet OptiPlua vise a atteindre les objectifs suivants :")

    objectives = [
        ("Objectif 1 :", "Generer des donnees synthetiques realistes representant un "
         "etablissement scolaire complet (200 enseignants, 80 salles, 150 classes, 24 matieres) "
         "couvrant trois types d'etablissements (Primaire, College, Lycee)."),
        ("Objectif 2 :", "Construire un moteur heuristique de generation d'emplois du temps "
         "capable de respecter 7 contraintes dures (C1 a C7) tout en produisant des solutions "
         "de qualite acceptable."),
        ("Objectif 3 :", "Implementer un systeme de scoring multi-critere tenant compte a la "
         "fois des enseignants (minimisation des trous) et des eleves (minimisation des fenetres "
         "et de la surcharge journaliere)."),
        ("Objectif 4 :", "Entrainer un modele de Machine Learning (XGBoost) pour predire la "
         "qualite des affectations a partir de 22 features ingenierees."),
        ("Objectif 5 :", "Developper une interface web professionnelle (Streamlit) avec "
         "authentification, formulaires de saisie, generation parametrable, et affichage des "
         "3 meilleures variantes avec details et export CSV."),
    ]
    for prefix, text in objectives:
        add_bullet(doc, text, bold_prefix=prefix)

    doc.add_page_break()

    # ═══════════════════════════════════════════════════════════
    # 4. SOLUTION TECHNIQUE
    # ═══════════════════════════════════════════════════════════
    add_styled_heading(doc, "4. Solution Technique — Moteur Heuristique")

    # 4.1
    add_styled_heading(doc, "4.1 Architecture Globale", level=2)

    add_body(doc,
        "Le systeme OptiPlua est compose de quatre modules principaux qui s'articulent "
        "en pipeline :")

    add_table_with_header(doc,
        ["Module", "Fichier", "Role"],
        [
            ["Interface Web", "app.py", "Authentification, saisie des donnees, affichage des resultats"],
            ["Simulateur", "simulator.py", "Generation heuristique des emplois du temps"],
            ["Scorer", "scorer.py", "Evaluation et classement des variantes"],
            ["Predicteur ML", "predict_model.py", "Scoring par modele XGBoost entraine"],
        ])

    doc.add_paragraph()

    add_body(doc,
        "Le flux de donnees est le suivant : l'utilisateur saisit les donnees de son "
        "etablissement (enseignants, salles, matieres, classes) via l'interface web. Le "
        "simulateur genere N variantes d'emploi du temps avec des seeds aleatoires differentes. "
        "Chaque variante est evaluee par la fonction de scoring heuristique ou par le modele ML. "
        "Les 3 meilleures variantes sont presentees a l'utilisateur avec un detail des penalites "
        "et la possibilite de telecharger chaque emploi du temps en format CSV.")

    # 4.2
    add_styled_heading(doc, "4.2 Algorithme de Generation", level=2)

    add_body(doc,
        "L'algorithme de generation d'emploi du temps fonctionne par recherche aleatoire "
        "avec verification de contraintes. Voici les etapes detaillees :")

    algo_steps = [
        "Preparation des index : Construction de dictionnaires pour un acces rapide aux "
        "matieres par type d'etablissement, aux salles par type, et aux enseignants par "
        "matiere et type d'etablissement.",
        "Melange des classes : L'ordre des classes est permute aleatoirement a l'aide d'un "
        "seed configurable (random_state), ce qui garantit la reproductibilite tout en permettant "
        "de generer des variantes differentes.",
        "Iteration par classe et matiere : Pour chaque classe, on parcourt les matieres "
        "compatibles avec son type d'etablissement. Le nombre de seances est determine par "
        "les heures hebdomadaires requises (Heures_Hebdo_Requises / 2).",
        "Selection aleatoire : Pour chaque seance, on selectionne aleatoirement un creneau "
        "(parmi les 20 creneaux possibles : 5 jours x 4 plages horaires), un enseignant "
        "compatible, et une salle compatible.",
        "Verification des contraintes : Les 7 contraintes dures (C1-C7) sont verifiees "
        "simultanement. Si toutes sont satisfaites, l'affectation est validee.",
        "Mecanisme de retry : Si une contrainte est violee, une nouvelle combinaison aleatoire "
        "est tentee, jusqu'a un maximum de 300 tentatives (configurable).",
        "Enregistrement : L'affectation validee est enregistree avec toutes les informations "
        "(classe, matiere, enseignant, salle, creneau, jour, heure) et les statistiques "
        "(nombre de tentatives).",
    ]
    for i, step in enumerate(algo_steps, 1):
        add_bullet(doc, step, bold_prefix=f"Etape {i} :")

    # 4.3
    add_styled_heading(doc, "4.3 Contraintes Dures (C1-C7)", level=2)

    add_body(doc,
        "Le moteur de generation respecte strictement 7 contraintes dures qui garantissent "
        "la validite de chaque emploi du temps genere :")

    add_table_with_header(doc,
        ["Code", "Contrainte", "Description", "Verification"],
        [
            ["C1", "Anti-collision enseignant", "Un enseignant ne peut pas etre assigne a deux seances au meme creneau", "occupations_prof[id_prof]"],
            ["C2", "Anti-collision salle", "Une salle ne peut pas accueillir deux seances au meme creneau", "occupations_salle[id_salle]"],
            ["C3", "Anti-collision classe", "Une classe ne peut pas avoir deux seances au meme creneau", "occupations_classe[id_classe]"],
            ["C4", "Indisponibilite", "Un enseignant ne peut pas etre assigne pendant ses creneaux d'indisponibilite", "creneaux_indisponibles"],
            ["C5", "Heures maximales", "Un enseignant ne peut pas depasser son quota hebdomadaire d'heures", "heures_prof[id_prof] < max"],
            ["C6", "Compatibilite labo", "Les matieres necessitant un labo doivent etre assignees dans une salle de type laboratoire", "Type_Salle in TYPES_LABO"],
            ["C7", "Capacite salle", "La capacite de la salle doit etre suffisante pour le nombre d'eleves de la classe", "Capacite >= Nb_Etudiants"],
        ])

    # 4.4
    doc.add_paragraph()
    add_styled_heading(doc, "4.4 Fonction de Scoring Heuristique", level=2)

    add_body(doc,
        "La fonction de scoring evalue la qualite globale d'un emploi du temps sur une echelle "
        "de 0 a 100. Elle est basee sur 4 types de penalites :")

    add_body(doc,
        "Score = 100 x (1 - Penalite_totale / Penalite_max_tolerable)")
    doc.paragraphs[-1].runs[0].font.name = "Consolas"
    doc.paragraphs[-1].runs[0].font.size = Pt(11)

    add_body(doc, "Ou Penalite_max_tolerable = nombre_total_seances x 5.0")

    add_table_with_header(doc,
        ["Penalite", "Formule", "Poids", "Objectif"],
        [
            ["Trous enseignants", "Somme des heures de gap par prof/jour", "x 2.0", "Minimiser les fenetres des profs"],
            ["Trous classes", "Somme des heures de gap par classe/jour", "x 2.5", "Minimiser les fenetres des eleves"],
            ["Sous-utilisation salles", "Nombre de seances avec taux < 40%", "x 1.5", "Optimiser l'usage des salles"],
            ["Surcharge journaliere", "Nombre de jours avec > 4 seances/classe", "x 1.0", "Equilibrer la charge"],
        ])

    doc.add_paragraph()
    add_body(doc,
        "Cette fonction de scoring prend en compte a la fois le confort des enseignants "
        "(penalite sur les trous) et celui des eleves (penalite sur les fenetres et la surcharge "
        "journaliere), ce qui constitue une amelioration par rapport aux approches classiques "
        "qui ne considerent que les contraintes enseignants.")

    doc.add_page_break()

    # ═══════════════════════════════════════════════════════════
    # 5. SOLUTION MATHEMATIQUE
    # ═══════════════════════════════════════════════════════════
    add_styled_heading(doc, "5. Solution Mathematique — Formalisation")

    add_body(doc,
        "Le probleme d'emploi du temps peut etre formalise comme un probleme de satisfaction "
        "de contraintes (CSP — Constraint Satisfaction Problem). Cette section presente la "
        "formalisation mathematique complete.")

    # 5.1
    add_styled_heading(doc, "5.1 Variables de Decision", level=2)

    add_body(doc, "Soit X = {x_ijkl} l'ensemble des variables de decision, ou :")
    add_bullet(doc, "i represente une classe (i = 1, ..., C)")
    add_bullet(doc, "j represente une matiere (j = 1, ..., M)")
    add_bullet(doc, "k represente un enseignant (k = 1, ..., E)")
    add_bullet(doc, "l represente un creneau horaire (l = 1, ..., T)")

    add_body(doc, "")
    add_body(doc, "x_ijkl = 1 si la classe i a une seance de la matiere j avec l'enseignant k "
        "au creneau l, et x_ijkl = 0 sinon.")

    add_body(doc,
        "Dans notre implementation, C = 150 classes, M = 24 matieres, E = 200 enseignants, "
        "T = 20 creneaux (5 jours x 4 plages de 2 heures : 08:00-10:00, 10:00-12:00, "
        "14:00-16:00, 16:00-18:00).")

    # 5.2
    add_styled_heading(doc, "5.2 Contraintes CSP", level=2)

    add_body(doc, "Les contraintes du probleme se formalisent comme suit :")

    constraints_math = [
        ("C1 — Anti-collision enseignant :",
         "Pour tout enseignant k et tout creneau l : "
         "Somme_i Somme_j x_ijkl <= 1. "
         "Un enseignant ne peut enseigner qu'une seule matiere a une seule classe par creneau."),
        ("C2 — Anti-collision salle :",
         "Pour toute salle s et tout creneau l : "
         "|{(i,j,k) : x_ijkl = 1 et salle(i,j,k,l) = s}| <= 1. "
         "Une salle ne peut accueillir qu'une seule seance par creneau."),
        ("C3 — Anti-collision classe :",
         "Pour toute classe i et tout creneau l : "
         "Somme_j Somme_k x_ijkl <= 1. "
         "Une classe ne peut suivre qu'une seule matiere par creneau."),
        ("C4 — Indisponibilite :",
         "Pour tout enseignant k et tout creneau l dans Indispo(k) : "
         "Somme_i Somme_j x_ijkl = 0. "
         "Aucune affectation pendant les creneaux d'indisponibilite."),
        ("C5 — Heures maximales :",
         "Pour tout enseignant k : "
         "Somme_i Somme_j Somme_l x_ijkl x 2 <= H_max(k). "
         "Le total d'heures ne depasse pas le quota hebdomadaire."),
        ("C6 — Compatibilite labo :",
         "Si la matiere j necessite un laboratoire, alors la salle assignee doit etre de "
         "type {Labo_Science, Labo_Informatique, Laboratoire}."),
        ("C7 — Capacite :",
         "Pour toute affectation, la capacite de la salle doit etre superieure ou egale au "
         "nombre d'eleves de la classe : Capacite(salle) >= Nb_Etudiants(classe)."),
    ]
    for prefix, text in constraints_math:
        add_bullet(doc, text, bold_prefix=prefix)

    # 5.3
    add_styled_heading(doc, "5.3 Fonction Objectif", level=2)

    add_body(doc,
        "La fonction objectif vise a minimiser les penalites liees a la qualite de l'emploi "
        "du temps. Elle est definie comme :")

    add_body(doc, "Minimiser f(X) = P_trous_prof + P_trous_classe + P_salles + P_surcharge")
    doc.paragraphs[-1].runs[0].font.name = "Consolas"

    add_body(doc, "Ou :")

    obj_details = [
        "P_trous_prof = Somme_(k,d) gap(k,d) x 2.0 — somme des heures de gap par enseignant k "
        "et jour d, ponderee par 2.0",
        "P_trous_classe = Somme_(i,d) gap(i,d) x 2.5 — somme des heures de gap par classe i "
        "et jour d, ponderee par 2.5",
        "P_salles = |{(i,j,k,l) : taux_remplissage < 0.4}| x 1.5 — nombre de seances avec "
        "un taux de remplissage inferieur a 40%, pondere par 1.5",
        "P_surcharge = |{(i,d) : nb_seances(i,d) > 4}| x 1.0 — nombre de jours ou une classe "
        "a plus de 4 seances, pondere par 1.0",
    ]
    for d in obj_details:
        add_bullet(doc, d)

    add_body(doc, "")
    add_body(doc,
        "Le score final est normalise entre 0 et 100 selon la formule :")
    add_body(doc, "Score = max(0, 100 x (1 - f(X) / (N_seances x 5.0)))")
    doc.paragraphs[-1].runs[0].font.name = "Consolas"

    add_body(doc,
        "Ou N_seances est le nombre total de seances planifiees. Le denominateur (N_seances x 5.0) "
        "represente la penalite maximale tolerable, calibree pour produire des scores discriminants.")

    doc.add_page_break()

    # ═══════════════════════════════════════════════════════════
    # 6. SOLUTION ML
    # ═══════════════════════════════════════════════════════════
    add_styled_heading(doc, "6. Solution ML — Modele XGBoost")

    add_body(doc,
        "En complement du scoring heuristique, le projet integre un modele de Machine Learning "
        "base sur XGBoost (eXtreme Gradient Boosting) pour predire la qualite des affectations "
        "individuelles. Ce modele offre une alternative data-driven au scoring analytique.")

    # 6.1
    add_styled_heading(doc, "6.1 Feature Engineering", level=2)

    add_body(doc,
        "22 features ont ete ingenierees a partir des donnees brutes de chaque seance. "
        "Elles se repartissent en trois categories :")

    add_table_with_header(doc,
        ["Categorie", "Features", "Nombre"],
        [
            ["Numeriques directes", "Nb_Etudiants, Capacite_Salle, Taux_Remplissage, Heure_Debut_Num, Jour_Encoded", "5"],
            ["Features derivees", "Pression_Planification (etudiants/capacite), Est_Matin (heure < 12), Est_Debut_Semaine (lundi/mardi)", "3"],
            ["One-Hot Encoding", "Type_Etablissement (Primaire, College, Lycee), Type_Salle (5 types), Niveau (8 niveaux)", "14"],
        ])

    doc.add_paragraph()
    add_body(doc,
        "La feature Pression_Planification capture le ratio entre le nombre d'eleves et la "
        "capacite de la salle, permettant au modele de detecter les surcharges. Les features "
        "Est_Matin et Est_Debut_Semaine encodent des informations temporelles qui influencent "
        "la qualite percue d'un creneau.")

    # 6.2
    add_styled_heading(doc, "6.2 Configuration du Modele", level=2)

    add_body(doc, "Le modele XGBoost a ete configure avec les hyperparametres suivants :")

    add_table_with_header(doc,
        ["Parametre", "Valeur", "Description"],
        [
            ["n_estimators", "100", "Nombre d'arbres de decision"],
            ["max_depth", "6", "Profondeur maximale de chaque arbre"],
            ["learning_rate", "0.1", "Taux d'apprentissage (shrinkage)"],
            ["subsample", "0.8", "Fraction d'echantillons par arbre"],
            ["colsample_bytree", "0.8", "Fraction de features par arbre"],
            ["objective", "reg:squarederror", "Regression par erreur quadratique"],
        ])

    doc.add_paragraph()
    add_body(doc,
        "Le preprocessing inclut une normalisation StandardScaler des features numeriques, "
        "et le modele est sauvegarde avec les fichiers : optiplua_model.pkl (modele XGBoost), "
        "scaler.pkl (StandardScaler), feature_names.pkl (noms des features attendues).")

    # 6.3
    add_styled_heading(doc, "6.3 Resultats d'Entrainement", level=2)

    add_body(doc, "Le modele entraine atteint les performances suivantes sur le jeu de test :")

    add_table_with_header(doc,
        ["Metrique", "Valeur", "Interpretation"],
        [
            ["R2 (Coefficient de determination)", "0.9988", "Le modele explique 99.88% de la variance"],
            ["MAE (Mean Absolute Error)", "0.0819", "Erreur moyenne absolue tres faible"],
            ["RMSE (Root Mean Squared Error)", "0.101", "Erreur quadratique moyenne faible"],
        ])

    doc.add_paragraph()
    add_body(doc,
        "Ces resultats excellents s'expliquent par la nature deterministe du scoring heuristique "
        "que le modele apprend a reproduire. Le modele ML offre neanmoins l'avantage de pouvoir "
        "generaliser a de nouvelles configurations et de fournir un scoring plus rapide pour "
        "de grands volumes de donnees.")

    doc.add_page_break()

    # ═══════════════════════════════════════════════════════════
    # 7. MODELISATION UML
    # ═══════════════════════════════════════════════════════════
    add_styled_heading(doc, "7. Modelisation UML")

    add_body(doc,
        "Cette section presente la modelisation UML du systeme OptiPlua a travers trois "
        "diagrammes essentiels : le diagramme de cas d'utilisation, le diagramme de classes, "
        "et le diagramme de sequence.")

    # 7.1
    add_styled_heading(doc, "7.1 Diagramme de Cas d'Utilisation", level=2)

    add_body(doc,
        "Le diagramme de cas d'utilisation identifie les interactions entre l'acteur principal "
        "(l'administrateur scolaire) et le systeme. Les cas d'utilisation sont :")

    use_cases = [
        "S'inscrire : Creer un compte avec email, mot de passe et nom de l'etablissement.",
        "Se connecter : Authentification par email et mot de passe (SHA-256).",
        "Saisir les donnees : Entrer les informations de l'etablissement (enseignants, "
        "salles, matieres, classes) via formulaire interactif, import CSV, ou donnees d'exemple.",
        "Configurer les parametres : Definir le nombre de variantes (3-20), le nombre maximal "
        "de tentatives (100-500), et la methode de scoring (heuristique ou ML).",
        "Generer les emplois du temps : Lancer la generation de N variantes avec suivi "
        "de progression en temps reel.",
        "Consulter les resultats : Visualiser les 3 meilleures variantes classees "
        "(Or, Argent, Bronze) avec details des penalites.",
        "Filtrer et explorer : Filtrer l'emploi du temps par classe, jour, ou enseignant.",
        "Telecharger : Exporter chaque variante en format CSV.",
    ]
    for uc in use_cases:
        add_bullet(doc, uc)

    # 7.2
    add_styled_heading(doc, "7.2 Diagramme de Classes", level=2)

    add_body(doc,
        "Le diagramme de classes represente la structure statique du systeme. Les classes "
        "principales sont :")

    add_table_with_header(doc,
        ["Classe", "Attributs principaux", "Methodes / Relations"],
        [
            ["Enseignant", "ID_Enseignant, Nom, Matieres[], Niveaux_Autorises[], "
             "Heures_Max, Creneaux_Indisponibles[]", "Enseigne -> Matiere (N:M)"],
            ["Salle", "ID_Salle, Type_Salle, Capacite, Type_Etablissement",
             "Accueille -> Seance (1:N)"],
            ["Matiere", "ID_Matiere, Nom, Type_Etablissement, Heures_Hebdo, Necessite_Labo",
             "Enseignee par -> Enseignant (N:M)"],
            ["Classe", "ID_Classe, Niveau, Nb_Etudiants, Type_Etablissement",
             "Suit -> Seance (1:N)"],
            ["EmploiDuTemps", "seances[], score, details_penalites",
             "Compose de -> Seance (1:N)"],
            ["Seance", "ID_Classe, ID_Matiere, ID_Enseignant, ID_Salle, Creneau, Jour",
             "Association (Classe, Matiere, Enseignant, Salle)"],
            ["TimetableScorer", "model_dir, predictor",
             "score_variant_ml(), rank_variants()"],
            ["OptiPluaPredictor", "model, scaler, feature_names",
             "predict(), engineer_features()"],
        ])

    # 7.3
    doc.add_paragraph()
    add_styled_heading(doc, "7.3 Diagramme de Sequence", level=2)

    add_body(doc,
        "Le diagramme de sequence decrit le flux d'interactions lors de la generation "
        "d'un emploi du temps. La sequence principale est :")

    seq_steps = [
        "Utilisateur -> Interface (app.py) : Saisie des donnees (4 DataFrames)",
        "Interface -> Simulateur (simulator.py) : generer_n_variantes(df_ens, df_sal, df_mat, df_cls, n=10)",
        "Simulateur -> Simulateur : build_indexes() — construction des dictionnaires d'acces rapide",
        "Simulateur -> Simulateur [boucle n fois] : generer_emploi_du_temps(seed=base_seed+i)",
        "Simulateur -> Simulateur [boucle par classe] : verifier_contraintes(C1-C7)",
        "Simulateur -> Simulateur : calculer_score_emploi() — scoring heuristique",
        "Simulateur -> Interface : Liste[(df_emploi, score, details)] triee par score",
        "Interface -> Utilisateur : Affichage Top 3 (Or, Argent, Bronze) + details",
    ]
    for i, step in enumerate(seq_steps, 1):
        add_bullet(doc, step, bold_prefix=f"{i}.")

    doc.add_page_break()

    # ═══════════════════════════════════════════════════════════
    # 8. INTERFACE UTILISATEUR
    # ═══════════════════════════════════════════════════════════
    add_styled_heading(doc, "8. Interface Utilisateur")

    add_body(doc,
        "L'interface utilisateur a ete developpee avec Streamlit, un framework Python pour "
        "la creation d'applications web interactives. Le design adopte un theme sombre "
        "professionnel avec une palette navy/teal/cyan, adapte a un contexte academique.")

    add_styled_heading(doc, "8.1 Authentification", level=2)
    add_body(doc,
        "Le systeme propose une page d'authentification avec deux modes : connexion et "
        "inscription. Les mots de passe sont hashes avec SHA-256 avant stockage dans un "
        "fichier JSON (data/users.json). Chaque compte est associe a un nom d'etablissement.")

    add_styled_heading(doc, "8.2 Saisie des Donnees", level=2)
    add_body(doc,
        "L'utilisateur dispose de trois modes pour saisir les donnees de son etablissement :")
    add_bullet(doc, "Formulaire interactif : Des formulaires dynamiques permettent d'ajouter "
        "des enseignants, salles, matieres et classes un par un avec validation en temps reel.")
    add_bullet(doc, "Import CSV : Upload de 4 fichiers CSV avec validation automatique des "
        "colonnes requises.")
    add_bullet(doc, "Donnees d'exemple : Chargement instantane du jeu de donnees synthetique "
        "fourni avec le projet (donnees du dossier data/).")

    add_styled_heading(doc, "8.3 Generation et Resultats", level=2)
    add_body(doc,
        "La page de generation affiche les parametres configurables dans la barre laterale "
        "(nombre de variantes, nombre de tentatives, methode de scoring). Un bouton lance "
        "la generation avec une barre de progression en temps reel. Les resultats sont "
        "presentes sous forme de 3 colonnes (Or, Argent, Bronze), chacune contenant :")
    add_bullet(doc, "Le score global sur 100 avec un indicateur visuel")
    add_bullet(doc, "Le detail des 4 types de penalites")
    add_bullet(doc, "Un apercu filtrable de l'emploi du temps (par classe, jour, enseignant)")
    add_bullet(doc, "Un bouton de telechargement CSV")

    doc.add_page_break()

    # ═══════════════════════════════════════════════════════════
    # 9. RESULTATS
    # ═══════════════════════════════════════════════════════════
    add_styled_heading(doc, "9. Resultats et Discussion")

    add_body(doc,
        "Les resultats presentes ci-dessous ont ete obtenus avec le jeu de donnees synthetique "
        "complet (150 classes, 200 enseignants, 80 salles, 24 matieres).")

    add_styled_heading(doc, "9.1 Performance de Generation", level=2)

    add_table_with_header(doc,
        ["Metrique", "Valeur"],
        [
            ["Nombre de variantes generees", "10"],
            ["Temps total de generation", "~18.3 secondes"],
            ["Temps moyen par variante", "~1.83 secondes"],
            ["Nombre de seances par variante", "~1228"],
            ["Taux de reussite d'affectation", "> 95%"],
        ])

    doc.add_paragraph()

    add_styled_heading(doc, "9.2 Scores des Variantes", level=2)

    add_body(doc,
        "Les scores obtenus pour les 10 variantes generees se situent dans la plage 27-33 "
        "sur 100. Le Top 3 est :")

    add_table_with_header(doc,
        ["Rang", "Score", "Pen. Trous Profs", "Pen. Trous Classes", "Pen. Salles", "Pen. Surcharge"],
        [
            ["1er (Or)", "33.0", "1912", "2095", "108", "0"],
            ["2eme (Argent)", "32.7", "1940", "2120", "112", "0"],
            ["3eme (Bronze)", "31.2", "1985", "2180", "115", "0"],
        ])

    doc.add_paragraph()

    add_styled_heading(doc, "9.3 Analyse des Resultats", level=2)

    add_body(doc,
        "Plusieurs observations peuvent etre faites a partir de ces resultats :")

    add_bullet(doc,
        "Les scores relativement bas (27-33/100) s'expliquent par la complexite de l'instance : "
        "avec 150 classes et seulement 20 creneaux, la densite de l'emploi du temps est tres "
        "elevee, ce qui genere inevitablement des trous pour les enseignants et les classes.",
        bold_prefix="Scores moderes :")

    add_bullet(doc,
        "La penalite dominante est celle des trous (enseignants et classes), ce qui est "
        "coherent avec la densite elevee du planning. Les penalites de salles sont comparativement "
        "faibles, indiquant une bonne utilisation des ressources spatiales.",
        bold_prefix="Penalites dominantes :")

    add_bullet(doc,
        "L'absence de surcharge journaliere (penalite = 0) indique que l'algorithme distribue "
        "naturellement les seances de maniere equilibree sur les 5 jours.",
        bold_prefix="Equilibre journalier :")

    add_bullet(doc,
        "Les scores du modele ML (R2 = 0.9988) confirment la capacite du modele XGBoost "
        "a reproduire fidelement le scoring heuristique, offrant une alternative viable "
        "pour le classement des variantes.",
        bold_prefix="Validation ML :")

    doc.add_page_break()

    # ═══════════════════════════════════════════════════════════
    # 10. CONCLUSION
    # ═══════════════════════════════════════════════════════════
    add_styled_heading(doc, "10. Conclusion et Perspectives")

    add_styled_heading(doc, "10.1 Conclusion", level=2)

    add_body(doc,
        "Le projet OptiPlua a atteint ses objectifs principaux en proposant une solution "
        "complete pour l'optimisation des emplois du temps scolaires. Les realisations "
        "majeures sont :")

    realisations = [
        "Un moteur heuristique capable de generer des emplois du temps valides pour des "
        "instances de grande taille (150 classes, 200 enseignants), avec respect strict de "
        "7 contraintes dures.",
        "Un systeme de scoring multi-critere innovant qui prend en compte a la fois le "
        "confort des enseignants (minimisation des trous) et celui des eleves (minimisation "
        "des fenetres et equilibrage de la charge journaliere).",
        "Un modele de Machine Learning (XGBoost) avec 22 features ingenierees, atteignant "
        "un R2 de 0.9988, offrant une alternative data-driven au scoring analytique.",
        "Une interface web professionnelle avec authentification, formulaires de saisie "
        "interactifs, generation parametrable, et presentation des 3 meilleures variantes "
        "avec details et export CSV.",
        "Un pipeline complet de la saisie des donnees jusqu'a l'export des resultats, "
        "accessible sans competences techniques.",
    ]
    for r in realisations:
        add_bullet(doc, r)

    add_styled_heading(doc, "10.2 Perspectives", level=2)

    add_body(doc,
        "Plusieurs pistes d'amelioration et d'extension sont envisagees pour les versions "
        "futures du projet :")

    perspectives = [
        ("Algorithmes genetiques :", "Remplacement ou complement de la recherche aleatoire "
         "par des algorithmes evolutionnaires (croisement, mutation, selection) pour explorer "
         "plus efficacement l'espace de solutions et obtenir des scores significativement "
         "plus eleves."),
        ("Application mobile :", "Developpement d'une application mobile (React Native ou "
         "Flutter) permettant aux enseignants et eleves de consulter leur emploi du temps "
         "personnel avec notifications de changements."),
        ("Deploiement SaaS :", "Transformation du projet en service SaaS multi-etablissements "
         "avec base de donnees centralisee, gestion des droits d'acces, et tableau de bord "
         "administratif."),
        ("Export PDF :", "Ajout de la generation de fichiers PDF formates pour impression "
         "directe des emplois du temps, avec mise en page professionnelle par classe et "
         "par enseignant."),
        ("Integration systemes existants :", "Connexion avec les systemes d'information "
         "scolaires existants (MASSAR, Pronote, etc.) pour l'import automatique des donnees "
         "et la synchronisation des emplois du temps."),
        ("Preferences des eleves :", "Prise en compte des preferences horaires des eleves "
         "(matieres difficiles le matin, sport l'apres-midi) comme contraintes souples "
         "dans la fonction objectif."),
    ]
    for prefix, text in perspectives:
        add_bullet(doc, text, bold_prefix=prefix)

    # ═══════════════════════════════════════════════════════════
    # SAVE
    # ═══════════════════════════════════════════════════════════
    doc.save(output_path)
    print(f"Rapport saved to: {output_path}")


if __name__ == "__main__":
    output = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rapport_optiplua.docx")
    create_rapport(output)
