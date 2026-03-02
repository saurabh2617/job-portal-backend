from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


# =========================
# USER MODEL
# =========================
class User(db.Model):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)

    # Relationships
    profile = db.relationship("Profile", backref="user", uselist=False, cascade="all, delete")
    jobs = db.relationship("Job", backref="recruiter", cascade="all, delete")
    applications = db.relationship("Application", backref="applicant", cascade="all, delete")


# =========================
# PROFILE MODEL
# =========================
class Profile(db.Model):
    __tablename__ = "profile"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    name = db.Column(db.String(100))
    headline = db.Column(db.String(200))
    about = db.Column(db.Text)
    skills = db.Column(db.Text)
    resume = db.Column(db.String(200))


# =========================
# JOB MODEL
# =========================
class Job(db.Model):
    __tablename__ = "job"

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    company = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False)

    recruiter_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    # Relationship
    applications = db.relationship("Application", backref="job", cascade="all, delete")


# =========================
# APPLICATION MODEL
# =========================
class Application(db.Model):
    __tablename__ = "application"

    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey("job.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    status = db.Column(db.String(20), default="Pending")

    resume = db.Column(db.String(200))   # ✅ NEW
