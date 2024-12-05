from pymongo import MongoClient

# Connexion à la base de données MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["attendance_db"]

# Suppression des comptes existants
result = db.users.delete_many({})  # Supprime tous les documents dans la collection 'users'

print(f"{result.deleted_count} comptes supprimés.")

# (Facultatif) Supprimez également les étudiants, si nécessaire :
delete_students = input("Voulez-vous supprimer également tous les étudiants ? (oui/non): ")
if delete_students.lower() == "oui":
    result_students = db.students.delete_many({})
    print(f"{result_students.deleted_count} étudiants supprimés.")
