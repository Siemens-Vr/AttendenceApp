from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from uuid import uuid4
from bson.objectid import ObjectId
from datetime import datetime, timedelta
from PIL import Image
import io
import base64

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

    @blueprint.route("/")
    def index():
        """
        Affiche la page principale avec les étudiants et leurs tâches.
        """
        students = list(students_collection.find())
        for student in students:
            student["_id"] = str(student["_id"])  # Convertir ObjectId en string pour Jinja
            attendance = student.get("attendance", {})
            if attendance.get("start_time") and not attendance.get("pause_time"):
                student["status"] = "Active"  # Travaillant actuellement
            elif attendance.get("pause_time"):
                student["status"] = "Paused"  # En pause
            else:
                student["status"] = "Inactive"  # Journée non démarrée ou terminée
        return render_template("index.html", students=students)


    @main.route("/add_student", methods=["POST"])
    def add_student():
        """
        Ajoute un étudiant avec les informations fournies.
        """
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
            img.thumbnail((150, 150), Image.LANCZOS)  # Utilisation de LANCZOS au lieu de ANTIALIAS
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            encoded_image = base64.b64encode(buffer.getvalue()).decode("utf-8")

            # Insertion dans la base de données
            students_collection.insert_one({
                "name": name,
                "role": role,
                "image": encoded_image,
                "tasks": [],
                "attendance": {}
            })
            return redirect(url_for("main.index"))
        except Exception as e:
            return jsonify({"error": f"Failed to add student: {str(e)}"}), 500
        
    @main.route("/remove_student/<student_id>", methods=["POST"])
    def remove_student(student_id):
        """
        Supprime un étudiant par son ID.
        """
        try:
            students_collection.delete_one({"_id": ObjectId(student_id)})
            return redirect(url_for("main.index"))
        except Exception as e:
            return jsonify({"error": f"Failed to remove student: {str(e)}"}), 500




    @main.route("/add_task/<student_id>", methods=["POST"])
    def add_task(student_id):
        """
        Ajoute une tâche à un étudiant spécifique.
        """
        task_description = request.form.get("task_description")
        if not task_description:
            return jsonify({"error": "Task description is required"}), 400

        task = {
            "_id": str(uuid4()),  # ID unique pour chaque tâche
            "description": task_description,
            "timestamp": datetime.now()
        }

        students_collection.update_one(
            {"_id": ObjectId(student_id)},
            {"$push": {"tasks": task}}
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
        




    @main.route("/tasks/<student_id>")
    def view_tasks(student_id):
        """
        Affiche les tâches d'un étudiant spécifique.
        """
        student = students_collection.find_one({"_id": ObjectId(student_id)})
        if not student:
            return "Student not found", 404

        tasks = student.get("tasks", [])
        return render_template("tasks.html", student=student, tasks=tasks)



    @main.route("/toggle_day/<student_id>", methods=["POST"])
    def toggle_day(student_id):
        """
        Commence ou termine une journée pour un étudiant.
        """
        student = students_collection.find_one({"_id": ObjectId(student_id)})
        if not student:
            return jsonify({"error": "Student not found"}), 404

        # Récupérer les données de présence
        attendance = student.get("attendance", {})
        current_time = datetime.now()

        if not attendance.get("start_time"):
            # Démarrer la journée
            attendance["start_time"] = current_time
            attendance["pause_time"] = None
        else:
            # Terminer la journée
            start_time = attendance.get("start_time")
            total_hours = attendance.get("total_hours", 0)

            if start_time:
                # Calculer les heures travaillées
                total_hours += (current_time - start_time).total_seconds() / 3600

            attendance["total_hours"] = total_hours
            attendance["start_time"] = None  # Réinitialiser le temps de départ

        # Mettre à jour les données dans MongoDB
        students_collection.update_one({"_id": ObjectId(student_id)}, {"$set": {"attendance": attendance}})
        return redirect(url_for("main.index"))


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

    @main.route("/weekly_report")
    def weekly_report():
        """
        Génère le rapport hebdomadaire.
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)

        # Pipeline MongoDB pour calculer les heures travaillées
        pipeline = [
            {"$match": {
                "attendance.start_time": {"$gte": start_date, "$lte": end_date}
            }},
            {"$group": {
                "_id": {"name": "$name", "date": "$attendance.start_time"},
                "total_hours": {"$sum": "$attendance.total_hours"},
                "tasks": {"$push": "$tasks"}  # Ajouter les tâches pour chaque étudiant
            }},
            {"$sort": {"_id.date": 1}}
        ]

        report_data = list(students_collection.aggregate(pipeline))

        # Convertir les dates de la clé "_id.date" en objets datetime si elles sont des chaînes
        for record in report_data:
            date = record["_id"].get("date")
            if isinstance(date, str):
                record["_id"]["date"] = datetime.fromisoformat(date)  # Conversion ISO format en datetime

        # Ajout des étudiants et de leurs tâches
        students = list(students_collection.find({}, {"name": 1, "tasks": 1, "_id": 0}))

        return render_template("weekly_report.html", report_data=report_data, students=students)


    @main.route("/sign", methods=["POST"])
    def sign():
        data = request.json
        signature = data.get("signature")
        role = data.get("role")
        name = data.get("name")
        date = data.get("date")

        if not signature or not role or not name or not date:
            return jsonify({"error": "Invalid data"}), 400

        # Update the database
        mongo.db.attendance.update_one(
            {"_id.name": name, "_id.date": date},
            {"$set": {f"{role}_signature": signature}},
            upsert=True
        )
        return jsonify({"message": "Signature saved successfully"}), 200
    
    @blueprint.route("/save_signature", methods=["POST"])
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