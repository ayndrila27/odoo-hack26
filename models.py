"""
Database models for the NovaHR Authentication & Employee Profile module.
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)

    role = db.Column(db.String(20), nullable=False, default="employee")  # "employee" | "hr"

    employee_id = db.Column(db.String(20), unique=True, nullable=False)
    department = db.Column(db.String(80), nullable=True)
    designation = db.Column(db.String(80), nullable=True)

    phone = db.Column(db.String(20), nullable=True)
    address = db.Column(db.String(255), nullable=True)
    profile_pic = db.Column(db.String(255), nullable=True, default="default.png")

    date_joined = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"
