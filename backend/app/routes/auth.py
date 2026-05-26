from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from app.database.db import getDB
from app.database.models import new_user
import bcrypt

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    db = getDB()

    if db.users.find_one({ "email": email }):
        return jsonify({ "error": "Email already exists" }), 400

    user = new_user(email, password)
    db.users.insert_one(user)

    return jsonify({ "message": "Account created successfully" }), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    db = getDB()
    user = db.users.find_one({ "email": email })

    if not user:
        return jsonify({ "error": "Invalid email or password" }), 401

    if not bcrypt.checkpw(password.encode("utf-8"), user["password"]):
        return jsonify({ "error": "Invalid email or password" }), 401

    token = create_access_token(identity=str(user["_id"]))
    return jsonify({ "token": token }), 200