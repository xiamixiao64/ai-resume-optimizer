"""ResumeForge AI - Main Application"""
import os
import secrets
import datetime
import logging
from flask import Flask
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv

load_dotenv()

# App setup
app = Flask(__name__)

# Secret key: use env var or generate a random one (for development only)
secret_key = os.environ.get('FLASK_SECRET_KEY')
if not secret_key:
    if os.environ.get('FLASK_DEBUG', 'false').lower() == 'true':
        secret_key = secrets.token_hex(32)
        logger.warning("Using generated secret key - set FLASK_SECRET_KEY in production!")
    else:
        raise RuntimeError("FLASK_SECRET_KEY environment variable is required in production")

app.secret_key = secret_key

# Session security
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('FLASK_DEBUG', 'false').lower() != 'true'
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(days=7)

# Extensions
limiter = Limiter(get_remote_address, app=app, default_limits=["200 per day"])
logger = logging.getLogger(__name__)

# CSRF Protection - enabled in production, can be disabled for development
CSRF_ENABLED = os.environ.get('CSRF_ENABLED', 'true').lower() == 'true'
csrf = CSRFProtect(app) if CSRF_ENABLED else None
if not CSRF_ENABLED:
    logger.warning("CSRF protection is DISABLED - use only in development!")

# Initialize storage
from services.storage import init_supabase
init_supabase()

# Register blueprints
from routes.auth import auth_bp
from routes.optimize import optimize_bp
from routes.features import features_bp
from routes.admin import admin_bp
from routes.seo import seo_bp

app.register_blueprint(auth_bp)
app.register_blueprint(optimize_bp)
app.register_blueprint(features_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(seo_bp)

# CSRF exemptions for API endpoints (forms still protected)
if csrf:
    csrf.exempt(optimize_bp)
    csrf.exempt(features_bp)

# Apply rate limits to auth routes
app.view_functions['auth.login'] = limiter.limit("5 per minute")(app.view_functions['auth.login'])
app.view_functions['auth.register'] = limiter.limit("3 per minute")(app.view_functions['auth.register'])
app.view_functions['optimize.upload_file'] = limiter.limit("5 per minute")(app.view_functions['optimize.upload_file'])
app.view_functions['optimize.optimize'] = limiter.limit("10 per minute")(app.view_functions['optimize.optimize'])
app.view_functions['optimize.api_optimize'] = limiter.limit("20 per minute")(app.view_functions['optimize.api_optimize'])
app.view_functions['optimize.create_checkout'] = limiter.limit("5 per minute")(app.view_functions['optimize.create_checkout'])
app.view_functions['features.match_jobs'] = limiter.limit("10 per minute")(app.view_functions['features.match_jobs'])
app.view_functions['features.optimize_linkedin'] = limiter.limit("10 per minute")(app.view_functions['features.optimize_linkedin'])


@app.after_request
def set_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'

    # HSTS - only in production
    if os.environ.get('FLASK_DEBUG', 'false').lower() != 'true':
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'

    # CSP - strict policy
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "font-src 'self'; "
        "connect-src 'self'; "
        "frame-ancestors 'none'"
    )
    return response


if __name__ == '__main__':
    debug_mode = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=debug_mode, port=port)
