"""
Attendance & Leave Module  (Teammate 2)
----------------------------------------
Self-contained Flask Blueprint. Register it on the main app with:

    from attendance_leave import attendance_leave_bp
    app.register_blueprint(attendance_leave_bp)

Assumes:
  - session['employee_id'] is already set by the Auth module (Teammate 1)
    after a successful login.
  - session['employee_name'] (optional) for display purposes.

If those keys aren't in session, routes redirect to '/login' (Teammate 1's route name -
change AUTH_LOGIN_ENDPOINT below if theirs is named differently).
"""

from flask import (
    Blueprint, render_template, request, redirect,
    url_for, session, flash, jsonify
)
from datetime import datetime, date, timedelta
from functools import wraps
from models import db, Attendance, Leave

attendance_leave_bp = Blueprint(
    "attendance_leave", __name__,
    template_folder="templates",
    static_folder="static"
)

# Change this if Teammate 1 names their login route differently
AUTH_LOGIN_ENDPOINT = "login"


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "employee_id" not in session:
            flash("Please log in first.", "warning")
            try:
                return redirect(url_for(AUTH_LOGIN_ENDPOINT))
            except Exception:
                # Fallback if auth blueprint isn't wired up yet (for solo testing)
                return redirect("/login")
        return f(*args, **kwargs)
    return wrapper


def get_week_range(anchor=None):
    """Return (monday, sunday) for the week containing `anchor` date."""
    anchor = anchor or date.today()
    monday = anchor - timedelta(days=anchor.weekday())
    sunday = monday + timedelta(days=6)
    return monday, sunday


# ---------------------------------------------------------------
# CHECK-IN / CHECK-OUT
# ---------------------------------------------------------------

@attendance_leave_bp.route("/attendance/checkin", methods=["POST"])
@login_required
def check_in():
    emp_id = session["employee_id"]
    today = date.today()

    record = Attendance.query.filter_by(employee_id=emp_id, date=today).first()
    if record and record.check_in:
        flash("You have already checked in today.", "info")
        return redirect(url_for("attendance_leave.attendance_daily"))

    if not record:
        record = Attendance(employee_id=emp_id, date=today)
        db.session.add(record)

    record.check_in = datetime.now()
    record.status = "Present"
    db.session.commit()
    flash(f"Checked in at {record.check_in.strftime('%H:%M:%S')}", "success")
    return redirect(url_for("attendance_leave.attendance_daily"))


@attendance_leave_bp.route("/attendance/checkout", methods=["POST"])
@login_required
def check_out():
    emp_id = session["employee_id"]
    today = date.today()

    record = Attendance.query.filter_by(employee_id=emp_id, date=today).first()
    if not record or not record.check_in:
        flash("You need to check in before checking out.", "warning")
        return redirect(url_for("attendance_leave.attendance_daily"))

    if record.check_out:
        flash("You have already checked out today.", "info")
        return redirect(url_for("attendance_leave.attendance_daily"))

    record.check_out = datetime.now()

    # Mark Half-day if worked less than 4 hours, else Present
    worked_hours = (record.check_out - record.check_in).total_seconds() / 3600
    record.status = "Half-day" if worked_hours < 4 else "Present"

    db.session.commit()
    flash(f"Checked out at {record.check_out.strftime('%H:%M:%S')}", "success")
    return redirect(url_for("attendance_leave.attendance_daily"))


# ---------------------------------------------------------------
# ATTENDANCE VIEWS
# ---------------------------------------------------------------

@attendance_leave_bp.route("/attendance/daily")
@login_required
def attendance_daily():
    emp_id = session["employee_id"]
    today = date.today()
    record = Attendance.query.filter_by(employee_id=emp_id, date=today).first()
    return render_template("attendance_daily.html", record=record, today=today)


