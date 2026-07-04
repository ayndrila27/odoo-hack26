"""
Shared helpers for the Authentication & Profile modules.
"""
from functools import wraps
from flask import session, redirect, url_for, flash

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}


def login_required(view_func):
    """Redirect anonymous visitors to the login page."""

    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "error")
            return redirect(url_for("auth.login"))
        return view_func(*args, **kwargs)

    return wrapped


def get_current_user():
    """Fetch the User object for the logged-in session, or None."""
    from models import User

    user_id = session.get("user_id")
    if not user_id:
        return None
    return User.query.get(user_id)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def generate_employee_id():
    """Simple sequential employee ID generator, e.g. EMP0007."""
    from models import User

    count = User.query.count() + 1
    return f"EMP{count:04d}"
