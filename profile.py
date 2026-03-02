from flask import Blueprint, request, jsonify
from models import db, Profile
from flask_jwt_extended import jwt_required, get_jwt_identity
import os
from werkzeug.utils import secure_filename

profile_bp = Blueprint('profile', __name__)

UPLOAD_FOLDER = "uploads"

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


# -----------------------------
# CREATE PROFILE
# -----------------------------
@profile_bp.route("/profile", methods=["POST"])
@jwt_required()
def create_profile():
    user_id = int(get_jwt_identity())
    data = request.json

    existing_profile = Profile.query.filter_by(user_id=user_id).first()
    if existing_profile:
        return jsonify({"message": "Profile already exists"}), 400

    profile = Profile(
        user_id=user_id,
        name=data.get("name"),
        headline=data.get("headline"),
        about=data.get("about"),
        skills=data.get("skills")
    )

    db.session.add(profile)
    db.session.commit()

    return jsonify({"message": "Profile created"})


# -----------------------------
# GET PROFILE
# -----------------------------
@profile_bp.route("/profile", methods=["GET"])
@jwt_required()
def get_profile():
    user_id = int(get_jwt_identity())

    profile = Profile.query.filter_by(user_id=user_id).first()

    if not profile:
        return jsonify({"message": "Profile not found"}), 404

    return jsonify({
        "name": profile.name,
        "headline": profile.headline,
        "about": profile.about,
        "skills": profile.skills,
        "resume": profile.resume
    })


# -----------------------------
# UPDATE PROFILE
# -----------------------------
@profile_bp.route("/profile", methods=["PUT"])
@jwt_required()
def update_profile():
    user_id = int(get_jwt_identity())
    data = request.json

    profile = Profile.query.filter_by(user_id=user_id).first()

    if not profile:
        return jsonify({"message": "Profile not found"}), 404

    profile.name = data.get("name", profile.name)
    profile.headline = data.get("headline", profile.headline)
    profile.about = data.get("about", profile.about)
    profile.skills = data.get("skills", profile.skills)

    db.session.commit()

    return jsonify({"message": "Profile updated successfully"})


# -----------------------------
# UPLOAD RESUME
# -----------------------------
@profile_bp.route('/upload-resume', methods=['POST'])
@jwt_required()
def upload_resume():
    user_id = int(get_jwt_identity())

    if 'resume' not in request.files:
        return jsonify(msg="No file uploaded"), 400

    file = request.files['resume']
    filename = secure_filename(file.filename)

    file_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(file_path)

    profile = Profile.query.filter_by(user_id=user_id).first()

    if not profile:
        return jsonify(msg="Create profile first"), 400

    profile.resume = filename
    db.session.commit()

    return jsonify(msg="Resume uploaded successfully")
