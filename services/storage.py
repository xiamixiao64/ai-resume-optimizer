"""Storage service - Supabase with in-memory fallback"""
import os
import uuid
import datetime
import logging
from flask import session

logger = logging.getLogger(__name__)

# Supabase client (initialized in app.py)
supabase = None

# In-memory fallbacks
_memory_users = {}
_events = []
_history = []

# Config
FREE_OPTIMIZATIONS = 5

import bcrypt


def init_supabase():
    """Initialize Supabase client from env vars"""
    global supabase
    url = os.environ.get('SUPABASE_URL', '')
    key = os.environ.get('SUPABASE_KEY', '')
    if url and key:
        from supabase import create_client
        supabase = create_client(url, key)
    return supabase


def hash_password(password):
    """Hash password with bcrypt. Raises RuntimeError if bcrypt unavailable."""
    if not HAS_BCRYPT:
        raise RuntimeError("bcrypt is required for password hashing. Install with: pip install bcrypt")
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(stored, provided):
    """Verify password against stored bcrypt hash"""
    if not (stored.startswith('$2b$') or stored.startswith('$2a$')):
        logger.error("Invalid password hash format - only bcrypt supported")
        return False
    return bcrypt.checkpw(provided.encode(), stored.encode())


# ==================== User Management ====================

def get_user_by_id(user_id):
    """Get user by ID"""
    if supabase:
        try:
            result = supabase.table('users').select('*').eq('id', user_id).execute()
            if result.data and len(result.data) > 0:
                return result.data[0]
        except Exception as e:
            logger.error(f"DB error: {e}")
    return _memory_users.get(user_id)


def get_user_id():
    """Get current logged-in user ID from session"""
    user_id = session.get('user_id')
    if user_id and get_user_by_id(user_id):
        return user_id
    return None


def register_user(email, password):
    """Register new user, returns (user_id, error)"""
    if supabase:
        result = supabase.table('users').select('id').eq('email', email).execute()
        if result.data and len(result.data) > 0:
            return None, "Email already registered"
        user_id = str(uuid.uuid4())
        supabase.table('users').insert({
            'id': user_id, 'email': email, 'password': hash_password(password),
            'usage_count': 0, 'is_pro': False
        }).execute()
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


def login_user(email, password):
    """Login user, returns (user_id, error)"""
    if supabase:
        result = supabase.table('users').select('*').eq('email', email).execute()
        if not result.data or len(result.data) == 0:
            return None, "Invalid email or password"
        user = result.data[0]
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


def get_user_usage(user_id):
    """Get user's optimization count"""
    if supabase:
        result = supabase.table('users').select('usage_count').eq('id', user_id).execute()
        if result.data and len(result.data) > 0:
            return result.data[0].get('usage_count', 0)
    return _memory_users.get(user_id, {}).get('usage_count', 0)


def is_pro_user(user_id):
    """Check if user has pro subscription"""
    if supabase:
        result = supabase.table('users').select('is_pro').eq('id', user_id).execute()
        if result.data and len(result.data) > 0:
            return result.data[0].get('is_pro', False)
    return _memory_users.get(user_id, {}).get('is_pro', False)


def increment_usage(user_id):
    """Increment user's usage count"""
    current = get_user_usage(user_id)
    new_count = current + 1
    if supabase:
        supabase.table('users').update({'usage_count': new_count}).eq('id', user_id).execute()
    elif user_id in _memory_users:
        _memory_users[user_id]['usage_count'] = new_count


def check_usage_limit(user_id):
    """Check if user has exceeded free tier"""
    if not user_id:
        return False
    if is_pro_user(user_id):
        return True
    return get_user_usage(user_id) < FREE_OPTIMIZATIONS


def set_pro_status(user_id, status=True):
    """Set user's pro status"""
    if supabase:
        supabase.table('users').update({'is_pro': status}).eq('id', user_id).execute()
    elif user_id in _memory_users:
        _memory_users[user_id]['is_pro'] = status


# ==================== Event Tracking ====================

