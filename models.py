
from datetime import datetime, timedelta
from bson.objectid import ObjectId
from flask_login import UserMixin
from extensions import mongo



# MongoDB collections (à lier depuis app.py)


# Modèle utilisateur pour Flask-Login
class User(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data["_id"])
        self.username = user_data["username"]
        self.role = user_data["role"]
        self.employee_card_id = user_data.get("employee_card_id")

def get_students():
    students = list(mongo.students.find())
    for student in students:
        student["_id"] = str(student["_id"])
    return students


def add_student(name, role, image):
    student_data = {
        "name": name,
        "role": role,
        "image": image,
        "created_at": datetime.now(),
        "active": True
    }
    mongo.db.students.insert_one(student_data)

def get_tasks(student_name):
    return list(mongo.db.tasks.find({"name": student_name}).sort("timestamp", 1))

def add_task(student_name, task_description):
    task_data = {
        "name": student_name,
        "task": task_description,
        "timestamp": datetime.now(),
    }
    mongo.db.tasks.insert_one(task_data)

def add_signature(name, date, role, signature):
    mongo.db.signatures.update_one(
        {"name": name, "date": date},
        {"$set": {f"{role}_signature": signature}},
        upsert=True
    )
