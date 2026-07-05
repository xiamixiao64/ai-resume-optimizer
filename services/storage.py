"""Storage service - Supabase REST API (no httpcore dependency)"""
import os
import uuid
import datetime
import logging
from typing import Optional, Tuple
from urllib.parse import quote
import requests as http_requests
from flask import session

logger = logging.getLogger(__name__)

# Supabase REST API config
supabase_url = None
supabase_key = None

# In-memory fallbacks
_memory_users = {}
_events = []
_history = []

# Config
FREE_OPTIMIZATIONS = 5

import bcrypt


def init_supabase():
    """Initialize Supabase REST API credentials from env vars"""
    global supabase_url, supabase_key
    supabase_url = os.environ.get('SUPABASE_URL', '')
    supabase_key = os.environ.get('SUPABASE_KEY', '')
    if supabase_url and supabase_key:
        logger.info(f"Supabase configured: {supabase_url}")
    else:
        logger.warning("Supabase not configured. Using in-memory storage.")
    return None


def _supabase_request(method, table, data=None, filters=None):
    """Make a request to Supabase REST API"""
    if not supabase_url or not supabase_key:
        return None

    url = f"{supabase_url}/rest/v1/{table}"
    headers = {
        "apikey": supabase_key,
        "Authorization": f"Bearer {supabase_key}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }

    try:
        if method == "GET":
            if filters:
                for key, value in filters.items():
                    # URL-encode filter values to prevent injection
                    encoded_value = quote(str(value), safe='')
                    url += f"&{key}=eq.{encoded_value}" if "?" in url else f"?{key}=eq.{encoded_value}"
            resp = http_requests.get(url, headers=headers, timeout=10)
        elif method == "POST":
            resp = http_requests.post(url, headers=headers, json=data, timeout=10)
        elif method == "PATCH":
            if filters:
                for key, value in filters.items():
                    encoded_value = quote(str(value), safe='')
                    url += f"&{key}=eq.{encoded_value}" if "?" in url else f"?{key}=eq.{encoded_value}"
            resp = http_requests.patch(url, headers=headers, json=data, timeout=10)
        elif method == "DELETE":
            if filters:
                for key, value in filters.items():
                    encoded_value = quote(str(value), safe='')
                    url += f"&{key}=eq.{encoded_value}" if "?" in url else f"?{key}=eq.{encoded_value}"
            resp = http_requests.delete(url, headers=headers, timeout=10)
        else:
            return None

        if resp.status_code in [200, 201]:
            return resp.json()
        else:
            logger.error(f"Supabase API error: {resp.status_code} - {resp.text[:200]}")
            return None
    except Exception as e:
        logger.error(f"Supabase request failed: {e}")
        return None


def hash_password(password: str) -> str:
    """Hash password with bcrypt."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(stored, provided):
    """Verify password against stored bcrypt hash"""
    if not (stored.startswith('$2b$') or stored.startswith('$2a$')):
        logger.error("Invalid password hash format - only bcrypt supported")
        return False
    return bcrypt.checkpw(provided.encode(), stored.encode())


# ==================== User Management ====================

def get_user_by_id(user_id: str) -> Optional[dict]:
    """Get user by ID.

    Args:
        user_id: The unique user identifier.

    Returns:
        User dictionary, or None if not found.
    """
    if supabase_url and supabase_key:
        result = _supabase_request("GET", "users", filters={"id": user_id})
        if result and len(result) > 0:
            return result[0]
    return _memory_users.get(user_id)


def get_user_id() -> Optional[str]:
    """Get current logged-in user ID from session.

    Returns:
        User ID if logged in, None otherwise.
    """
    user_id = session.get('user_id')
    if user_id and get_user_by_id(user_id):
        return user_id
    return None


def register_user(email: str, password: str) -> Tuple[Optional[str], Optional[str]]:
    """Register new user.

    Args:
        email: User email address.
        password: User password.

    Returns:
        Tuple of (user_id, error_message). user_id is None if registration fails.
    """
    if supabase_url and supabase_key:
        existing = _supabase_request("GET", "users", filters={"email": email})
        if existing and len(existing) > 0:
            return None, "Email already registered"
        user_id = str(uuid.uuid4())
        _supabase_request("POST", "users", {
            'id': user_id, 'email': email, 'password': hash_password(password),
            'usage_count': 0, 'is_pro': False
        })
        return user_id, None
    else:
        for uid, u in _memory_users.items():
            if u['email'] == email:
                return None, "Email already registered"
        user_id = str(uuid.uuid4())
        _memory_users[user_id] = {
            'id': user_id, 'email': email, 'password': hash_password(password),
            'usage_count': 0, 'is_pro': False
        }
        return user_id, None


def login_user(email: str, password: str) -> Tuple[Optional[str], Optional[str]]:
    """Login user.

    Args:
        email: User email address.
        password: User password.

    Returns:
        Tuple of (user_id, error_message). user_id is None if login fails.
    """
    if supabase_url and supabase_key:
        result = _supabase_request("GET", "users", filters={"email": email})
        if not result or len(result) == 0:
            return None, "Invalid email or password"
        user = result[0]
        if not verify_password(user['password'], password):
            return None, "Invalid email or password"
        return user['id'], None
    else:
        for uid, u in _memory_users.items():
            if u['email'] == email:
                if verify_password(u['password'], password):
                    return uid, None
                return None, "Invalid email or password"
        return None, "Invalid email or password"


def get_user_usage(user_id: str) -> int:
    """Get user's optimization count.

    Args:
        user_id: The unique user identifier.

    Returns:
        Number of optimizations used.
    """
    if supabase_url and supabase_key:
        result = _supabase_request("GET", "users", filters={"id": user_id})
        if result and len(result) > 0:
            return result[0].get('usage_count', 0)
    return _memory_users.get(user_id, {}).get('usage_count', 0)


def is_pro_user(user_id: str) -> bool:
    """Check if user has pro subscription.

    Args:
        user_id: The unique user identifier.

    Returns:
        True if user has pro status, False otherwise.
    """
    if supabase_url and supabase_key:
        result = _supabase_request("GET", "users", filters={"id": user_id})
        if result and len(result) > 0:
            return result[0].get('is_pro', False)
    return _memory_users.get(user_id, {}).get('is_pro', False)


def increment_usage(user_id: str) -> None:
    """Increment user's usage count.

    Args:
        user_id: The unique user identifier.
    """
    current = get_user_usage(user_id)
    new_count = current + 1
    if supabase_url and supabase_key:
        _supabase_request("PATCH", "users", {'usage_count': new_count}, {"id": user_id})
    elif user_id in _memory_users:
        _memory_users[user_id]['usage_count'] = new_count


def check_usage_limit(user_id: Optional[str]) -> bool:
    """Check if user has exceeded free tier.

    Args:
        user_id: The unique user identifier, or None.

    Returns:
        True if user can use more optimizations, False otherwise.
    """
    if not user_id:
        return False
    if is_pro_user(user_id):
        return True
    return get_user_usage(user_id) < FREE_OPTIMIZATIONS


def check_and_increment_usage(user_id: Optional[str]) -> bool:
    """Atomically check usage limit and increment if allowed.

    Args:
        user_id: The unique user identifier, or None.

    Returns:
        True if usage was incremented, False if limit reached.
    """
    if not user_id:
        return False
    if is_pro_user(user_id):
        increment_usage(user_id)
        return True
    current = get_user_usage(user_id)
    if current >= FREE_OPTIMIZATIONS:
        return False
    increment_usage(user_id)
    return True


def set_pro_status(user_id: str, status: bool = True) -> None:
    """Set user's pro status.

    Args:
        user_id: The unique user identifier.
        status: True to enable pro, False to disable.
    """
    if supabase_url and supabase_key:
        _supabase_request("PATCH", "users", {'is_pro': status}, {"id": user_id})
    elif user_id in _memory_users:
        _memory_users[user_id]['is_pro'] = status


# ==================== Event Tracking ====================

def track_event(user_id: str, event_type: str, event_data: dict = None) -> None:
    """Track user event.

    Args:
        user_id: The unique user identifier.
        event_type: Type of event (e.g., 'page_view', 'optimize_start').
        event_data: Optional event metadata.
    """
    if supabase_url and supabase_key:
        _supabase_request("POST", "events", {
            'user_id': user_id, 'event_type': event_type,
            'event_data': event_data or {}
        })
    else:
        event = {
            'id': len(_events) + 1, 'user_id': user_id,
            'event_type': event_type, 'event_data': event_data or {},
            'created_at': datetime.datetime.now().isoformat()
        }
        _events.append(event)
        if len(_events) > 10000:
            _events[:] = _events[-10000:]


# ==================== History ====================

def save_history(record):
    """Save optimization record"""
    if supabase_url and supabase_key:
        _supabase_request("POST", "optimizations", record)
    _history.append(record)


def get_user_history(user_id, limit=50):
    """Get user's optimization history"""
    if supabase_url and supabase_key:
        result = _supabase_request("GET", "optimizations", filters={"user_id": user_id})
        if result:
            records = sorted(result, key=lambda x: x.get('created_at', ''), reverse=True)
            return records[:limit]
    records = [r for r in _history if r['user_id'] == user_id]
    records.sort(key=lambda x: x['created_at'], reverse=True)
    return records[:limit]


def get_history_record(record_id, user_id):
    """Get single history record"""
    if supabase_url and supabase_key:
        result = _supabase_request("GET", "optimizations", filters={"id": record_id, "user_id": user_id})
        if result and len(result) > 0:
            return result[0]
    return next((r for r in _history if r['id'] == record_id and r['user_id'] == user_id), None)


def delete_history_record(record_id, user_id):
    """Delete history record"""
    if supabase_url and supabase_key:
        _supabase_request("DELETE", "optimizations", filters={"id": record_id, "user_id": user_id})
    global _history
    _history = [r for r in _history if not (r['id'] == record_id and r['user_id'] == user_id)]


# ==================== Admin Stats ====================

def get_admin_stats():
    """Get admin dashboard statistics"""
    event_counts = {}
    daily = {}
    now = datetime.datetime.now()
    total_users = 0
    total_events = 0

    for i in range(7):
        day = (now - datetime.timedelta(days=i)).strftime('%Y-%m-%d')
        daily[day] = 0

    if supabase_url and supabase_key:
        users_result = _supabase_request("GET", "users")
        total_users = len(users_result) if users_result else 0
        week_ago = (now - datetime.timedelta(days=7)).isoformat()
        events_result = _supabase_request("GET", "events")
        for e in events_result or []:
            t = e.get('event_type', '')
            event_counts[t] = event_counts.get(t, 0) + 1
            total_events += 1
            try:
                day = e.get('created_at', '')[:10]
                if day in daily:
                    daily[day] += 1
            except Exception:
                pass
    else:
        total_users = len(_memory_users)
        for e in _events:
            t = e['event_type']
            event_counts[t] = event_counts.get(t, 0) + 1
            total_events += 1
            try:
                day = e['created_at'][:10]
                if day in daily:
                    daily[day] += 1
            except Exception:
                pass

    return {
        'total_users': total_users,
        'total_events': total_events,
        'event_counts': event_counts,
        'daily_events': daily,
        'free_optimizations': FREE_OPTIMIZATIONS
    }


# ==================== Job Application Tracking ====================

# In-memory storage for job applications
_job_applications = []


def save_job_application(application):
    """Save a job application record"""
    if supabase_url and supabase_key:
        _supabase_request("POST", "job_applications", application)
    _job_applications.append(application)


def get_user_job_applications(user_id, limit=100):
    """Get user's job applications"""
    if supabase_url and supabase_key:
        result = _supabase_request("GET", "job_applications", filters={"user_id": user_id})
        if result:
            records = sorted(result, key=lambda x: x.get('created_at', ''), reverse=True)
            return records[:limit]
    records = [r for r in _job_applications if r['user_id'] == user_id]
    records.sort(key=lambda x: x['created_at'], reverse=True)
    return records[:limit]


def get_job_application(application_id, user_id):
    """Get single job application"""
    if supabase_url and supabase_key:
        result = _supabase_request("GET", "job_applications", filters={"id": application_id, "user_id": user_id})
        if result and len(result) > 0:
            return result[0]
    return next((r for r in _job_applications if r['id'] == application_id and r['user_id'] == user_id), None)


def update_job_application(application_id, user_id, updates):
    """Update a job application"""
    if supabase_url and supabase_key:
        _supabase_request("PATCH", "job_applications", updates, {"id": application_id, "user_id": user_id})
    else:
        for app in _job_applications:
            if app['id'] == application_id and app['user_id'] == user_id:
                app.update(updates)
                break


def delete_job_application(application_id, user_id):
    """Delete a job application"""
    if supabase_url and supabase_key:
        _supabase_request("DELETE", "job_applications", filters={"id": application_id, "user_id": user_id})
    global _job_applications
    _job_applications = [r for r in _job_applications if not (r['id'] == application_id and r['user_id'] == user_id)]


def get_job_application_stats(user_id):
    """Get job application statistics"""
    apps = get_user_job_applications(user_id, limit=1000)
    
    stats = {
        'total': len(apps),
        'by_status': {},
        'response_rate': 0,
        'interview_rate': 0
    }
    
    responded = 0
    interviews = 0
    
    for app in apps:
        status = app.get('status', 'applied')
        stats['by_status'][status] = stats['by_status'].get(status, 0) + 1
        
        if status in ['responded', 'interview', 'offer', 'rejected']:
            responded += 1
        if status in ['interview', 'offer']:
            interviews += 1
    
    if stats['total'] > 0:
        stats['response_rate'] = round(responded / stats['total'] * 100, 1)
        stats['interview_rate'] = round(interviews / stats['total'] * 100, 1)
    
    return stats
