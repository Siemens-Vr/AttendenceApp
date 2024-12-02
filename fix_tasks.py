from pymongo import MongoClient
from uuid import uuid4

# Connexion à MongoDB
# Remplacez les paramètres ci-dessous par les vôtres
MONGO_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "nom_de_votre_base_de_donnees"
STUDENTS_COLLECTION_NAME = "students"

def connect_to_database():
    """
    Établit une connexion à MongoDB.
    """
    client = MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]
    return db

def verify_and_fix_tasks():
    """
    Vérifie les données des étudiants et corrige les tâches manquantes ou mal formatées.
    """
    # Connexion à la base de données et à la collection
    db = connect_to_database()
    students_collection = db[STUDENTS_COLLECTION_NAME]

    # Parcours des étudiants
    print("Vérification et correction des tâches...")
    for student in students_collection.find():
        updated_tasks = []
        corrections_made = False  # Indicateur pour savoir si des corrections ont été faites

        for task in student.get('tasks', []):
            # Vérification si le champ `_id` est manquant
            if '_id' not in task:
                print(f"Ajout de '_id' manquant pour une tâche de l'étudiant {student.get('name', 'Inconnu')}")
                task['_id'] = str(uuid4())  # Génération d'un nouvel identifiant unique
                corrections_made = True
            updated_tasks.append(task)

        # Mise à jour des données dans la base si des corrections ont été faites
        if corrections_made:
            students_collection.update_one(
                {"_id": student["_id"]},
                {"$set": {"tasks": updated_tasks}}
            )
            print(f"Les tâches de l'étudiant {student.get('name', 'Inconnu')} ont été corrigées.")

    print("Vérification et correction terminées.")

if __name__ == "__main__":
    try:
        verify_and_fix_tasks()
    except Exception as e:
        print(f"Une erreur est survenue : {e}")
