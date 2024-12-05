from flask_restful import Api
from flask_pymongo import PyMongo
from flask_login import LoginManager
mongo = PyMongo()
api = Api()
login_manager = LoginManager()