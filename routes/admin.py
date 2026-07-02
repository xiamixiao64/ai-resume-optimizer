"""Admin routes"""
import os
from flask import Blueprint, jsonify, render_template, session
from services.storage import get_user_by_id, get_admin_stats

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/admin')
def admin_dashboard():
    admin_email = os.environ.get('ADMIN_EMAIL', '')
    user = get_user_by_id(session.get('user_id'))
    if not user or user.get('email') != admin_email:
        return jsonify({'error': 'Unauthorized'}), 403
    return render_template('admin.html', user=user)


@admin_bp.route('/api/admin/stats')
def admin_stats():
    admin_email = os.environ.get('ADMIN_EMAIL', '')
    user = get_user_by_id(session.get('user_id'))
    if not user or user.get('email') != admin_email:
        return jsonify({'error': 'Unauthorized'}), 403
    return jsonify(get_admin_stats())
