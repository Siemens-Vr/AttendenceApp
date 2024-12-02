from flask_pymongo import PyMongo
from datetime import datetime, timedelta

db = PyMongo()


def get_students():
    students = list(db.students.find())
    for student in students:
        student["_id"] = str(student["_id"])
    return students

def get_students():
    return list(db.db.students.find())

def add_student(name, role, image):
    student_data = {
        "name": name,
        "role": role,
        "image": image,
        "created_at": datetime.now(),
        "active": True
    }
    db.db.students.insert_one(student_data)

def get_tasks(student_name):
    return list(db.db.tasks.find({"name": student_name}).sort("timestamp", 1))

def add_task(student_name, task_description):
    task_data = {
        "name": student_name,
        "task": task_description,
        "timestamp": datetime.now(),
    }
    db.db.tasks.insert_one(task_data)

def add_signature(name, date, role, signature):
    db.db.signatures.update_one(
        {"name": name, "date": date},
        {"$set": {f"{role}_signature": signature}},
        upsert=True
    )