@attendance_leave_bp.route("/attendance/weekly")
@login_required
def attendance_weekly():
    emp_id = session["employee_id"]
    offset = int(request.args.get("offset", 0))  # 0 = this week, -1 = last week, etc.
    anchor = date.today() + timedelta(weeks=offset)
    monday, sunday = get_week_range(anchor)

    records = Attendance.query.filter(
        Attendance.employee_id == emp_id,
        Attendance.date >= monday,
        Attendance.date <= sunday
    ).order_by(Attendance.date).all()

    by_date = {r.date: r for r in records}
    days = []
    for i in range(7):
        d = monday + timedelta(days=i)
        rec = by_date.get(d)
        days.append({
            "date": d,
            "weekday": d.strftime("%A"),
            "status": rec.status if rec else "Absent",
            "check_in": rec.check_in.strftime("%H:%M") if rec and rec.check_in else "-",
            "check_out": rec.check_out.strftime("%H:%M") if rec and rec.check_out else "-",
        })

    return render_template(
        "attendance_weekly.html", days=days,
        monday=monday, sunday=sunday, offset=offset
    )


@attendance_leave_bp.route("/attendance/history")
@login_required
def attendance_history():
    emp_id = session["employee_id"]
    records = Attendance.query.filter_by(employee_id=emp_id) \
        .order_by(Attendance.date.desc()).all()

    # Simple monthly present/absent counts for a quick summary
    total_present = sum(1 for r in records if r.status in ("Present", "Half-day"))
    total_absent = sum(1 for r in records if r.status == "Absent")
    total_leave = sum(1 for r in records if r.status == "Leave")

    return render_template(
        "attendance_history.html", records=records,
        total_present=total_present, total_absent=total_absent, total_leave=total_leave
    )


# ---------------------------------------------------------------
# LEAVE MANAGEMENT
# ---------------------------------------------------------------

@attendance_leave_bp.route("/leave/apply", methods=["GET", "POST"])
@login_required
def apply_leave():
    if request.method == "POST":
        emp_id = session["employee_id"]
        leave_type = request.form.get("leave_type")
        start_date_str = request.form.get("start_date")
        end_date_str = request.form.get("end_date")
        remarks = request.form.get("remarks", "").strip()

        errors = []
        if leave_type not in ("Paid", "Sick", "Unpaid"):
            errors.append("Please select a valid leave type.")

        try:
            start_dt = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_dt = datetime.strptime(end_date_str, "%Y-%m-%d").date()
            if end_dt < start_dt:
                errors.append("End date cannot be before start date.")
        except (ValueError, TypeError):
            errors.append("Please pick a valid date range on the calendar.")
            start_dt = end_dt = None

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("apply_leave.html")

        new_leave = Leave(
            employee_id=emp_id,
            leave_type=leave_type,
            start_date=start_dt,
            end_date=end_dt,
            remarks=remarks,
            status="Pending"
        )
        db.session.add(new_leave)
        db.session.commit()
        flash("Leave request submitted successfully.", "success")
        return redirect(url_for("attendance_leave.leave_status"))

    return render_template("apply_leave.html")


@attendance_leave_bp.route("/leave/status")
@login_required
def leave_status():
    emp_id = session["employee_id"]
    leaves = Leave.query.filter_by(employee_id=emp_id) \
        .order_by(Leave.applied_on.desc()).all()
    return render_template("leave_status.html", leaves=leaves)


# ---------------------------------------------------------------
# JSON APIs (handy for the calendar widget + for Teammate 3's admin views)
# ---------------------------------------------------------------

@attendance_leave_bp.route("/api/attendance/calendar")
@login_required
def attendance_calendar_json():
    """Returns this employee's attendance as {date: status} for calendar highlighting."""
    emp_id = session["employee_id"]
    records = Attendance.query.filter_by(employee_id=emp_id).all()
    return jsonify({r.date.isoformat(): r.status for r in records})


@attendance_leave_bp.route("/api/leave/mine")
@login_required
def my_leaves_json():
    emp_id = session["employee_id"]
    leaves = Leave.query.filter_by(employee_id=emp_id).all()
    return jsonify([l.to_dict() for l in leaves])
