"""
NovaHR — unified entry point.
Registers all three modules' blueprints on one shared Flask app + one
shared SQLite db (see models.py). Run with: python app.py
"""

import os
from flask import Flask

from models import db
from auth_routes import auth_bp
from profile_routes import profile_bp
from attendance_leave import attendance_bp
from admin_routes import admin_bp

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
app.jinja_env.filters["ord0"] = lambda s: ord(s[0]) if s else 0
app.jinja_env.globals["MONTH_NAMES"] = [
    "", "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]

app.register_blueprint(auth_bp)
app.register_blueprint(profile_bp)
app.register_blueprint(attendance_bp)
app.register_blueprint(admin_bp)


@app.context_processor
def inject_current_user():
    """Makes the real logged-in user (with their actual photo) available to
    every template — previously the sidebar always showed a static
    placeholder avatar for every user, logged-in or not."""
    from auth_utils import get_current_user
    return {"current_user": get_current_user()}

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)
