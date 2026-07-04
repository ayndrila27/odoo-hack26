import os

from flask import Flask

from config import Config
from app.extensions import db, bcrypt, login_manager


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Make sure folders used for uploads/instance db exist
    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(app.config["PAYSLIP_FOLDER"], exist_ok=True)

    # --- init extensions ---
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "admin.login"
    login_manager.login_message_category = "warning"

    # Import models so SQLAlchemy knows about all tables before create_all()
    from app.models import Admin, Employee  # noqa: F401

    @login_manager.user_loader
    def load_user(user_id):
        # IDs are prefixed (see Admin.get_id) so one login_manager can
        # eventually serve both Admin and Employee sessions.
        if user_id.startswith("admin-"):
            return Admin.query.get(int(user_id.split("-", 1)[1]))
        if user_id.startswith("employee-"):
            # Teammate building Employee self-service login: give Employee
            # a matching get_id() (e.g. f"employee-{self.id}") and this
            # branch will pick it up automatically.
            return Employee.query.get(int(user_id.split("-", 1)[1]))
        return None

    # --- register blueprints ---
    from app.admin.routes import admin_bp
    from app.payroll.routes import payroll_bp

    app.register_blueprint(admin_bp)
    app.register_blueprint(payroll_bp)

    with app.app_context():
        db.create_all()

    return app
