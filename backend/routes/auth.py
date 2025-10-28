from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta
from database import db
from models.user import User
from flask_jwt_extended import create_access_token

bp = Blueprint("auth", __name__, url_prefix="/auth")

@bp.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    email = data.get("email")
    password = data.get("password")
    username = data.get("username") or email.split("@")[0]

    if not email or not password:
        return jsonify({"msg": "Missing email or password"}), 400

    # Enforce KPU student email domain
    allowed_domain = "student.kpu.ca"
    try:
        domain = email.split("@", 1)[1].lower()
    except Exception:
        domain = ""
    if domain != allowed_domain:
        return jsonify({"msg": "Please use your KPU student email (@student.kpu.ca)."}), 400

    existing = User.query.filter_by(email=email).first()
    if existing:
        return jsonify({"msg": "Email already registered"}), 409

    hashed_pw = generate_password_hash(password)
    user = User(username=username, email=email, password_hash=hashed_pw)
    db.session.add(user)
    db.session.commit()
    # JWT 'sub' (subject) must be a string; store user id as string
    token = create_access_token(identity=str(user.id), expires_delta=timedelta(days=7))
    return jsonify({"msg": "User registered", "user": user.to_dict(), "token": token}), 201

@bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    email = data.get("email")
    password = data.get("password")
    if not email or not password:
        return jsonify({"msg": "Missing credentials"}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"msg": "Invalid credentials"}), 401

    # JWT 'sub' (subject) must be a string; store user id as string
    token = create_access_token(identity=str(user.id))
    return jsonify({"msg": "Login success", "user": user.to_dict(), "token": token}), 200
