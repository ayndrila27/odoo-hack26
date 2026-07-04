"""
Shared database models for the whole HRMS app.
Combines: Auth/Profile (Teammate 1), Attendance & Leave (Teammate 2),
Payroll (Teammate 3). ONE db instance, ONE file — don't split this back up,
every blueprint imports `db` and whichever models it needs from here.
"""

from datetime import datetime, date

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    """Owned by Auth & Profile module. role is 'employee' or 'hr'."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="employee")  # "employee" | "hr"
    employee_id = db.Column(db.String(20), unique=True, nullable=False)  # display code e.g. EMP0001
    department = db.Column(db.String(80), nullable=True)
    designation = db.Column(db.String(80), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    address = db.Column(db.String(255), nullable=True)
    profile_pic = db.Column(db.String(255), nullable=True, default="default.png")
    date_joined = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"


class Attendance(db.Model):
    """Owned by Attendance & Leave module. One row per user per day."""

    __tablename__ = "attendance"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    date = db.Column(db.Date, nullable=False, default=date.today, index=True)
    check_in = db.Column(db.DateTime, nullable=True)
    check_out = db.Column(db.DateTime, nullable=True)
    # Present / Absent / Half-day / Leave
    status = db.Column(db.String(20), nullable=False, default="Absent")

    __table_args__ = (
        db.UniqueConstraint("user_id", "date", name="uq_user_date"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "date": self.date.isoformat(),
            "check_in": self.check_in.strftime("%H:%M:%S") if self.check_in else None,
            "check_out": self.check_out.strftime("%H:%M:%S") if self.check_out else None,
            "status": self.status,
        }

    def __repr__(self):
        return f"<Attendance user={self.user_id} {self.date} {self.status}>"


class Leave(db.Model):
    """Owned by Attendance & Leave module. One row per leave request."""

    __tablename__ = "leave_request"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    # Paid / Sick / Unpaid
    leave_type = db.Column(db.String(20), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    remarks = db.Column(db.String(500), nullable=True)
    # Pending / Approved / Rejected -> updated by Admin/Payroll module
    status = db.Column(db.String(20), nullable=False, default="Pending")
    admin_comment = db.Column(db.String(500), nullable=True)
    applied_on = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "leave_type": self.leave_type,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "remarks": self.remarks,
            "status": self.status,
            "admin_comment": self.admin_comment,
            "applied_on": self.applied_on.strftime("%Y-%m-%d %H:%M"),
        }

    def __repr__(self):
        return f"<Leave user={self.user_id} {self.leave_type} {self.status}>"


class Payroll(db.Model):
    """Owned by Admin & Payroll module."""

    __tablename__ = "payroll"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    month = db.Column(db.Integer, nullable=False)  # 1-12
    year = db.Column(db.Integer, nullable=False)

    basic_salary = db.Column(db.Float, nullable=False, default=0.0)

    # Allowances
    hra = db.Column(db.Float, default=0.0)
    da = db.Column(db.Float, default=0.0)
    medical_allowance = db.Column(db.Float, default=0.0)
    other_allowance = db.Column(db.Float, default=0.0)

    # Deductions
    provident_fund = db.Column(db.Float, default=0.0)
    professional_tax = db.Column(db.Float, default=0.0)
    other_deduction = db.Column(db.Float, default=0.0)

    gross_salary = db.Column(db.Float, default=0.0)
    total_deductions = db.Column(db.Float, default=0.0)
    net_salary = db.Column(db.Float, default=0.0)

    payslip_filename = db.Column(db.String(255))
    generated_on = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint("user_id", "month", "year", name="uq_user_month_year"),
    )

    def recalculate(self):
        self.gross_salary = (
            self.basic_salary + self.hra + self.da +
            self.medical_allowance + self.other_allowance
        )
        self.total_deductions = (
            self.provident_fund + self.professional_tax + self.other_deduction
        )
        self.net_salary = self.gross_salary - self.total_deductions

    def __repr__(self):
        return f"<Payroll user={self.user_id} {self.month}/{self.year}>"
