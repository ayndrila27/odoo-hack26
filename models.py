from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date

db = SQLAlchemy()


class Attendance(db.Model):
    """One row per employee per day."""
    __tablename__ = "attendance"

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.String(50), nullable=False, index=True)
    date = db.Column(db.Date, nullable=False, default=date.today, index=True)
    check_in = db.Column(db.DateTime, nullable=True)
    check_out = db.Column(db.DateTime, nullable=True)
    # Present / Absent / Half-day / Leave
    status = db.Column(db.String(20), nullable=False, default="Absent")

    __table_args__ = (
        db.UniqueConstraint("employee_id", "date", name="uq_employee_date"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "employee_id": self.employee_id,
            "date": self.date.isoformat(),
            "check_in": self.check_in.strftime("%H:%M:%S") if self.check_in else None,
            "check_out": self.check_out.strftime("%H:%M:%S") if self.check_out else None,
            "status": self.status,
        }


class Leave(db.Model):
    """One row per leave request."""
    __tablename__ = "leave_request"

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.String(50), nullable=False, index=True)
    # Paid / Sick / Unpaid
    leave_type = db.Column(db.String(20), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    remarks = db.Column(db.String(500), nullable=True)
    # Pending / Approved / Rejected  -> Admin (teammate 3) updates this field
    status = db.Column(db.String(20), nullable=False, default="Pending")
    admin_comment = db.Column(db.String(500), nullable=True)
    applied_on = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "employee_id": self.employee_id,
            "leave_type": self.leave_type,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "remarks": self.remarks,
            "status": self.status,
            "admin_comment": self.admin_comment,
            "applied_on": self.applied_on.strftime("%Y-%m-%d %H:%M"),
        }
