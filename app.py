"""
Standalone runner for Teammate 2's Attendance & Leave module.

This lets YOU test check-in/out, weekly/daily views, leave apply/status
right now, without waiting on Teammate 1's auth module.

Run:
    python app.py

Then open http://127.0.0.1:5000/dev-login to "log in" as a fake employee,
and you'll be redirected straight into the attendance dashboard.

--------------------------------------------------------------------
WHEN MERGING WITH THE TEAM:
1. Give Teammate 1 the `models.py` (they may already have their own — just
   make sure Attendance/Leave tables end up in the same app + same db.session).
2. Give Teammate 1 the `attendance_leave.py` blueprint + `templates/` +
   `static/style.css` to drop into the shared project.
3. In THEIR main app.py, they just need:

     from models import db
     from attendance_leave import attendance_leave_bp
     app.register_blueprint(attendance_leave_bp)

4. Delete/ignore this app.py and the /dev-login route — it's only a
   stand-in for Teammate 1's real Sign Up / Sign In pages.
--------------------------------------------------------------------
"""

from flask import Flask, session, redirect, url_for
from models import db
from attendance_leave import attendance_leave_bp

app = Flask(__name__)
app.config["SECRET_KEY"] = "dev-secret-key-change-me"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///hrms.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)
app.register_blueprint(attendance_leave_bp)

with app.app_context():
    db.create_all()


# --- TEMPORARY stand-in for Teammate 1's login, so you can test solo ---
@app.route("/dev-login")
def dev_login():
    session["employee_id"] = "EMP001"
    session["employee_name"] = "Test Employee"
    return redirect(url_for("attendance_leave.attendance_daily"))


@app.route("/login")
def login():
    # Placeholder so login_required's redirect doesn't 404 during solo testing.
    return (
        "<h3>This is a stand-in for Teammate 1's Sign In page.</h3>"
        '<p><a href="/dev-login">Click here to fake-login as EMP001</a></p>'
    )


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
def index():
    if "employee_id" in session:
        return redirect(url_for("attendance_leave.attendance_daily"))
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)
