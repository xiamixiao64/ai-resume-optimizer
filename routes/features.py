"""Feature routes - Jobs, LinkedIn, Templates, Batch, History"""
import random
import logging
from flask import Blueprint, request, jsonify, render_template, session, redirect, url_for
from services.ai import call_ai, parse_ai_json
from services.storage import (
    get_user_by_id, get_user_id, check_usage_limit, increment_usage,
    track_event, save_history, get_user_history, get_history_record, delete_history_record
)

logger = logging.getLogger(__name__)
features_bp = Blueprint('features', __name__)

# ==================== A/B Testing ====================

_ab_tests = {
    'cta_button': {'variants': {'A': 'Optimize My Resume — It\'s Free', 'B': 'Get Your ATS Score — Free'}},
    'hero_heading': {'variants': {'A': 'Beat ATS Systems.<br>Land More Interviews.', 'B': 'Your Resume vs. The ATS.<br>Who Wins?'}}
}


def get_ab_variant(test_name):
    session_key = f'ab_{test_name}'
    if session_key in session:
        return session[session_key]
    if test_name not in _ab_tests:
        return 'A'
    variant = random.choice(list(_ab_tests[test_name]['variants'].keys()))
    session[session_key] = variant
    user_id = get_user_id()
    if user_id:
        track_event(user_id, 'ab_assign', {'test': test_name, 'variant': variant})
    return variant


# ==================== Jobs ====================

@features_bp.route('/jobs')
def jobs_page():
    user = get_user_by_id(session.get('user_id'))
    if not user:
        return redirect(url_for('auth.register'))
    return render_template('jobs.html', user=user)


@features_bp.route('/api/jobs/match', methods=['POST'])
def match_jobs():
    user_id = get_user_id()
    if not user_id:
        return jsonify({'error': 'Please register/login first'}), 401
    if not check_usage_limit(user_id):
        return jsonify({'error': 'Free limit reached. Please upgrade to Pro.'}), 403
    resume_text = request.form.get('resume_text', '')
    if not resume_text:
        return jsonify({'error': 'Please paste your resume'}), 400
    increment_usage(user_id)
    prompt = f"""Based on this resume, suggest 6-8 matching job roles. For each role, provide a match score and key skills.

RESUME:
{resume_text}

Return strict JSON (no other text):
{{
  "jobs": [
    {{
      "title": "Job Title",
      "company_type": "Company Type (e.g., Tech Startup, Enterprise, Agency)",
      "match_score": 85,
      "matched_skills": ["Python", "React"],
      "missing_skills": ["Kubernetes"],
      "salary_range": "$80K-$120K",
      "description": "Brief role description (1-2 sentences)"
    }}
  ]
}}

Rules:
1. Suggest realistic job titles that match the resume's experience level
2. Match score should reflect actual skill overlap (50-95 range)
3. Include both matched and missing skills for each role
4. Keep descriptions concise
5. Sort by match_score descending"""
    data = parse_ai_json(call_ai(prompt, "You are a career advisor. Return strict JSON only, no markdown."))
    return jsonify(data if data else {"jobs": []})


# ==================== LinkedIn ====================

@features_bp.route('/linkedin')
def linkedin_page():
    user = get_user_by_id(session.get('user_id'))
    if not user:
        return redirect(url_for('auth.register'))
    return render_template('linkedin.html', user=user)


@features_bp.route('/api/linkedin/optimize', methods=['POST'])
def optimize_linkedin():
    user_id = get_user_id()
    if not user_id:
        return jsonify({'error': 'Please register/login first'}), 401
    if not check_usage_limit(user_id):
        return jsonify({'error': 'Free limit reached. Please upgrade to Pro.'}), 403
    profile_text = request.form.get('profile_text', '')
    target_role = request.form.get('target_role', '')
    if not profile_text:
        return jsonify({'error': 'Please paste your LinkedIn profile'}), 400
    increment_usage(user_id)
    track_event(user_id, 'linkedin_optimize', {'has_target_role': bool(target_role)})
    prompt = f"""Optimize this LinkedIn profile for better visibility and recruiter engagement.

LINKEDIN PROFILE:
{profile_text}

TARGET ROLE: {target_role or 'Not specified'}

LinkedIn is different from resumes:
- Headline: Include keywords but also be compelling (max 220 chars)
- About: Conversational tone, tell your story, include CTA (max 2600 chars)
- Experience: Concise bullets, focus on impact, use first person
- Skills: Match target role keywords, prioritize top 3

Return strict JSON (no other text):
{{
  "headline": "Optimized headline (max 220 chars)",
  "about": "Optimized About section (2-3 paragraphs, conversational)",
  "experience": [
    {{
      "title": "Job Title",
      "company": "Company Name",
      "optimized_bullets": ["Concise impact bullet 1", "Bullet 2"]
    }}
  ],
  "skills_suggestion": ["Skill 1", "Skill 2", "Skill 3"],
  "improvements": ["General improvement tip 1", "Tip 2"],
  "keywords_to_add": ["keyword1", "keyword2"]
}}

Rules:
1. Keep original experience and company names
2. Make About section conversational, not robotic
3. Headline should be keyword-rich but human-readable
4. Skills should match the target role if provided
5. Don't fabricate experience"""
    data = parse_ai_json(call_ai(prompt, "You are a LinkedIn optimization expert. Return strict JSON only."))
    return jsonify(data if data else {})


