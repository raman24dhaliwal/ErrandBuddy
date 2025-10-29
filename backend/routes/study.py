from flask import Blueprint, request, jsonify
from database import db
from models.study_session import StudySession
from models.user import User
from flask_jwt_extended import jwt_required, get_jwt_identity


bp = Blueprint("study", __name__, url_prefix="/study")


@bp.route("", methods=["GET"])
def list_sessions():
    # Optional filtering by campus and course substring
    q = (request.args.get("q") or "").strip()
    campus = (request.args.get("campus") or "").strip().title()

    query = StudySession.query
    if campus:
        query = query.filter(StudySession.campus == campus)
    if q:
        try:
            query = query.filter(StudySession.course.ilike(f"%{q}%"))
        except Exception:
            query = query.filter(StudySession.course.like(f"%{q}%"))
    sessions = query.order_by(StudySession.created_at.desc()).all()

    # Include basic owner info for convenience
    result = []
    for s in sessions:
        item = s.to_dict()
        try:
            u = User.query.get(s.user_id)
            if u:
                item["owner"] = {"id": u.id, "username": u.username,
                                  "first_name": u.first_name, "last_name": u.last_name}
        except Exception:
            pass
        result.append(item)
    return jsonify(result)


ALLOWED_CAMPUSES = {"Surrey", "Langley", "Richmond"}


@bp.route("", methods=["POST"])
@jwt_required()
def create_session():
    data = request.get_json() or {}
    course = (data.get("course") or "").strip()
    available = bool(data.get("available", True))
    campus = (data.get("campus") or "Surrey").strip().title()
    teacher = (data.get("teacher") or "").strip()
    description = (data.get("description") or "").strip()
    if not course:
        return jsonify({"msg": "Missing course"}), 400
    if campus not in ALLOWED_CAMPUSES:
        return jsonify({"msg": "Invalid campus", "allowed": sorted(list(ALLOWED_CAMPUSES))}), 400
    user_id = int(get_jwt_identity())
    s = StudySession(user_id=user_id, course=course, available=available, campus=campus,
                     teacher=teacher, description=description)
    db.session.add(s)
    db.session.commit()
    return jsonify({"msg": "Study session created", "session": s.to_dict()}), 201


@bp.route("/<int:session_id>", methods=["PUT"])
@jwt_required()
def update_session(session_id):
    s = StudySession.query.get_or_404(session_id)
    user_id = int(get_jwt_identity())
    if s.user_id != user_id:
        return jsonify({"msg": "Unauthorized"}), 403
    data = request.get_json() or {}
    if "course" in data:
        c = (data.get("course") or "").strip()
        if c:
            s.course = c
    if "available" in data:
        s.available = bool(data.get("available"))
    if "campus" in data:
        campus = (data.get("campus") or "").strip().title()
        if campus and campus in ALLOWED_CAMPUSES:
            s.campus = campus
    if "teacher" in data:
        s.teacher = (data.get("teacher") or "").strip()
    if "description" in data:
        s.description = (data.get("description") or "").strip()
    db.session.commit()
    return jsonify({"msg": "Session updated", "session": s.to_dict()})


@bp.route("/<int:session_id>", methods=["DELETE"])
@jwt_required()
def delete_session(session_id):
    s = StudySession.query.get_or_404(session_id)
    user_id = int(get_jwt_identity())
    if s.user_id != user_id:
        return jsonify({"msg": "Unauthorized"}), 403
    db.session.delete(s)
    db.session.commit()
    return jsonify({"msg": "Session deleted"})


@bp.route("/<int:session_id>/connect", methods=["POST"])
@jwt_required()
def connect_session(session_id):
    """Return data needed to start a chat with the session owner."""
    s = StudySession.query.get_or_404(session_id)
    user_id = int(get_jwt_identity())
    if s.user_id == user_id:
        return jsonify({"msg": "You own this session."}), 400
    owner = User.query.get(s.user_id)
    if not owner:
        return jsonify({"msg": "Owner not found"}), 404
    return jsonify({
        "msg": "Connected",
        "owner_id": owner.id,
        "owner": {
            "id": owner.id,
            "username": owner.username,
            "first_name": owner.first_name,
            "last_name": owner.last_name,
        },
        "session": s.to_dict(),
    }), 200
