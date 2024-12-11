from flask import Blueprint, request, redirect, url_for, render_template, flash
from flask_login import login_user, logout_user, login_required, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
from extensions import mongo
from uuid import uuid4
import math
auth = Blueprint("auth", __name__)


class User(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data["_id"])
        self.username = user_data["username"]
        self.role = user_data["role"]
        self.employee_card_id = user_data.get("employee_card_id")

import logging

@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # Récupérer les données utilisateur
        user_data = mongo.db.users.find_one({"username": username})
        print("User data from DB:", user_data)

        if user_data:
            is_password_correct = check_password_hash(user_data["password"], password)
            print("Password correct:", is_password_correct)

            if is_password_correct:
                user = User(user_data)  # Crée un objet utilisateur
                login_user(user)
                return redirect(url_for("main.index"))  # Page après connexion
            else:
                print("Password does not match")

        else:
            print("User not found in database")

        flash("Invalid username or password")

    return render_template("login.html")




@auth.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))

@auth.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        try:
            username = request.form.get("username").strip()  # Normalisation
            password = request.form.get("password").strip()
            role = request.form.get("role")

            # Vérification de l'existence de l'utilisateur
            if mongo.db.users.find_one({"username": username}):
                flash("Username already exists", "warning")
                return redirect(url_for("auth.register"))

            # Validation du mot de passe
            if len(password) < 8 or not any(char.isdigit() for char in password) or not any(char.isalpha() for char in password):
                flash("Password must be at least 8 characters long and include both letters and numbers", "danger")
                return redirect(url_for("auth.register"))

            # Hachage du mot de passe
            hashed_password = generate_password_hash(password, method="pbkdf2:sha256")

            # Création du nouvel utilisateur
            user = {
                "username": username,
                "password": hashed_password,
                "role": role,
            }

            # Insertion dans la base de données
            mongo.db.users.insert_one(user)
            flash("User registered successfully", "success")
            return redirect(url_for("auth.login"))

        except Exception as e:
            flash(f"An error occurred: {e}", "danger")
            return redirect(url_for("auth.register"))

    return render_template("register.html")

