from datetime import datetime

from flask_login import UserMixin

from app.extensions import db, bcrypt


class Admin(db.Model, UserMixin):
    """HR/Admin user. Owned by the Admin/HR module."""

    __tablename__ = "admins"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def get_id(self):
        # Prefixed so Flask-Login can tell Admin sessions apart from
        # Employee sessions (teammate's self-service login module should
        # do the same on the Employee model, e.g. return f"employee-{self.id}").
        return f"admin-{self.id}"

    def __repr__(self):
        return f"<Admin {self.username}>"
