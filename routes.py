from flask import Blueprint

# Blueprint for the Payroll module.
# templates live in app/templates/payroll/
payroll_bp = Blueprint(
    "payroll",
    __name__,
    url_prefix="/payroll",
    template_folder="../templates/payroll",
)


@payroll_bp.route("/ping")
def ping():
    # Temporary route to confirm the blueprint is wired up.
    return "Payroll blueprint is ready."
