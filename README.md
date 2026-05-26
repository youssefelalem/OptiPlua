2. Importez les fichiers `data/enseignants_data.csv`, `data/salles_data.csv` et `data/classes_data.csv` présents dans le dossier `data/`.
<div align="center">

# OptiPlua

### AI-Powered School Timetable Optimization Platform

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Jupyter](https://img.shields.io/badge/Jupyter-Notebook-F37626?style=for-the-badge&logo=jupyter&logoColor=white)](https://jupyter.org)
[![Pandas](https://img.shields.io/badge/Pandas-Data%20Engine-150458?style=for-the-badge&logo=pandas&logoColor=white)](https://pandas.pydata.org)
[![XGBoost](https://img.shields.io/badge/XGBoost-ML%20Model-FF6600?style=for-the-badge&logo=xgboost&logoColor=white)](https://xgboost.readthedocs.io)
[![Status](https://img.shields.io/badge/Status-Phase%202%20%F0%9F%94%84-yellow?style=for-the-badge)]()

**OptiPlua** est une plateforme SaaS intelligente qui génère, optimise et évalue automatiquement les emplois du temps pour les établissements éducatifs marocains — Écoles, Centres de Soutien et Universités.

*Projet de recherche appliquée — Youssef EL ALEM & Douae MOUSSAOUI*

---

</div>

## Vue d'ensemble

OptiPlua combine un **moteur heuristique** de contraintes dures avec du **Machine Learning (XGBoost)** pour résoudre le problème NP-difficile de la planification scolaire. Le système tient compte des disponibilités des enseignants, des capacités des salles, des niveaux autorisés et des contraintes métier propres à chaque type d'établissement.

```
Données Synthétiques  →  Simulateur Heuristique  →  Scoring ML  →  Dashboard Streamlit
      (Phase 1)                (Phase 2)              (Phase 3)        (Phase 4)
```

---

## Fonctionnalités

| Module | Description | Statut |
|--------|-------------|--------|
| **Générateur de données** | Crée des profils réalistes d'enseignants, classes, salles et matières | ✅ Terminé |
| **Simulateur heuristique** | Assigne les cours en respectant 5 contraintes dures, semaine complète (20 créneaux) | ✅ Terminé |
| **Export CSV enrichi** | `raw_schedules_test.csv` avec 16 colonnes (Jour, Matière, Enseignant, Salle, etc.) | ✅ Terminé |
| **EDA & Analyse** | Exploration statistique des emplois du temps générés | 🔄 En cours |
| **Système de Scoring** | Pénalise les trous, récompense la flexibilité | ⏳ À venir |
| **Modèle XGBoost** | Prédit et optimise le score d'un planning | ⏳ À venir |
| **Dashboard Streamlit** | Interface interactive pour visualiser et ajuster les plannings | ⏳ À venir |

---

## Architecture du Projet

```
OptiPlua/
├── data/
│   ├── enseignants_data.csv      # 200 profils d'enseignants avec contraintes
│   ├── salles_data.csv           # 80 salles (Amphithéâtre, Labo, Générale)
│   ├── matieres_data.csv         # 24 matières par type d'établissement
│   ├── classes_data.csv          # 150 classes avec niveaux et effectifs
│   └── raw_schedules_test.csv    # Emploi du temps généré (output simulateur)
│
├── notebooks/
│   ├── data_generator.ipynb      # Génération des données synthétiques
│   └── simulation.ipynb          # Moteur heuristique v2.0
│
├── src/                          # [Phase 3] Scripts Python finaux
│   ├── constraints.py
│   ├── simulator.py
│   └── scoring.py
│
└── README.md
```

---

## Contraintes Implémentées

Le moteur de simulation respecte **5 contraintes dures** :

| ID | Contrainte | Description |
|----|-----------|-------------|
| C1 | Anti-collision Enseignant | Un prof ne peut pas avoir 2 cours simultanés |
| C2 | Anti-collision Salle | Une salle ne peut accueillir qu'une classe à la fois |
| C3 | Anti-collision Classe | Une classe ne peut pas avoir 2 cours en même temps |
| C4 | Indisponibilités | Les créneaux bloqués de chaque enseignant sont respectés |
| C5 | Quota horaire | `Heures_Max_Par_Semaine` de chaque enseignant est respecté |

---

## Stack Technique

- **Python 3.10+** — Langage principal
- **Pandas** — Manipulation et analyse des données
- **XGBoost** — Modèle de scoring ML (Phase 3)
- **Streamlit** — Interface utilisateur (Phase 4)
- **Jupyter Notebook** — Développement itératif

---

## Installation

```bash
# 1. Cloner le dépôt
git clone https://github.com/youssefelalem/OptiPlua.git
cd OptiPlua

# 2. Créer et activer l'environnement virtuel
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux / macOS

# 3. Installer les dépendances
pip install pandas jupyter xgboost streamlit
```

### Lancer la simulation

```bash
# Ouvrir Jupyter
jupyter notebook

# Exécuter dans cet ordre :
# 1. notebooks/data_generator.ipynb  → génère les 4 fichiers CSV
# 2. notebooks/simulation.ipynb      → génère raw_schedules_test.csv
```

---

## Roadmap

```
[Phase 1]  Cadrage & Génération des données         ✅  Terminée
[Phase 2]  Simulateur heuristique & EDA             🔄  En cours
[Phase 3]  Dataset massif, Scoring & XGBoost        ⏳  Planifiée
[Phase 4]  Dashboard Streamlit & API                ⏳  Planifiée
[Phase 5]  Export PDF & Déploiement SaaS            ⏳  Planifiée
```

---

## Auteurs

| Nom | Rôle |
|-----|------|
| **Youssef EL ALEM** | Data Engineering, Simulation, ML |
| **Douae MOUSSAOUI** | EDA, Scoring, Visualisation |

---

<div align="center">

*OptiPlua — Planification Intelligente pour l'Éducation*

</div>