from flask_restful import Resource, reqparse
from extensions import mongo  # Assurez-vous que `mongo` est importé depuis extensions

def serialize_mongo_doc(doc):
    """
    Serialize a MongoDB document for JSON response.
    """
    if "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc

class StudentsResource(Resource):
    """
    Handle fetching all students.
    """
    def get(self):
        students = list(mongo.db.students.find())
        if not students:
            return {"message": "No students found"}, 404
        return [serialize_mongo_doc(student) for student in students], 200

class AddStudentResource(Resource):
    """
    Handle adding a new student.
    """
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument("name", required=True, help="Name is required")
        parser.add_argument("role", required=True, help="Role is required")
        args = parser.parse_args()

        student = {"name": args["name"], "role": args["role"]}
        mongo.db.students.insert_one(student)
        return {"message": "Student added successfully"}, 201

# Configuration des routes API
def configure_api_routes(api):
    """
    Register API routes.
    """
    api.add_resource(StudentsResource, '/api/students')
    api.add_resource(AddStudentResource, '/api/students/add')
