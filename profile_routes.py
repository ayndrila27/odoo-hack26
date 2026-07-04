"""
Employee Profile blueprint: view, edit contact details, upload picture.
"""
import os
import uuid

from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, current_app
)
from werkzeug.utils import secure_filename

from datetime import datetime

from models import db, Payroll
from auth_utils import login_required, get_current_user, allowed_file

profile_bp = Blueprint("profile", __name__)


@profile_bp.route("/profile/payroll")
@login_required
def my_payroll():
    """Read-only payroll view for the logged-in employee (spec 3.6.1)."""
    user = get_current_user()
    month = int(request.args.get("month", datetime.utcnow().month))
    year = int(request.args.get("year", datetime.utcnow().year))

    payroll = Payroll.query.filter_by(user_id=user.id, month=month, year=year).first()
    history = (
        Payroll.query.filter_by(user_id=user.id)
        .order_by(Payroll.year.desc(), Payroll.month.desc())
        .limit(12)
        .all()
    )

    return render_template(
        "my_payroll.html", payroll=payroll, history=history, month=month, year=year
    )


@profile_bp.route("/profile")
@login_required
def profile():
    user = get_current_user()
    return render_template("profile.html", user=user)


@profile_bp.route("/profile/edit", methods=["GET", "POST"])
@login_required
def edit_profile():
    user = get_current_user()

    if request.method == "POST":
        phone = request.form.get("phone", "").strip()
        address = request.form.get("address", "").strip()

        if phone and (not phone.replace("+", "").replace(" ", "").isdigit() or len(phone) < 7):
            flash("Please enter a valid phone number.", "error")
            return render_template("edit_profile.html", user=user)

        user.phone = phone or None
        user.address = address or None
        db.session.commit()

        flash("Profile updated successfully.", "success")
        return redirect(url_for("profile.profile"))

    return render_template("edit_profile.html", user=user)


@profile_bp.route("/profile/upload-picture", methods=["POST"])
@login_required
def upload_picture():
    user = get_current_user()
    file = request.files.get("profile_pic")

    if not file or file.filename == "":
        flash("Please choose an image to upload.", "error")
        return redirect(url_for("profile.profile"))

    if not allowed_file(file.filename):
        flash("Only PNG, JPG, JPEG or GIF images are allowed.", "error")
        return redirect(url_for("profile.profile"))

    ext = secure_filename(file.filename).rsplit(".", 1)[1].lower()
    unique_name = f"user_{user.id}_{uuid.uuid4().hex[:8]}.{ext}"
    save_path = os.path.join(current_app.config["UPLOAD_FOLDER"], unique_name)
    file.save(save_path)

    user.profile_pic = unique_name
    db.session.commit()

    flash("Profile picture updated.", "success")
    return redirect(url_for("profile.profile"))
@profile_bp.route("/profile/remove-picture", methods=["POST"])
@login_required
def remove_picture():
    user = get_current_user()

    if user.profile_pic and user.profile_pic != "default.png":
        image_path = os.path.join(
            current_app.config["UPLOAD_FOLDER"],
            user.profile_pic
        )

        if os.path.exists(image_path):
            os.remove(image_path)

    user.profile_pic = "default.png"
    db.session.commit()

    flash("Profile photo removed successfully.", "success")
    return redirect(url_for("profile.profile"))