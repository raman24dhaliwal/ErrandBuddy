from flask import Blueprint, request, jsonify
from database import db
from models.message import Message
from models.user import User
from flask_jwt_extended import jwt_required, get_jwt_identity

bp = Blueprint("chat", __name__, url_prefix="/chat")

@bp.route("/messages/<int:other_id>", methods=["GET"])
@jwt_required()
def get_conversation(other_id):
    user_id = int(get_jwt_identity())
    msgs = Message.query.filter(
        ((Message.sender_id == user_id) & (Message.receiver_id == other_id)) |
        ((Message.sender_id == other_id) & (Message.receiver_id == user_id))
    ).order_by(Message.timestamp.asc()).all()
    return jsonify([m.to_dict() for m in msgs])

@bp.route("/send", methods=["POST"])
@jwt_required()
def send_message():
    data = request.get_json() or {}
    user_id = int(get_jwt_identity())
    receiver_id = data.get("receiver_id")
    content = data.get("content")
    if not receiver_id or not content:
        return jsonify({"msg": "Missing data"}), 400
    # ensure receiver exists
    rec = User.query.get(receiver_id)
    if not rec:
        return jsonify({"msg": "Receiver not found"}), 404
    msg = Message(sender_id=user_id, receiver_id=receiver_id, content=content)
    db.session.add(msg)
    db.session.commit()
    return jsonify({"msg": "Message sent", "message": msg.to_dict()}), 201
