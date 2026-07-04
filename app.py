"""
NovaHR — Authentication & Employee Profile module.
Run with:  py app.py   (or: python app.py)
"""
import os
from flask import Flask

from models import db
from auth_routes import auth_bp
from profile_routes import profile_bp

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")

app = Flask(__name__)

app.config["SECRET_KEY"] = "odoo-hackathon-2026-secret-key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(BASE_DIR, "hrms.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5 MB max upload

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

db.init_app(app)

app.register_blueprint(auth_bp)
app.register_blueprint(profile_bp)

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)