# ==================== Templates ====================

@features_bp.route('/templates')
def templates_page():
    user = get_user_by_id(session.get('user_id'))
    if not user:
        return redirect(url_for('auth.register'))
    return render_template('templates_page.html', user=user)


# ==================== Batch ====================

@features_bp.route('/batch')
def batch_page():
    user = get_user_by_id(session.get('user_id'))
    if not user:
        return redirect(url_for('auth.register'))
    return render_template('batch.html', user=user)


# ==================== History ====================

@features_bp.route('/history')
def history_page():
    user = get_user_by_id(session.get('user_id'))
    if not user:
        return redirect(url_for('auth.register'))
    return render_template('history.html', user=user)


@features_bp.route('/api/history', methods=['GET'])
def get_history():
    user_id = get_user_id()
    if not user_id:
        return jsonify({'error': 'Not logged in'}), 401
    records = get_user_history(user_id)
    return jsonify({'records': records})


@features_bp.route('/api/history/<record_id>', methods=['GET', 'DELETE'])
def history_record(record_id):
    user_id = get_user_id()
    if not user_id:
        return jsonify({'error': 'Not logged in'}), 401
    if request.method == 'DELETE':
        delete_history_record(record_id, user_id)
        track_event(user_id, 'history_delete', {'record_id': record_id})
        return jsonify({'status': 'ok'})
    record = get_history_record(record_id, user_id)
    if not record:
        return jsonify({'error': 'Not found'}), 404
    return jsonify(record)


# ==================== A/B Convert ====================

@features_bp.route('/api/ab/convert', methods=['POST'])
def ab_convert():
    test_name = request.form.get('test', '')
    variant = get_ab_variant(test_name)
    user_id = get_user_id()
    if user_id:
        track_event(user_id, 'ab_convert', {'test': test_name, 'variant': variant})
    return jsonify({'status': 'ok'})


# ==================== Feedback ====================

@features_bp.route('/api/feedback', methods=['POST'])
def submit_feedback():
    """Submit user feedback"""
    data = request.json
    feedback = data.get('feedback', '')
    page = data.get('page', '')
    score = data.get('score', '')

    if not feedback:
        return jsonify({'error': 'Feedback text required'}), 400

    user_id = get_user_id()
    track_event(user_id or 'anonymous', 'feedback', {
        'page': page,
        'score': score,
        'feedback_length': len(feedback)
    })

    # In production, save to database or send to email
    logger.info(f"Feedback received: {feedback[:100]}... (page={page}, score={score})")

    return jsonify({'status': 'ok', 'message': 'Thank you for your feedback!'})


# ==================== ATS Detector ====================

@features_bp.route('/ats-detector')
def ats_detector_page():
    """ATS Type Detector - Detect which ATS system a job posting uses"""
    user = get_user_by_id(session.get('user_id'))
    return render_template('ats_detector.html', user=user)


