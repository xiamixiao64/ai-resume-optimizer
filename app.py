"""ResumeForge AI - Main Application"""
import os
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
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(days=7)

# Extensions
limiter = Limiter(get_remote_address, app=app, default_limits=["200 per day"])
csrf = CSRFProtect(app)
logger = logging.getLogger(__name__)

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
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
    return response


if __name__ == '__main__':
    app.run(debug=True, port=5000)
