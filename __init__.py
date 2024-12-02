from flask import Flask
from flask_restful import Api
from extensions import mongo, api
from routes import configure_routes
from api_routes import configure_api_routes

def create_app():
    """
    Create and configure the Flask application.
    """
    app = Flask(__name__)
    
    # Configuration de MongoDB
    app.config["MONGO_URI"] = "mongodb://localhost:27017/attendance_db"
    
    # Initialiser les extensions
    mongo.init_app(app)
    api.init_app(app)
    
    # Configurer les routes principales (pages HTML)
    configure_routes(app, mongo)
    
    # Configurer les routes API (RESTful)
    configure_api_routes(api)
    
    return app
