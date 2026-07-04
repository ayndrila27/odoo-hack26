"""
Admin & Payroll Module (Teammate 3)

NOTE FOR TEAMMATE 3: your uploaded files (admin.py, payroll.py, routes.py,
__init__.py) were written for an app/ package + Flask-Login structure that
was never actually created in this repo -- they import `app.extensions`
and `app.admin.routes`, which don't exist here, so they crashed on import.

The rest of the team already has a WORKING plain-session auth system
(session['user_id'], session['role']), so this file rebuilds your module
to plug into that instead. Your Payroll model's fields/logic are preserved
almost exactly (see models.py) -- only the auth mechanism changed.

Feel free to take it from here and restyle/extend -- the routes below are
functional but intentionally simple (Bootstrap, not custom NovaHR CSS)
since building the actual admin UI is your module's job.
"""

from functools import wraps
from datetime import datetime, timedelta

from flask import (
    Blueprint, render_template, request, redirect, url_for, session, flash
)

from models import db, User, Attendance, Leave, Payroll

admin_bp = Blueprint("admin", __name__, template_folder="templates")


def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in first.", "error")
            return redirect(url_for("auth.login"))
        if User.query.get(session["user_id"]) is None:
            session.clear()
            flash("Your session has expired. Please log in again.", "error")
            return redirect(url_for("auth.login"))
        if session.get("role") != "hr":
            flash("You don't have permission to view that page.", "error")
            return redirect(url_for("profile.profile"))
        return f(*args, **kwargs)
    return wrapper


# ---------------------------------------------------------------
# DASHBOARD
# ---------------------------------------------------------------

@admin_bp.route("/admin")
@admin_required
def dashboard():
    total_employees = User.query.filter_by(role="employee").count()
    pending_leaves = Leave.query.filter_by(status="Pending").count()
    today_present = Attendance.query.filter_by(
        date=datetime.utcnow().date(), status="Present"
    ).count()

    # --- last 7 days attendance (present count vs total employees) ---
    weekly_attendance = []
    today = datetime.utcnow().date()
    denom = max(total_employees, 1)
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        present_count = Attendance.query.filter(
            Attendance.date == d, Attendance.status.in_(["Present", "Half-day"])
        ).count()
        weekly_attendance.append({
            "label": d.strftime("%a %d"),
            "count": present_count,
            "pct": round((present_count / denom) * 100),
        })

    # --- leave status breakdown ---
    leave_counts = {
        "Pending": Leave.query.filter_by(status="Pending").count(),
        "Approved": Leave.query.filter_by(status="Approved").count(),
        "Rejected": Leave.query.filter_by(status="Rejected").count(),
    }
    max_leave = max(leave_counts.values()) or 1
    leave_breakdown = [
        {"label": k, "count": v, "pct": round((v / max_leave) * 100),
         "css": "teal" if k == "Approved" else ("danger" if k == "Rejected" else "")}
        for k, v in leave_counts.items()
    ]

    return render_template(
        "admin_dashboard.html",
        total_employees=total_employees,
        pending_leaves=pending_leaves,
        today_present=today_present,
        weekly_attendance=weekly_attendance,
        leave_breakdown=leave_breakdown,
    )


# ---------------------------------------------------------------
# EMPLOYEE LIST / DETAIL
# ---------------------------------------------------------------

@admin_bp.route("/admin/employees")
@admin_required
def employee_list():
    employees = User.query.order_by(User.full_name).all()
    return render_template("employee_list.html", employees=employees)


@admin_bp.route("/admin/employees/<int:user_id>", methods=["GET", "POST"])
@admin_required
def employee_detail(user_id):
    employee = User.query.get_or_404(user_id)

    if request.method == "POST":
        employee.full_name = request.form.get("full_name", employee.full_name).strip()
        employee.department = request.form.get("department", "").strip() or None
        employee.designation = request.form.get("designation", "").strip() or None
        employee.phone = request.form.get("phone", "").strip() or None
        employee.address = request.form.get("address", "").strip() or None
        new_role = request.form.get("role")
        if new_role in ("employee", "hr"):
            employee.role = new_role
        db.session.commit()
        flash(f"Updated {employee.full_name}'s details.", "success")
        return redirect(url_for("admin.employee_detail", user_id=employee.id))

    attendance_records = Attendance.query.filter_by(user_id=employee.id) \
        .order_by(Attendance.date.desc()).limit(30).all()
    leave_records = Leave.query.filter_by(user_id=employee.id) \
        .order_by(Leave.applied_on.desc()).all()

    return render_template(
        "employee_detail.html", employee=employee,
        attendance_records=attendance_records, leave_records=leave_records
    )


