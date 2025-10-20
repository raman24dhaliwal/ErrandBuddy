from flask import Blueprint, request, jsonify
from database import db
from models.user import User
from flask_jwt_extended import jwt_required, get_jwt_identity

bp = Blueprint("users", __name__, url_prefix="/users")

@bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    user_id = get_jwt_identity()
    user = User.query.get_or_404(user_id)
    return jsonify(user.to_dict())

@bp.route("/<int:user_id>", methods=["GET"])
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify(user.to_dict())

@bp.route("/me", methods=["PUT"])
@jwt_required()
def update_profile():
    user_id = get_jwt_identity()
    user = User.query.get_or_404(user_id)
    data = request.get_json() or {}
    user.username = data.get("username", user.username)
    user.bio = data.get("bio", user.bio)
    db.session.commit()
    return jsonify({"msg": "Profile updated", "user": user.to_dict()})
