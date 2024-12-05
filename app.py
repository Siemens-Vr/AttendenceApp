import os
import json
import ipaddress
from flask import Flask, request, abort, Blueprint
from flask_pymongo import PyMongo
from flask_login import LoginManager
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
from routes import main as main_blueprint, configure_routes
from auth import auth as auth_blueprint, User  # Assurez-vous que `auth.py` existe
from extensions import mongo


# Initialisation des extensions globales
login_manager = LoginManager()





@login_manager.user_loader
def load_user(user_id):
    if not mongo.cx:  # Vérifie si `mongo` est connecté
        return None
    user_data = mongo.db.users.find_one({"_id": ObjectId(user_id)})
    if user_data:
        return User(user_data)
    return None



def load_allowed_ips(file_path=None):
    if file_path is None:
        file_path = os.path.join(os.path.dirname(__file__), "allowed_ips.json")
    try:
        with open(file_path, "r") as file:
            data = json.load(file)
            return data.get("allowed_ips", [])
    except Exception as e:
        print(f"Erreur lors du chargement des IP autorisées : {e}")
        return []


def is_ip_allowed():
    allowed_ips = load_allowed_ips()
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    print(f"Requête reçue de l'IP : {client_ip}")
    for allowed_ip in allowed_ips:
        try:
            if '/' in allowed_ip:
                if ipaddress.ip_address(client_ip) in ipaddress.ip_network(allowed_ip, strict=False):
                    return True
            else:
                if client_ip == allowed_ip:
                    return True
        except ValueError as e:
            print(f"Erreur lors de la vérification de l'IP {allowed_ip} : {e}")
            continue
    return False


def create_app():
    app = Flask(__name__)
    app.config["MONGO_URI"] = "mongodb://localhost:27017/attendance_db"
    app.secret_key = "4b3403665fea6d2a8a392c1c0732e8a1"
    
    # Initialisation des extensions
    mongo.init_app(app)
    login_manager.init_app(app)

    # Configuration Flask-Login
    login_manager.login_view = "auth.login"

    # Charger la configuration optionnelle
    config_file = "config.json"
    if os.path.exists(config_file):
        with open(config_file, "r") as file:
            config_data = json.load(file)
            app.config.update(config_data)

    @app.before_request
    def restrict_ip():
        if not is_ip_allowed():
            abort(403)

    # Configurez les routes
    configure_routes(main_blueprint, mongo)

    # Enregistrez les blueprints
    app.register_blueprint(auth_blueprint, url_prefix="/auth")
    app.register_blueprint(main_blueprint)

    return app


if __name__ == "__main__":

    app = create_app()
    app.run(debug=True, host="0.0.0.0", port=5000)
