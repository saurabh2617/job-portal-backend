from flask import Blueprint, request, jsonify, send_from_directory
from models import db, Job, Application, User, Profile
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
import os
import uuid

jobs_bp = Blueprint('jobs', __name__)

# Absolute upload folder
basedir = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(basedir, "uploads")

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


# -----------------------------
# PROFILE REQUIRED HELPER
# -----------------------------
def require_profile(user_id):
    profile = Profile.query.filter_by(user_id=user_id).first()
    if not profile:
        return False
    return True


# -----------------------------
# POST JOB (Recruiter)
# -----------------------------
@jobs_bp.route('/jobs', methods=['POST'])
@jwt_required()
def post_job():
    user_id = int(get_jwt_identity())

    user = User.query.get(user_id)
    if not user or user.role != "recruiter":
        return jsonify(msg="Access denied"), 403

    # 🔥 Profile mandatory
    if not require_profile(user_id):
        return jsonify(msg="Complete your profile first"), 403

    data = request.get_json()

    job = Job(
        recruiter_id=user_id,
        title=data['title'],
        description=data['description'],
        company=data['company'],
        location=data['location']
    )

    db.session.add(job)
    db.session.commit()

    return jsonify(msg="Job posted successfully"), 201


# -----------------------------
# GET ALL JOBS
# -----------------------------
@jobs_bp.route('/jobs', methods=['GET'])
@jwt_required()
def get_jobs():
    user_id = int(get_jwt_identity())

    # ✅ FIX: Check if the user is a jobseeker, block recruiters
    user = User.query.get(user_id)
    if not user or user.role != "jobseeker":
        return jsonify(msg="Access denied: Only job seekers can browse jobs"), 403

    # 🔥 Profile mandatory
    if not require_profile(user_id):
        return jsonify(msg="Complete your profile first"), 403

    jobs = Job.query.all()
    result = []

    for job in jobs:
        applied = Application.query.filter_by(
            job_id=job.id,
            user_id=user_id
        ).first() is not None

        result.append({
            "id": job.id,
            "title": job.title,
            "description": job.description,
            "company": job.company,
            "location": job.location,
            "applied": applied
        })

    return jsonify(result)


# -----------------------------
# SINGLE JOB
# -----------------------------
@jobs_bp.route('/jobs/<int:id>', methods=['GET'])
@jwt_required()
def get_single_job(id):
    user_id = int(get_jwt_identity())

    if not require_profile(user_id):
        return jsonify(msg="Complete your profile first"), 403

    job = Job.query.get_or_404(id)

    return jsonify({
        "id": job.id,
        "title": job.title,
        "description": job.description,
        "company": job.company,
        "location": job.location
    })


# -----------------------------
# APPLY JOB
# -----------------------------
@jobs_bp.route('/apply/<int:job_id>', methods=['POST'])
@jwt_required()
def apply_job(job_id):
    user_id = int(get_jwt_identity())

    user = User.query.get(user_id)
    if not user or user.role != "jobseeker":
        return jsonify(msg="Only job seekers can apply"), 403

    # 🔥 Profile mandatory
    if not require_profile(user_id):
        return jsonify(msg="Complete your profile before applying"), 403

    existing = Application.query.filter_by(
        job_id=job_id,
        user_id=user_id
    ).first()

    if existing:
        return jsonify(msg="Already applied"), 400

    if 'resume' not in request.files:
        return jsonify(msg="Resume file required"), 400

    file = request.files['resume']

    if file.filename == "":
        return jsonify(msg="No file selected"), 400

    if not file.filename.lower().endswith(".pdf"):
        return jsonify(msg="Only PDF resumes allowed"), 400

    unique_name = str(uuid.uuid4()) + "_" + secure_filename(file.filename)
    file.save(os.path.join(UPLOAD_FOLDER, unique_name))

    application = Application(
        job_id=job_id,
        user_id=user_id,
        status="Pending",
        resume=unique_name
    )

    db.session.add(application)
    db.session.commit()

    return jsonify(msg="Application submitted successfully"), 201


# -----------------------------
# VIEW RESUME
# -----------------------------
@jobs_bp.route('/resume/<filename>', methods=['GET'])
@jwt_required()
def get_resume(filename):
    user_id = int(get_jwt_identity())

    user = User.query.get(user_id)
    if not user or user.role != "recruiter":
        return jsonify(msg="Access denied"), 403

    application = Application.query.filter_by(resume=filename).first()
    if not application:
        return jsonify(msg="Resume not found"), 404

    job = Job.query.get(application.job_id)
    if job.recruiter_id != user_id:
        return jsonify(msg="Unauthorized"), 403

    return send_from_directory(UPLOAD_FOLDER, filename)