# ---------------------------------------------------------------
# ATTENDANCE (ALL EMPLOYEES)
# ---------------------------------------------------------------

@admin_bp.route("/admin/attendance")
@admin_required
def all_attendance():
    date_str = request.args.get("date", datetime.utcnow().date().isoformat())
    try:
        selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        selected_date = datetime.utcnow().date()

    records = (
        db.session.query(Attendance, User)
        .join(User, Attendance.user_id == User.id)
        .filter(Attendance.date == selected_date)
        .order_by(User.full_name)
        .all()
    )
    return render_template(
        "all_attendance.html", records=records, selected_date=selected_date
    )


# ---------------------------------------------------------------
# LEAVE APPROVAL
# ---------------------------------------------------------------

@admin_bp.route("/admin/leaves")
@admin_required
def leave_requests():
    status_filter = request.args.get("status", "Pending")
    query = db.session.query(Leave, User).join(User, Leave.user_id == User.id)
    if status_filter != "All":
        query = query.filter(Leave.status == status_filter)
    leaves = query.order_by(Leave.applied_on.desc()).all()
    return render_template(
        "leave_requests.html", leaves=leaves, status_filter=status_filter
    )


@admin_bp.route("/admin/leaves/<int:leave_id>/decide", methods=["POST"])
@admin_required
def decide_leave(leave_id):
    leave = Leave.query.get_or_404(leave_id)
    decision = request.form.get("decision")
    comment = request.form.get("comment", "").strip()

    if decision not in ("Approved", "Rejected"):
        flash("Invalid decision.", "error")
        return redirect(url_for("admin.leave_requests"))

    leave.status = decision
    leave.admin_comment = comment or None
    db.session.commit()
    flash(f"Leave request #{leave.id} marked as {decision}.", "success")
    return redirect(url_for("admin.leave_requests"))


# ---------------------------------------------------------------
# PAYROLL
# ---------------------------------------------------------------

@admin_bp.route("/admin/payroll")
@admin_required
def payroll_list():
    month = int(request.args.get("month", datetime.utcnow().month))
    year = int(request.args.get("year", datetime.utcnow().year))

    employees = User.query.filter_by(role="employee").order_by(User.full_name).all()
    payroll_by_user = {
        p.user_id: p for p in Payroll.query.filter_by(month=month, year=year).all()
    }

    return render_template(
        "payroll_list.html", employees=employees, payroll_by_user=payroll_by_user,
        month=month, year=year
    )


@admin_bp.route("/admin/payroll/<int:user_id>", methods=["GET", "POST"])
@admin_required
def payroll_edit(user_id):
    employee = User.query.get_or_404(user_id)
    month = int(request.args.get("month", datetime.utcnow().month))
    year = int(request.args.get("year", datetime.utcnow().year))

    payroll = Payroll.query.filter_by(user_id=user_id, month=month, year=year).first()
    if not payroll:
        payroll = Payroll(user_id=user_id, month=month, year=year)
        db.session.add(payroll)

    if request.method == "POST":
        def f(name):
            try:
                return float(request.form.get(name, 0) or 0)
            except ValueError:
                return 0.0

        payroll.basic_salary = f("basic_salary")
        payroll.hra = f("hra")
        payroll.da = f("da")
        payroll.medical_allowance = f("medical_allowance")
        payroll.other_allowance = f("other_allowance")
        payroll.provident_fund = f("provident_fund")
        payroll.professional_tax = f("professional_tax")
        payroll.other_deduction = f("other_deduction")
        payroll.recalculate()
        db.session.commit()
        flash(f"Payroll for {employee.full_name} ({month}/{year}) saved.", "success")
        return redirect(url_for("admin.payroll_list", month=month, year=year))

    return render_template(
        "payroll_edit.html", employee=employee, payroll=payroll, month=month, year=year
    )
