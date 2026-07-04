from datetime import datetime

from app.extensions import db


class Payroll(db.Model):
    """Owned by the Payroll module."""

    __tablename__ = "payroll"

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("employees.id"), nullable=False)
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

    payslip_filename = db.Column(db.String(255))  # stored under static/payslips
    generated_on = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint("employee_id", "month", "year", name="uq_employee_month_year"),
    )

    def __repr__(self):
        return f"<Payroll emp={self.employee_id} {self.month}/{self.year}>"
