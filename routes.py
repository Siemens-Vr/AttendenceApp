# Flask
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash

# Flask-Login
from flask_login import login_required, current_user

# UUID pour générer des identifiants uniques
from uuid import uuid4

# MongoDB ObjectId pour gérer les identifiants des documents
from bson.objectid import ObjectId

# Gestion des dates et heures
from datetime import datetime, timedelta

# Pillow pour la manipulation des images
from PIL import Image
from base64 import b64decode
# Manipulation des fichiers en mémoire et conversion en Base64
import io, os
import base64
from datetime import datetime
from bson.objectid import ObjectId
# Extensions Flask (MongoDB doit être initialisé dans un fichier `extensions.py`)
from extensions import mongo



main = Blueprint("main", __name__)

def process_image(file):
    """
    Traite une image pour la convertir en Base64 avec un format défini.
    """
    try:
        image = Image.open(file)
        # Convertir l'image au format RGB si nécessaire
        if image.mode != "RGB":
            image = image.convert("RGB")
        # Réduire la taille si nécessaire (facultatif)
        max_size = (200, 200)  # Exemple de taille maximum
        image.thumbnail(max_size, Image.ANTIALIAS)

        # Sauvegarder l'image en mémoire
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode("utf-8")
    except Exception as e:
        print(f"Erreur lors du traitement de l'image : {e}")
        raise





