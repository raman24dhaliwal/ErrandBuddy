from flask import Blueprint, request, jsonify
from database import db
from models.ride import Ride
from models.user import User
from flask_jwt_extended import jwt_required, get_jwt_identity

bp = Blueprint("rides", __name__, url_prefix="/rides")

@bp.route("", methods=["GET"])
def list_rides():
    rides = Ride.query.order_by(Ride.created_at.desc()).all()
    return jsonify([r.to_dict() for r in rides])

@bp.route("", methods=["POST"])
@jwt_required()
def create_ride():
    data = request.get_json() or {}
    origin = data.get("origin")
    destination = data.get("destination")
    time = data.get("time")
    if not origin or not destination or not time:
        return jsonify({"msg": "Missing data"}), 400
    user_id = get_jwt_identity()
    ride = Ride(driver_id=user_id, origin=origin, destination=destination, time=time)
    db.session.add(ride)
    db.session.commit()
    return jsonify({"msg": "Ride created", "ride": ride.to_dict()}), 201
