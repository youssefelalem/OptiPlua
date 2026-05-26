<div align="center">

# 🚀 OptiPlua
### Plateforme SaaS d'Optimisation des Emplois du Temps par l'IA
### AI-Powered School Timetable Optimization Platform

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-UI-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io)
[![Pandas](https://img.shields.io/badge/Pandas-Data%20Engine-150458?style=for-the-badge&logo=pandas&logoColor=white)](https://pandas.pydata.org)
[![XGBoost](https://img.shields.io/badge/XGBoost-ML%20Scoring-FF6600?style=for-the-badge&logo=xgboost&logoColor=white)](https://xgboost.readthedocs.io)

---

**OptiPlua** est une plateforme SaaS intelligente conçue pour générer, optimiser et évaluer automatiquement les emplois du temps au sein des établissements scolaires marocains (Écoles, Centres de Soutien, et Universités). 

Le système combine un **moteur heuristique performant** avec du **Machine Learning (XGBoost)** pour résoudre le problème complexe d'attribution des cours en respectant les contraintes d'enseignants, de salles, de classes et de quotas horaires.

*Projet de recherche appliquée — Youssef EL ALEM & Douae MOUSSAOUI*

---

</div>

## 📌 Sommaire
1. [Vue d'ensemble](#-vue-densemble)
2. [Fonctionnalités Clés](#-fonctionnalités-clés)
3. [Architecture du Projet](#-architecture-du-projet)
4. [Moteur de Contraintes](#-moteur-de-contraintes-dures)
5. [Système d'Évaluation & Scoring](#-système-dévaluation--scoring)
6. [Installation & Démarrage](#-installation--démarrage)

---

## 🔍 Vue d'ensemble

L'ordonnancement des cours est un problème NP-difficile. **OptiPlua** le résout efficacement à travers un workflow structuré :
```text
Générateur de Données ──> Simulateur Heuristique ──> Moteur de Scoring ──> Dashboard Streamlit
```

---

## ✨ Fonctionnalités Clés

* **Génération Automatique :** Production instantanée d'emplois du temps optimisés et 100% exempts de collisions.
* **Dashboard Interactif :** Interface graphique intuitive développée sous **Streamlit** permettant l'importation de fichiers CSV et la visualisation immédiate des résultats.
* **Gestion des Salles Spécialisées :** Prise en charge automatique des laboratoires (Sciences, Informatique) et respect strict des capacités des salles face aux effectifs des classes.
* **Optimisation du Confort (Scoring) :** Réduction des heures creuses (gaps) des professeurs et optimisation du taux d'occupation des salles de classe.

---

## 📂 Architecture du Projet

```text
OptiPlua/
├── app.py                     # Dashboard interactif Streamlit (Interface Utilisateur)
├── simulator.py               # Moteur heuristique d'affectation et de planification
├── constraints.py             # Logique de vérification des contraintes & Calcul du score de qualité
├── enseignants_data.csv       # Profils d'enseignants avec matières, niveaux et indisponibilités
├── salles_data.csv            # Liste des salles de classe (Capacité, Type)
├── classes_data.csv           # Liste des classes avec effectifs et niveaux
├── matieres_data.csv          # Référentiel des matières par type d'établissement
├── data_generator.ipynb       # Notebook de génération de données synthétiques réalistes
└── simulation.ipynb           # Notebook d'exploration et de test du simulateur v2.0
```

---

## ⚙️ Moteur de Contraintes Dures

Le moteur d'affectation garantit qu'aucun emploi du temps généré ne viole les **5 contraintes dures (Hard Constraints)** suivantes :

| Code | Contrainte | Description |
| :---: | :--- | :--- |
| **C1** | **Anti-collision Enseignant** | Un enseignant ne peut pas dispenser deux cours différents simultanément. |
| **C2** | **Anti-collision Salle** | Une salle ne peut pas accueillir deux classes différentes en même temps. |
| **C3** | **Anti-collision Classe** | Une classe ne peut pas avoir deux matières ou cours prévus en même temps. |
| **C4** | **Disponibilité Enseignant** | Respect strict des créneaux horaires d'indisponibilité de chaque professeur. |
| **C5** | **Quota Horaire Hebdomadaire** | Pas de dépassement du volume horaire hebdomadaire autorisé par enseignant. |

---

## 🏆 Système d'Évaluation & Scoring

Afin de départager les plannings générés, OptiPlua évalue la qualité de chaque proposition sur une échelle de **0 à 100** via les critères suivants :

1. **Heures Creuses des Enseignants (-2 pts / heure vide) :** Pénalise fortement les temps d'attente inutiles des professeurs entre deux cours sur une même journée.
2. **Sous-utilisation des Salles (-1.5 pts / séance) :** Pénalise l'attribution de petites classes dans de grandes salles de cours (taux d'occupation < 40%).

---

## 🛠️ Installation & Démarrage

### 1. Prérequis
Assurez-vous que **Python 3.10+** est installé sur votre système.

### 2. Installation des dépendances
Ouvrez votre terminal dans le répertoire du projet et installez les packages nécessaires :
```bash
pip install pandas streamlit xgboost jupyter
```

### 3. Exécution du Dashboard Streamlit
Démarrez l'application web interactive locale :
```bash
streamlit run app.py
```
Une page web s'ouvrira automatiquement à l'adresse : `http://localhost:8501`.

### 4. Utilisation rapide
1. Rendez-vous sur le panneau latéral à gauche.
2. Importez les fichiers `enseignants_data.csv`, `salles_data.csv` et `classes_data.csv` présents à la racine du projet.
3. Ajustez le curseur pour le nombre de candidats à tester.
4. Cliquez sur **🚀 Générer les Meilleurs Emplois du Temps** pour découvrir les 3 meilleures options triées par score de qualité.

---

<div align="center">

*OptiPlua — Conçu avec passion pour l'excellence de la gestion éducative. 🇲🇦*

</div>