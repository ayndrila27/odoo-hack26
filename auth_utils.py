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

        # The session can outlive the actual user row (e.g. the account was
        # removed, or the dev database was reset while a browser still had
        # an old login cookie). Without this check, get_current_user()
        # silently returns None and every route that does user.id crashes
        # with AttributeError: 'NoneType' object has no attribute 'id'.
        if get_current_user() is None:
            session.clear()
            flash("Your session has expired. Please log in again.", "error")
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
