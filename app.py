from flask import Flask
from models import db
from auth import auth_bp
from profile import profile_bp
from jobs import jobs_bp
from flask_jwt_extended import JWTManager
from flask_cors import CORS
import os

app = Flask(__name__)

# ---------------------------------
# Database Configuration
# ---------------------------------
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = \
    'sqlite:///' + os.path.join(basedir, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# ---------------------------------
# JWT Configuration
# ---------------------------------
app.config['JWT_SECRET_KEY'] = 'super-secret-key-change-this'

jwt = JWTManager(app)

# ---------------------------------
# Initialize Extensions
# ---------------------------------
db.init_app(app)
CORS(app)

# ---------------------------------
# Register Blueprints (ALL routes start with /api)
# ---------------------------------
app.register_blueprint(auth_bp, url_prefix="/api")
app.register_blueprint(profile_bp, url_prefix="/api")
app.register_blueprint(jobs_bp, url_prefix="/api")

# ---------------------------------
# Create Database Tables
# ---------------------------------
with app.app_context():
    db.create_all()

# ---------------------------------
# Run App
# ---------------------------------
if __name__ == "__main__":
  app.run(debug=True, use_reloader=False)
