from pymongo import MongoClient
from werkzeug.security import generate_password_hash

# Connexion à MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["attendance_db"]

# Ajout d'un utilisateur
db.users.insert_one({
    "username": "admin",
    "password": generate_password_hash("admin", method="pbkdf2:sha256"),  # Mot de passe sécurisé
    "role": "admin",  # Ou "employee"
    "employee_card_id": None  # Facultatif pour les administrateurs
},
{
    "username": "Ali ZAITER",
    "password": generate_password_hash("Azerty@123", method="pbkdf2:sha256"),  # Mot de passe sécurisé
    "role": "employee",  # Ou "employee"
    "employee_card_id": None  # Facultatif pour les administrateurs
})

print("Utilisateur ajouté avec succès")
