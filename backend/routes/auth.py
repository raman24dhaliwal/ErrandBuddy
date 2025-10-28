from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from database import db
from models.user import User
from models.email_otp import EmailOTP
from flask_jwt_extended import create_access_token
import secrets

from mailer import send_email

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

    # Create the user record (unverified until OTP check passes)
    hashed_pw = generate_password_hash(password)
    user = User(username=username, email=email, password_hash=hashed_pw)
    db.session.add(user)
    db.session.commit()

    # Generate a 6-digit OTP and store hash with 10-minute expiry
    otp_code = f"{secrets.randbelow(1000000):06d}"
    otp_hash = generate_password_hash(otp_code)
    expires = datetime.utcnow() + timedelta(minutes=10)
    # Upsert single active OTP per user
    otp = EmailOTP.query.filter_by(user_id=user.id).first()
    if not otp:
        otp = EmailOTP(user_id=user.id, code_hash=otp_hash, expires_at=expires)
        db.session.add(otp)
    else:
        otp.code_hash = otp_hash
        otp.expires_at = expires
        otp.attempts = 0
        otp.verified = False
    db.session.commit()

    # Send OTP via email (or print to console in dev)
    subject = "ErrandBuddy Email Verification"
    body = (
        f"Hi {username},\n\n"
        f"Your verification code is: {otp_code}\n\n"
        f"This code expires in 10 minutes. If you did not request this, you can ignore this email.\n"
    )
    send_email(user.email, subject, body)

    return jsonify({
        "msg": "Verification code sent to your email.",
        "verify_required": True,
    }), 201

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

    # Require verified email via OTP before issuing tokens
    otp = EmailOTP.query.filter_by(user_id=user.id).first()
    if otp and not otp.verified:
        return jsonify({"msg": "Email not verified. Please enter the OTP sent to your email."}), 403

    # JWT 'sub' (subject) must be a string; store user id as string
    token = create_access_token(identity=str(user.id))
    return jsonify({"msg": "Login success", "user": user.to_dict(), "token": token}), 200


@bp.route("/verify-otp", methods=["POST"])
def verify_otp():
    data = request.get_json() or {}
    email = data.get("email")
    code = data.get("otp") or data.get("code")
    if not email or not code:
        return jsonify({"msg": "Missing email or OTP"}), 400
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"msg": "User not found"}), 404
    otp = EmailOTP.query.filter_by(user_id=user.id).first()
    if not otp:
        return jsonify({"msg": "No OTP request found. Please register again."}), 400
    if otp.verified:
        return jsonify({"msg": "Email already verified"}), 200
    if otp.is_expired():
        return jsonify({"msg": "OTP expired. Please request a new code."}), 400
    # rate-limit attempts (basic)
    if otp.attempts is not None and otp.attempts >= 5:
        return jsonify({"msg": "Too many attempts. Please request a new code."}), 429
    # verify code
    ok = check_password_hash(otp.code_hash, str(code).strip())
    otp.attempts = (otp.attempts or 0) + 1
    if not ok:
        db.session.commit()
        return jsonify({"msg": "Invalid code"}), 401
    # success
    otp.verified = True
    db.session.commit()
    return jsonify({"msg": "Email verified successfully"}), 200


@bp.route("/resend-otp", methods=["POST"])
def resend_otp():
    data = request.get_json() or {}
    email = data.get("email")
    if not email:
        return jsonify({"msg": "Missing email"}), 400
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"msg": "User not found"}), 404
    otp = EmailOTP.query.filter_by(user_id=user.id).first()
    if otp and otp.verified:
        return jsonify({"msg": "Email already verified"}), 200
    # generate new code
    otp_code = f"{secrets.randbelow(1000000):06d}"
    otp_hash = generate_password_hash(otp_code)
    expires = datetime.utcnow() + timedelta(minutes=10)
    if not otp:
        otp = EmailOTP(user_id=user.id, code_hash=otp_hash, expires_at=expires)
        db.session.add(otp)
    else:
        otp.code_hash = otp_hash
        otp.expires_at = expires
        otp.attempts = 0
        otp.verified = False
    db.session.commit()
    subject = "ErrandBuddy Email Verification (Resent)"
    body = (
        f"Hi {user.username},\n\n"
        f"Your verification code is: {otp_code}\n\n"
        f"This code expires in 10 minutes."
    )
    send_email(user.email, subject, body)
    return jsonify({"msg": "A new verification code has been sent."}), 200
