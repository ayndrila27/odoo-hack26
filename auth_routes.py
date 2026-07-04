"""
Authentication blueprint: Sign Up, Login, Logout, Role selection.
"""
from flask import (
    Blueprint, render_template, request, redirect, url_for, session, flash
)
from werkzeug.security import generate_password_hash, check_password_hash

from models import db, User
from auth_utils import generate_employee_id

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("profile.profile"))
    return redirect(url_for("auth.login"))


@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        role = request.form.get("role", "employee")
        department = request.form.get("department", "").strip()
        designation = request.form.get("designation", "").strip()

        if not full_name or not email or not password:
            flash("Please fill in all required fields.", "error")
            return render_template("signup.html", form=request.form)

        if role not in ("employee", "hr"):
            flash("Please select a valid role.", "error")
            return render_template("signup.html", form=request.form)

        if len(password) < 6:
            flash("Password must be at least 6 characters long.", "error")
            return render_template("signup.html", form=request.form)

        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return render_template("signup.html", form=request.form)

        if User.query.filter_by(email=email).first():
            flash("An account with this email already exists.", "error")
            return render_template("signup.html", form=request.form)

        new_user = User(
            full_name=full_name,
            email=email,
            password_hash=generate_password_hash(password),
            role=role,
            department=department or None,
            designation=designation or None,
            employee_id=generate_employee_id(),
            profile_pic="default.png",
        )
        db.session.add(new_user)
        db.session.commit()

        flash("Account created successfully! Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("signup.html", form={})


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()

        if not user or not check_password_hash(user.password_hash, password):
            flash("Invalid email or password.", "error")
            return render_template("login.html", email=email)

        session["user_id"] = user.id
        session["role"] = user.role
        session["full_name"] = user.full_name

        flash(f"Welcome back, {user.full_name.split(' ')[0]}!", "success")
        return redirect(url_for("profile.profile"))

    return render_template("login.html", email="")


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out successfully.", "success")
    return redirect(url_for("auth.login"))
