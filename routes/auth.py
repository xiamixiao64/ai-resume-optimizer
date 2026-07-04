"""Authentication routes"""
from flask import Blueprint, request, render_template, redirect, url_for, session
from services.storage import login_user, register_user

auth_bp = Blueprint('auth', __name__)

# In-memory IP tracking for rate limiting
_ip_registrations = {}


def check_ip_registration_limit(ip):
    """Check if IP has exceeded registration limit (3 per day)"""
    import datetime
    now = datetime.datetime.now()
    today = now.strftime('%Y-%m-%d')

    if ip not in _ip_registrations:
        _ip_registrations[ip] = []

    # Remove old entries (older than 24 hours)
    _ip_registrations[ip] = [
        t for t in _ip_registrations[ip]
        if (now - t).total_seconds() < 86400
    ]

    # Check limit
    if len(_ip_registrations[ip]) >= 3:
        return False

    # Record this registration
    _ip_registrations[ip].append(now)
    return True


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

        # Check IP rate limit
        ip = request.remote_addr
        if not check_ip_registration_limit(ip):
            return render_template('register.html', error='Registration limit reached. Please try again later.')

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