# -----------------------------
# MY APPLICATIONS
# -----------------------------
@jobs_bp.route('/my-applications', methods=['GET'])
@jwt_required()
def my_applications():
    user_id = int(get_jwt_identity())

    if not require_profile(user_id):
        return jsonify(msg="Complete your profile first"), 403

    applications = Application.query.filter_by(user_id=user_id).all()
    result = []

    for app in applications:
        job = Job.query.get(app.job_id)

        result.append({
            "id": app.id,  # ✅ FIX: Added application id for the frontend map function
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "status": app.status,
            "resume": app.resume
        })

    return jsonify(result)


# -----------------------------
# MY POSTED JOBS
# -----------------------------
@jobs_bp.route('/my-jobs', methods=['GET'])
@jwt_required()
def my_jobs():
    user_id = int(get_jwt_identity())

    user = User.query.get(user_id)
    if not user or user.role != "recruiter":
        return jsonify(msg="Access denied"), 403

    if not require_profile(user_id):
        return jsonify(msg="Complete your profile first"), 403

    jobs = Job.query.filter_by(recruiter_id=user_id).all()

    return jsonify([
        {
            "id": job.id,
            "title": job.title,
            "company": job.company,
            "location": job.location
        }
        for job in jobs
    ]), 200


# -----------------------------
# VIEW APPLICANTS
# -----------------------------
@jobs_bp.route('/job-applicants/<int:job_id>', methods=['GET'])
@jwt_required()
def job_applicants(job_id):
    user_id = int(get_jwt_identity())

    user = User.query.get(user_id)
    if not user or user.role != "recruiter":
        return jsonify(msg="Access denied"), 403

    if not require_profile(user_id):
        return jsonify(msg="Complete your profile first"), 403

    job = Job.query.get(job_id)
    if not job:
        return jsonify(msg="Job not found"), 404

    if job.recruiter_id != user_id:
        return jsonify(msg="Unauthorized"), 403

    applications = Application.query.filter_by(job_id=job_id).all()

    result = []
    for app in applications:
        applicant = User.query.get(app.user_id)
        profile = Profile.query.filter_by(user_id=app.user_id).first()

        result.append({
            "application_id": app.id,
            "name": profile.name if profile else "No profile",
            "email": applicant.email,
            "status": app.status,
            "resume": app.resume
        })

    return jsonify(result), 200

# -----------------------------
# RECRUITER DASHBOARD STATS
# -----------------------------
@jobs_bp.route('/recruiter-stats', methods=['GET'])
@jwt_required()
def recruiter_stats():
    user_id = int(get_jwt_identity())

    user = User.query.get(user_id)
    if not user or user.role != "recruiter":
        return jsonify(msg="Access denied"), 403

    # Total jobs posted
    total_jobs = Job.query.filter_by(recruiter_id=user_id).count()

    # Get job IDs
    recruiter_jobs = Job.query.filter_by(recruiter_id=user_id).all()
    job_ids = [job.id for job in recruiter_jobs]

    # Total applications received
    total_applications = 0
    if job_ids:
        total_applications = Application.query.filter(
            Application.job_id.in_(job_ids)
        ).count()

    return jsonify({
        "total_jobs": total_jobs,
        "total_applications": total_applications
    }), 200

# -----------------------------
# JOBSEEKER DASHBOARD STATS
# -----------------------------
@jobs_bp.route('/jobseeker-stats', methods=['GET'])
@jwt_required()
def jobseeker_stats():
    user_id = int(get_jwt_identity())

    user = User.query.get(user_id)
    if not user or user.role != "jobseeker":
        return jsonify(msg="Access denied"), 403

    total_applications = Application.query.filter_by(user_id=user_id).count()

    pending = Application.query.filter_by(
        user_id=user_id,
        status="Pending"
    ).count()

    accepted = Application.query.filter_by(
        user_id=user_id,
        status="Accepted"
    ).count()

    rejected = Application.query.filter_by(
        user_id=user_id,
        status="Rejected"
    ).count()

    return jsonify({
        "total_applications": total_applications,
        "pending": pending,
        "accepted": accepted,
        "rejected": rejected
    }), 200


# -----------------------------
# UPDATE STATUS
# -----------------------------
@jobs_bp.route('/update-status/<int:application_id>', methods=['PUT'])
@jwt_required()
def update_status(application_id):
    user_id = int(get_jwt_identity())

    user = User.query.get(user_id)
    if not user or user.role != "recruiter":
        return jsonify(msg="Access denied"), 403

    if not require_profile(user_id):
        return jsonify(msg="Complete your profile first"), 403

    application = Application.query.get(application_id)
    if not application:
        return jsonify(msg="Application not found"), 404

    job = Job.query.get(application.job_id)
    if job.recruiter_id != user_id:
        return jsonify(msg="Unauthorized"), 403

    data = request.get_json()
    application.status = data.get("status", application.status)

    db.session.commit()

    return jsonify(msg="Status updated successfully")