"""Authentication routes"""
from flask import Blueprint, request, render_template, redirect, url_for, session
from services.storage import login_user, register_user

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        user_id, error = login_user(email, password)
        if error:
            return render_template('login.html', error=error)
        session['user_id'] = user_id
        return redirect(url_for('optimize.index'))
    return render_template('login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        if not email or not password:
            return render_template('register.html', error='Email and password required')
        if len(password) < 6:
            return render_template('register.html', error='Password must be 6+ characters')
        user_id, error = register_user(email, password)
        if error:
            return render_template('register.html', error=error)
        session['user_id'] = user_id
        return redirect(url_for('optimize.index'))
    return render_template('register.html')


@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('optimize.index'))
