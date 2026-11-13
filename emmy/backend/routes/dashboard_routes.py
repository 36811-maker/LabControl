from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from backend.services.dashboard_service import get_dashboard_metrics

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
def index():
    if not current_user.is_authenticated:
        return redirect(url_for("auth.login"))

    metrics = get_dashboard_metrics(current_user)
    return render_template("dashboard.html", metrics=metrics)
