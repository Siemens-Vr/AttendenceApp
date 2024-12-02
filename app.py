import os
import json
import ipaddress
from flask import Flask, request, abort
from flask_pymongo import PyMongo
from routes import main, configure_routes  # Importation du Blueprint et des routes


def load_allowed_ips(file_path=None):
    """
    Charge la liste des adresses IP autorisées depuis un fichier JSON.
    """
    if file_path is None:
        # Chemin absolu basé sur l'emplacement du script
        file_path = os.path.join(os.path.dirname(__file__), "allowed_ips.json")
    
    try:
        with open(file_path, "r") as file:
            data = json.load(file)
            return data.get("allowed_ips", [])
    except Exception as e:
        print(f"Erreur lors du chargement des IP autorisées : {e}")
        return []



def is_ip_allowed():
    """
    Vérifie si l'adresse IP du client est autorisée.
    """
    allowed_ips = load_allowed_ips()

    # Récupérer l'adresse IP du client
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    print(f"Requête reçue de l'IP : {client_ip}")

    for allowed_ip in allowed_ips:
        try:
            if '/' in allowed_ip:  # Plage CIDR
                if ipaddress.ip_address(client_ip) in ipaddress.ip_network(allowed_ip, strict=False):
                    return True
            else:  # IP unique
                if client_ip == allowed_ip:
                    return True
        except ValueError as e:
            print(f"Erreur lors de la vérification de l'IP {allowed_ip} : {e}")
            continue

    return False



def create_app():
    """
    Crée et configure l'application Flask.
    """
    app = Flask(__name__)

    # Charger la configuration depuis un fichier JSON (optionnel)
    config_file = "config.json"
    if os.path.exists(config_file):
        with open(config_file, "r") as file:
            config_data = json.load(file)
            app.config.update(config_data)

    # Configuration MongoDB
    app.config["MONGO_URI"] = "mongodb://localhost:27017/attendance_db"
    mongo = PyMongo(app)

    # Configurez les routes avant d'enregistrer le Blueprint
    configure_routes(main, mongo)

    # Enregistrement du Blueprint
    app.register_blueprint(main, url_prefix="/")

    @app.before_request
    def restrict_ip():
        """
        Bloque les requêtes provenant d'adresses IP non autorisées.
        """
        if not is_ip_allowed():
            abort(403)

    return app


if __name__ == "__main__":
    print(f"Répertoire actuel : {os.getcwd()}")
    app = create_app()
    # Exécutez l'application Flask, écoute sur toutes les interfaces réseau
    app.run(debug=True, host="0.0.0.0", port=5000)