@features_bp.route('/api/ats/detect', methods=['POST'])
def detect_ats():
    """Detect ATS type from job description URL or text"""
    data = request.json
    job_description = data.get('job_description', '')
    job_url = data.get('job_url', '')

    if not job_description and not job_url:
        return jsonify({'error': 'Please provide job description text or URL'}), 400

    # Import ATSEngine for ATS detection
    from ats_engine import ATSEngine
    engine = ATSEngine()

    # If URL provided, try to fetch the job description
    if job_url and not job_description:
        try:
            import requests
            resp = requests.get(job_url, timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            if resp.status_code == 200:
                job_description = resp.text[:5000]  # Limit to 5000 chars
        except Exception as e:
            logger.error(f"Failed to fetch URL: {e}")
            return jsonify({'error': 'Failed to fetch job description from URL'}), 400

    # Detect ATS type
    ats_result = engine.identify_ats(job_description)

    # Get all supported ATS types for reference
    all_ats_types = []
    for ats_name, config in engine.ats_patterns.items():
        all_ats_types.append({
            'name': ats_name,
            'patterns': config['patterns'][:3],  # Show first 3 patterns
            'tips': config['tips']
        })

    # Track event
    user_id = get_user_id()
    if user_id:
        track_event(user_id, 'ats_detect', {
            'detected_type': ats_result['type'],
            'has_url': bool(job_url)
        })

    return jsonify({
        'detected': ats_result,
        'all_supported': all_ats_types,
        'tips': ats_result.get('tips', [])
    })


# ==================== Job Application Tracking ====================

@features_bp.route('/tracker')
def tracker_page():
    """Job Application Tracker page"""
    user = get_user_id()
    if not user:
        return redirect(url_for('auth.register'))
    
    from services.storage import get_user_job_applications, get_job_application_stats
    applications = get_user_job_applications(user)
    stats = get_job_application_stats(user)
    
    return render_template('tracker.html', user=get_user_by_id(user), applications=applications, stats=stats)


@features_bp.route('/api/tracker/applications', methods=['GET'])
def get_applications():
    """Get all job applications for current user"""
    user_id = get_user_id()
    if not user_id:
        return jsonify({'error': 'Not logged in'}), 401
    
    from services.storage import get_user_job_applications
    applications = get_user_job_applications(user_id)
    return jsonify({'applications': applications})


@features_bp.route('/api/tracker/applications', methods=['POST'])
def add_application():
    """Add a new job application"""
    user_id = get_user_id()
    if not user_id:
        return jsonify({'error': 'Not logged in'}), 401
    
    data = request.json
    company = data.get('company', '').strip()
    position = data.get('position', '').strip()
    job_url = data.get('job_url', '').strip()
    notes = data.get('notes', '').strip()
    
    if not company or not position:
        return jsonify({'error': 'Company and position are required'}), 400
    
    import uuid
    import datetime
    
    application = {
        'id': str(uuid.uuid4())[:8],
        'user_id': user_id,
        'company': company,
        'position': position,
        'job_url': job_url,
        'notes': notes,
        'status': 'applied',
        'ats_score': data.get('ats_score'),
        'created_at': datetime.datetime.now().isoformat(),
        'updated_at': datetime.datetime.now().isoformat()
    }
    
    from services.storage import save_job_application, track_event
    save_job_application(application)
    track_event(user_id, 'job_application_added', {'company': company, 'position': position})
    
    return jsonify({'application': application})


@features_bp.route('/api/tracker/applications/<application_id>', methods=['PUT'])
def update_application(application_id):
    """Update a job application"""
    user_id = get_user_id()
    if not user_id:
        return jsonify({'error': 'Not logged in'}), 401
    
    data = request.json
    updates = {}
    
    if 'status' in data:
        updates['status'] = data['status']
    if 'notes' in data:
        updates['notes'] = data['notes']
    if 'ats_score' in data:
        updates['ats_score'] = data['ats_score']
    
    import datetime
    updates['updated_at'] = datetime.datetime.now().isoformat()
    
    from services.storage import update_job_application, get_job_application
    app = get_job_application(application_id, user_id)
    if not app:
        return jsonify({'error': 'Application not found'}), 404
    
    update_job_application(application_id, user_id, updates)
    
    return jsonify({'status': 'ok'})


@features_bp.route('/api/tracker/applications/<application_id>', methods=['DELETE'])
def delete_application(application_id):
    """Delete a job application"""
    user_id = get_user_id()
    if not user_id:
        return jsonify({'error': 'Not logged in'}), 401
    
    from services.storage import delete_job_application, get_job_application
    app = get_job_application(application_id, user_id)
    if not app:
        return jsonify({'error': 'Application not found'}), 404
    
    delete_job_application(application_id, user_id)
    
    return jsonify({'status': 'ok'})


@features_bp.route('/api/tracker/stats', methods=['GET'])
def get_tracker_stats():
    """Get job application statistics"""
    user_id = get_user_id()
    if not user_id:
        return jsonify({'error': 'Not logged in'}), 401
    
    from services.storage import get_job_application_stats
    stats = get_job_application_stats(user_id)
    return jsonify(stats)
