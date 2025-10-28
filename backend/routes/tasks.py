from flask import Blueprint, request, jsonify
from database import db
from models.task import Task
from models.user import User
from flask_jwt_extended import jwt_required, get_jwt_identity

bp = Blueprint("tasks", __name__, url_prefix="/tasks")

@bp.route("", methods=["GET"])
def list_tasks():
    tasks = Task.query.order_by(Task.created_at.desc()).all()
    return jsonify([t.to_dict() for t in tasks])

@bp.route("/mine", methods=["GET"])
@jwt_required()
def list_my_tasks():
    user_id = int(get_jwt_identity())
    tasks = Task.query.filter_by(user_id=user_id).order_by(Task.created_at.desc()).all()
    return jsonify([t.to_dict() for t in tasks])

@bp.route("", methods=["POST"])
@jwt_required()
def create_task():
    data = request.get_json() or {}
    title = data.get("title")
    description = data.get("description", "")
    if not title:
        return jsonify({"msg": "Missing title"}), 400
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return jsonify({"msg": "User not found"}), 404
    task = Task(title=title, description=description, user_id=user_id)
    db.session.add(task)
    db.session.commit()
    return jsonify({"msg": "Task created", "task": task.to_dict()}), 201

@bp.route("/<int:task_id>", methods=["GET"])
def get_task(task_id):
    t = Task.query.get_or_404(task_id)
    return jsonify(t.to_dict())

@bp.route("/<int:task_id>", methods=["PUT"])
@jwt_required()
def update_task(task_id):
    data = request.get_json() or {}
    t = Task.query.get_or_404(task_id)
    user_id = int(get_jwt_identity())
    if t.user_id != user_id:
        return jsonify({"msg": "Unauthorized"}), 403
    t.title = data.get("title", t.title)
    t.description = data.get("description", t.description)
    t.status = data.get("status", t.status)
    db.session.commit()
    return jsonify({"msg": "Task updated", "task": t.to_dict()})

@bp.route("/<int:task_id>", methods=["DELETE"])
@jwt_required()
def delete_task(task_id):
    t = Task.query.get_or_404(task_id)
    user_id = int(get_jwt_identity())
    if t.user_id != user_id:
        return jsonify({"msg": "Unauthorized"}), 403
    db.session.delete(t)
    db.session.commit()
    return jsonify({"msg": "Task deleted"})
