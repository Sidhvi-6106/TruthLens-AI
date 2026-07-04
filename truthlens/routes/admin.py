from flask import Blueprint, jsonify

from truthlens.services.admin_service import get_admin_metrics


admin_bp = Blueprint("admin", __name__)


@admin_bp.get("/metrics")
def metrics():
    return jsonify(get_admin_metrics())