def track_event(user_id, event_type, event_data=None):
    """Track user event"""
    if supabase:
        try:
            supabase.table('events').insert({
                'user_id': user_id, 'event_type': event_type,
                'event_data': event_data or {}
            }).execute()
        except Exception as e:
            logger.error(f"Event tracking failed: {e}")
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
    if supabase:
        try:
            supabase.table('optimizations').insert(record).execute()
        except Exception as e:
            logger.error(f"History save failed: {e}")
    _history.append(record)


def get_user_history(user_id, limit=50):
    """Get user's optimization history"""
    if supabase:
        try:
            result = supabase.table('optimizations').select('*').eq('user_id', user_id).order('created_at', desc=True).limit(limit).execute()
            return result.data
        except Exception as e:
            logger.error(f"History fetch failed: {e}")
    records = [r for r in _history if r['user_id'] == user_id]
    records.sort(key=lambda x: x['created_at'], reverse=True)
    return records[:limit]


def get_history_record(record_id, user_id):
    """Get single history record"""
    if supabase:
        try:
            result = supabase.table('optimizations').select('*').eq('id', record_id).eq('user_id', user_id).execute()
            if result.data:
                return result.data[0]
        except Exception as e:
            logger.error(f"History fetch failed: {e}")
    return next((r for r in _history if r['id'] == record_id and r['user_id'] == user_id), None)


def delete_history_record(record_id, user_id):
    """Delete history record"""
    if supabase:
        try:
            supabase.table('optimizations').delete().eq('id', record_id).eq('user_id', user_id).execute()
        except Exception as e:
            logger.error(f"History delete failed: {e}")
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

    if supabase:
        try:
            users_result = supabase.table('users').select('id', count='exact').execute()
            total_users = users_result.count or 0
            week_ago = (now - datetime.timedelta(days=7)).isoformat()
            events_result = supabase.table('events').select('event_type,created_at').gte('created_at', week_ago).execute()
            for e in events_result.data or []:
                t = e['event_type']
                event_counts[t] = event_counts.get(t, 0) + 1
                total_events += 1
                try:
                    day = e['created_at'][:10]
                    if day in daily:
                        daily[day] += 1
                except Exception:
                    pass
        except Exception as e:
            logger.error(f"Admin stats query failed: {e}")
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
    if supabase:
        try:
            supabase.table('job_applications').insert(application).execute()
        except Exception as e:
            logger.error(f"Job application save failed: {e}")
    _job_applications.append(application)


def get_user_job_applications(user_id, limit=100):
    """Get user's job applications"""
    if supabase:
        try:
            result = supabase.table('job_applications').select('*').eq('user_id', user_id).order('created_at', desc=True).limit(limit).execute()
            return result.data
        except Exception as e:
            logger.error(f"Job applications fetch failed: {e}")
    records = [r for r in _job_applications if r['user_id'] == user_id]
    records.sort(key=lambda x: x['created_at'], reverse=True)
    return records[:limit]


def get_job_application(application_id, user_id):
    """Get single job application"""
    if supabase:
        try:
            result = supabase.table('job_applications').select('*').eq('id', application_id).eq('user_id', user_id).execute()
            if result.data:
                return result.data[0]
        except Exception as e:
            logger.error(f"Job application fetch failed: {e}")
    return next((r for r in _job_applications if r['id'] == application_id and r['user_id'] == user_id), None)


def update_job_application(application_id, user_id, updates):
    """Update a job application"""
    if supabase:
        try:
            supabase.table('job_applications').update(updates).eq('id', application_id).eq('user_id', user_id).execute()
        except Exception as e:
            logger.error(f"Job application update failed: {e}")
    else:
        for app in _job_applications:
            if app['id'] == application_id and app['user_id'] == user_id:
                app.update(updates)
                break


def delete_job_application(application_id, user_id):
    """Delete a job application"""
    if supabase:
        try:
            supabase.table('job_applications').delete().eq('id', application_id).eq('user_id', user_id).execute()
        except Exception as e:
            logger.error(f"Job application delete failed: {e}")
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