def configure_routes(blueprint, mongo):
    """
    Configure les routes pour le Blueprint.
    """
    # Récupération des collections MongoDB
    students_collection = mongo.db.students
    attendance_collection = mongo.db.attendance
    tasks_collection = mongo.db.tasks
    @main.route("/")
    @login_required
    def index():
        """
        Affiche la page principale avec les étudiants.
        - Les administrateurs voient tous les étudiants.
        - Les employés ne voient que les étudiants qu'ils ont ajoutés.
        """
        if current_user.role == "admin":
            # L'administrateur voit tous les étudiants
            students = list(students_collection.find())
        else:
            # L'employé ne voit que les étudiants qu'il a ajoutés
            students = list(students_collection.find({"employee_card_id": current_user.id}))



        for student in students:
            print( student)
            student["_id"] = str(student["_id"])  # Convertir ObjectId en string pour Jinja
            attendance = student.get("attendance", {})
            if attendance.get("start_time") and not attendance.get("pause_time"):
                student["status"] = "Active"
            elif attendance.get("pause_time"):
                student["status"] = "Paused"
            else:
                student["status"] = "Inactive"

            for task in student.get("tasks", []):
                if "_id" in task:
                    task["_id"] = str(task["_id"])

        return render_template("index.html", students=students)





    @main.route("/add_student", methods=["POST"])
    def add_student():
        name = request.form.get("name")
        role = request.form.get("role")
        image = request.files.get("image")

        if not name or not role:
            return jsonify({"error": "Name and role are required"}), 400

        if not image:
            return jsonify({"error": "Image is required"}), 400

        try:
            # Traitement de l'image
            img = Image.open(image)
            img.thumbnail((150, 150), Image.LANCZOS)
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            encoded_image = base64.b64encode(buffer.getvalue()).decode("utf-8")

            # Insertion dans la base de données
            student_data = {
                "name": name,
                "role": role,
                "image": encoded_image,
                "tasks": [],
                "attendance": {},
                "employee_card_id": current_user.id  # Utilise l'ID de l'utilisateur connecté
            }

            students_collection.insert_one(student_data)
            return redirect(url_for("main.index"))
        except Exception as e:
            return jsonify({"error": f"Failed to add student: {str(e)}"}), 500



        
    @main.route("/remove_student/<student_id>", methods=["POST"])
    @login_required
    def remove_student(student_id):
        """
        Supprime un étudiant par son ID.
        """
        student = students_collection.find_one({"_id": ObjectId(student_id)})
        if not student:
            flash("Student not found.")
            return redirect(url_for("main.index"))

        if current_user.role != "admin" and student.get("added_by") != current_user.employee_card_id:
            flash("You are not authorized to remove this student.")
            return redirect(url_for("main.index"))

        try:
            students_collection.delete_one({"_id": ObjectId(student_id)})
            flash("Student removed successfully.")
        except Exception as e:
            flash(f"Failed to remove student: {str(e)}")

        return redirect(url_for("main.index"))






    @main.route("/add_task/<student_id>", methods=["POST"])
    def add_task(student_id):
        task_description = request.form.get("task_description")
        if not task_description:
            return jsonify({"error": "Task description is required"}), 400

        current_date = datetime.now()
        task = {
            "_id": str(uuid4()),  # ID unique pour chaque tâche
            "description": task_description,
            "date": current_date,  # Date associée à l'enregistrement d'attendance
            "start_time": None,
            "end_time": None,
            "duration": 0  # Initialisé à 0
        }

        students_collection.update_one(
            {"_id": ObjectId(student_id)},
            {"$push": {"tasks": task}}
        )

        # Assurez-vous d'ajouter une relation avec `attendance` ici si nécessaire
        attendance_collection.update_one(
            {"name": students_collection.find_one({"_id": ObjectId(student_id)})["name"], "date": current_date},
            {"$push": {"tasks": task}},
            upsert=True
        )

        return redirect(url_for("main.index"))


    @main.route('/remove_task/<string:student_id>/<string:task_id>', methods=['POST'])
    def remove_task(student_id, task_id):
        """
        Supprime une tâche d'un étudiant spécifique par son ID.
        """
        try:
            # Trouver l'étudiant dans la base de données
            student = students_collection.find_one({"_id": ObjectId(student_id)})
            
            if not student:
                return jsonify({"error": "Student not found"}), 404

            # Récupérer la liste des tâches ou définir une liste vide si elle n'existe pas
            tasks = student.get('tasks', [])

            # Filtrer les tâches pour exclure celle avec l'ID donné
            updated_tasks = [task for task in tasks if '_id' in task and str(task['_id']) != task_id]

            # Mettre à jour les tâches dans la base de données
            students_collection.update_one(
                {"_id": ObjectId(student_id)},
                {"$set": {"tasks": updated_tasks}}
            )
            return redirect(url_for('main.index'))

        except Exception as e:
            return jsonify({"error": f"An error occurred: {str(e)}"}), 500
        




    @main.route("/view_tasks/<student_id>/<date>")
    @login_required
    def view_tasks(student_id, date):
        # Vérifiez si l'étudiant existe
        student = students_collection.find_one({"_id": ObjectId(student_id)})
        if not student:
            return "Student not found", 404

        # Vérifiez si l'utilisateur a accès
        if current_user.role != "admin" and student.get("employee_card_id") != str(current_user.id):
            return "Unauthorized access", 403

        # Obtenez les tâches pour cette date
        tasks = list(tasks_collection.find({
            "student_id": student_id,
            "date": datetime.strptime(date, "%Y-%m-%d")
        }))

        return render_template("tasks.html", student=student, date=date, tasks=tasks)




    @main.route("/toggle_day/<student_id>", methods=["POST"])
    def toggle_day(student_id):
        student = students_collection.find_one({"_id": ObjectId(student_id)})
        if not student:
            return jsonify({"error": "Student not found"}), 404

        attendance = student.get("attendance", {})
        current_time = datetime.now()

        if not attendance.get("start_time"):
            # Start a new day
            attendance["start_time"] = current_time
            attendance["pause_time"] = None

            # Create a new record in `attendance_collection`
            attendance_record = {
                "name": student["name"],
                "date": datetime.combine(current_time.date(), datetime.min.time()),  # Date only, without time
                "start_time": current_time,  # Include start time for potential debugging
                "end_time": None,  # Not finished yet
                "hours_worked": 0.0,  # Initially 0
                "student_signature": "Unsigned",
                "professor_signature": "Unsigned",
                "tasks": []  # Initialize an empty task list
            }
            attendance_collection.insert_one(attendance_record)
        else:
            # Stop the day and calculate hours worked
            start_time = attendance.get("start_time")
            total_hours = attendance.get("total_hours", 0)

            if start_time:
                hours_worked = (current_time - start_time).total_seconds() / 3600
                total_hours += hours_worked

                # Update the existing record in `attendance_collection`
                attendance_collection.update_one(
                    {
                        "name": student["name"],
                        "date": datetime.combine(current_time.date(), datetime.min.time())  # Match by date only
                    },
                    {
                        "$set": {
                            "end_time": current_time,
                            "hours_worked": total_hours
                        }
                    }
                )

            attendance["total_hours"] = total_hours
            attendance["start_time"] = None  # Reset the start time

        # Update the student's attendance in `students_collection`
        students_collection.update_one({"_id": ObjectId(student_id)}, {"$set": {"attendance": attendance}})
        return redirect(url_for("main.index"))


    @main.route("/delete_tasks/<student_id>", methods=["POST"])
    @login_required
    def delete_tasks(student_id):
        student = students_collection.find_one({"_id": ObjectId(student_id)})
        if not student:
            return "Student not found", 404

        # Vérifiez les autorisations
        if current_user.role != "admin" and student.get("employee_card_id") != str(current_user.id):
            return "Unauthorized access", 403

        # Récupérez les identifiants des tâches à supprimer
        task_ids = request.form.getlist("task_ids")
        if not task_ids:
            flash("No tasks selected for deletion", "warning")
            return redirect(url_for("main.student_weekly_report", student_id=student_id))

        # Supprimez les tâches sélectionnées
        for task_id in task_ids:
            tasks_collection.delete_one({"_id": ObjectId(task_id)})

        flash("Selected tasks deleted successfully", "success")
        return redirect(url_for("main.student_weekly_report", student_id=student_id))


    @main.route("/toggle_pause/<student_id>", methods=["POST"])
    def toggle_pause(student_id):
        """
        Met en pause ou reprend le travail pour un étudiant.
        """
        student = students_collection.find_one({"_id": ObjectId(student_id)})
        if not student:
            return jsonify({"error": "Student not found"}), 404

        attendance = student.get("attendance", {})
        current_time = datetime.now()

        if not attendance.get("pause_time"):
            # Mettre en pause
            attendance["pause_time"] = current_time
        else:
            # Reprendre le travail
            pause_start = attendance.pop("pause_time")
            total_paused = attendance.get("total_paused", 0)

            if pause_start:
                total_paused += (current_time - pause_start).total_seconds() / 3600

            attendance["total_paused"] = total_paused

        # Mettre à jour la base de données
        students_collection.update_one({"_id": ObjectId(student_id)}, {"$set": {"attendance": attendance}})
        return redirect(url_for("main.index"))


    @main.route("/toggle_attendance/<student_id>", methods=["POST"])
    def toggle_attendance(student_id):
        """
        Gère le début/fin de la journée de présence.
        """
        student = students_collection.find_one({"_id": ObjectId(student_id)})
        if not student:
            return "Student not found", 404

        attendance = student.get("attendance", {})
        if not attendance.get("start_time"):
            # Start attendance
            attendance["start_time"] = datetime.now()
        else:
            # End attendance
            start_time = attendance.pop("start_time", None)
            total_hours = attendance.get("total_hours", 0)
            if start_time:
                total_hours += (datetime.now() - start_time).total_seconds() / 3600
            attendance["total_hours"] = total_hours

        students_collection.update_one(
            {"_id": ObjectId(student_id)},
            {"$set": {"attendance": attendance}}
        )
        return redirect(url_for("main.index"))

    @main.route("/student_weekly_report/<student_id>")
    @login_required
    def student_weekly_report(student_id):
        student = students_collection.find_one({"_id": ObjectId(student_id)})
        if not student:
            return "Student not found", 404

        # Vérifiez les autorisations
        if current_user.role != "admin" and student.get("employee_card_id") != str(current_user.id):
            return "Unauthorized access", 403

        # Récupérez les enregistrements hebdomadaires
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)

        # Pipeline d'agrégation pour regrouper par jour, mois et année
        records = list(
            attendance_collection.aggregate([
                {"$match": {"name": student["name"], "date": {"$gte": start_date, "$lte": end_date}}},
                {
                    "$group": {
                        "_id": {
                            "year": {"$year": "$date"},
                            "month": {"$month": "$date"},
                            "day": {"$dayOfMonth": "$date"}
                        },
                        "total_hours": {"$sum": "$hours_worked"},
                        "tasks": {"$push": "$tasks"},
                        "student_signature": {"$first": "$student_signature"},
                        "professor_signature": {"$first": "$professor_signature"}
                    }
                },
                {"$sort": {"_id.year": 1, "_id.month": 1, "_id.day": 1}}
            ])
        )

        # Format des données pour le frontend
        formatted_records = [
            {
                "date": datetime(record["_id"]["year"], record["_id"]["month"], record["_id"]["day"]),
                "hours_worked": record["total_hours"],
                "tasks": [task for tasks_list in record["tasks"] for task in tasks_list],  # Aplatir les listes de tâches
                "student_signature": record["student_signature"],
                "professor_signature": record["professor_signature"]
            }
            for record in records
        ]

        return render_template("student_weekly_report.html", student=student, records=formatted_records)







    @main.route("/daily_tasks/<string:student_id>/<string:date>")
    @login_required
    def daily_tasks(student_id, date):
        """
        Affiche les tâches spécifiques à une date donnée pour un étudiant.
        """
        student = students_collection.find_one({"_id": ObjectId(student_id)})

        if not student:
            return "Student not found", 404

        attendance_record = attendance_collection.find_one({
            "student_id": student_id,
            "date": datetime.strptime(date, "%Y-%m-%d")
        })

        if not attendance_record:
            return "Attendance record not found for this date", 404

        tasks = attendance_record.get("tasks", [])
        return render_template("daily_tasks.html", tasks=tasks, student=student, date=date)


    @main.route("/sign/<role>/<student_id>/<date>", methods=["POST"])
    @login_required
    def sign(role, student_id, date):
        """
        Enregistre la signature pour un étudiant ou un professeur dans la base de données sans sauvegarder de fichier.
        """
        signature = request.form["signature"]

        # Vérifiez si l'étudiant existe
        student = students_collection.find_one({"_id": ObjectId(student_id)})
        if not student:
            return "Student not found", 404

        # Vérifiez les autorisations
        if current_user.role != "admin" and student.get("employee_card_id") != str(current_user.id):
            return "Unauthorized access", 403

        # Nettoyez la date pour ne garder que la partie date
        date_only = date.split(" ")[0]  # "2024-12-09 00:00:00" devient "2024-12-09"

        # Ajoutez la signature dans la base de données
        role_key = f"{role}_signature"
        result = attendance_collection.update_one(
            {"name": student["name"], "date": datetime.strptime(date_only, "%Y-%m-%d")},
            {"$set": {role_key: "Signed"}},  # Exemple : Enregistrez "Signed"
            upsert=True
        )

        # Log pour vérification
        print(f"Signature enregistrée : {role_key} -> 'Signed', Result: {result.modified_count}")

        flash(f"{role.capitalize()} signature added successfully.")
        return redirect(url_for("main.student_weekly_report", student_id=student_id))



    @main.route("/save_signature", methods=["POST"])
    def save_signature():
        """
        Sauvegarde la signature pour un étudiant ou un professeur.
        """
        data = request.get_json()
        name = data.get("name")
        date = data.get("date")
        role = data.get("role")  # 'student' ou 'professor'
        signature = data.get("signature")  # Signature encodée en base64

        if not name or not date or not role or not signature:
            return jsonify({"error": "Invalid data"}), 400

        # Met à jour ou ajoute la signature dans la base de données
        attendance_collection.update_one(
            {"_id.name": name, "_id.date": date},
            {"$set": {f"{role}_signature": signature}},
            upsert=True
        )

        return jsonify({"success": True, "role": role})
    @main.route("/reset_hours", methods=["POST"])
    def reset_hours():
        """
        Réinitialise l'affichage des heures sur la page principale tout en conservant
        les heures dans la base de données pour le rapport hebdomadaire.
        """
        students = students_collection.find()
        for student in students:
            attendance = student.get("attendance", {})
            total_hours = attendance.get("total_hours", 0)

            # Enregistre les heures travaillées dans le rapport
            attendance_record = {
                "name": student["name"],
                "date": datetime.combine(datetime.now().date(), datetime.min.time()),  # Conversion en datetime
                "hours_worked": total_hours,
            }
            attendance_collection.insert_one(attendance_record)

            # Réinitialise le compteur d'heures affiché
            attendance["total_hours"] = 0
            students_collection.update_one(
                {"_id": student["_id"]},
                {"$set": {"attendance": attendance}}
            )

        return redirect(url_for("main.index"))
    
    @main.route("/start_task/<string:student_id>/<string:task_id>", methods=["POST"])
    def start_task(student_id, task_id):
        """
        Démarre une tâche spécifique pour un étudiant.
        """
        current_time = datetime.now()
        students_collection.update_one(
            {"_id": ObjectId(student_id), "tasks._id": task_id},
            {"$set": {"tasks.$.start_time": current_time, "tasks.$.end_time": None}}
        )
        return redirect(url_for("main.index"))
    
    @main.route("/end_task/<string:student_id>/<string:task_id>", methods=["POST"])
    def end_task(student_id, task_id):
        """
        Termine une tâche spécifique pour un étudiant et calcule la durée.
        """
        current_time = datetime.now()
        student = students_collection.find_one({"_id": ObjectId(student_id)})
        
        if not student:
            return "Student not found", 404
        
        task = next((t for t in student["tasks"] if t["_id"] == task_id), None)
        if not task or not task.get("start_time"):
            return "Task not started or does not exist", 400

        start_time = task["start_time"]
        duration = (current_time - start_time).total_seconds()
        
        students_collection.update_one(
            {"_id": ObjectId(student_id), "tasks._id": task_id},
            {"$set": {"tasks.$.end_time": current_time, "tasks.$.duration": duration}}
        )
        return redirect(url_for("main.index"))

