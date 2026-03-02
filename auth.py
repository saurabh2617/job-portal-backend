from flask import Blueprint, request, jsonify
from models import db, User
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token

auth_bp = Blueprint('auth', __name__)

# -------------------------
# REGISTER
# -------------------------
@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    if not data.get("email") or not data.get("password") or not data.get("role"):
        return jsonify(msg="Missing fields"), 400

    existing_user = User.query.filter_by(email=data['email']).first()
    if existing_user:
        return jsonify(msg="User already exists"), 400

    user = User(
        email=data['email'],
        password=generate_password_hash(data['password']),
        role=data['role']
    )

    db.session.add(user)
    db.session.commit()

    return jsonify(msg="Registered successfully"), 201


# -------------------------
# LOGIN
# -------------------------
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    if not data.get("email") or not data.get("password"):
        return jsonify(msg="Missing email or password"), 400

    user = User.query.filter_by(email=data['email']).first()

    if not user or not check_password_hash(user.password, data['password']):
        return jsonify(msg="Invalid credentials"), 401

    access_token = create_access_token(identity=str(user.id))

    return jsonify(
        access_token=access_token,
        role=user.role
    ), 200
