import os
import shutil

# Dossiers à créer
folders = ["data", "notebooks", "src", "models"]

# Fichiers à déplacer
csv_files = [
    "classes_data.csv",
    "enseignants_data.csv",
    "final_schedules_ml.csv",
    "matieres_data.csv",
    "raw_schedules_test.csv",
    "salles_data.csv",
]
notebook_files = ["data_generator.ipynb", "simulation.ipynb"]

root = os.path.abspath(os.path.dirname(__file__))

# Créer les dossiers s'ils n'existent pas
for folder in folders:
    folder_path = os.path.join(root, folder)
    os.makedirs(folder_path, exist_ok=True)
    print(f"Created or exists: {folder_path}")

# Déplacer les fichiers CSV vers data/
for filename in csv_files:
    src = os.path.join(root, filename)
    dst = os.path.join(root, "data", filename)
    if os.path.exists(src) and os.path.isfile(src):
        shutil.move(src, dst)
        print(f"Moved CSV: {filename} -> data/")
    else:
        print(f"Skipped missing CSV: {filename}")

# Déplacer les notebooks vers notebooks/
for filename in notebook_files:
    src = os.path.join(root, filename)
    dst = os.path.join(root, "notebooks", filename)
    if os.path.exists(src) and os.path.isfile(src):
        shutil.move(src, dst)
        print(f"Moved notebook: {filename} -> notebooks/")
    else:
        print(f"Skipped missing notebook: {filename}")

print("Project structure updated successfully.")
