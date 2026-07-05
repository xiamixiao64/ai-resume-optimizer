"""
Integration tests for ResumeForge AI API endpoints
"""
import pytest
import json
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app


@pytest.fixture
def client():
    """Create test client"""
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing
    with app.test_client() as client:
        yield client


@pytest.fixture
def logged_in_client(client):
    """Create logged-in test client"""
    import uuid
    unique_email = f'test_{uuid.uuid4().hex[:8]}@example.com'
    
    # Register user with valid password (uppercase, lowercase, number, 8+ chars)
    resp = client.post('/register', data={
        'email': unique_email,
        'password': 'TestPass123'
    }, follow_redirects=False)
    
    # Login user
    resp = client.post('/login', data={
        'email': unique_email,
        'password': 'TestPass123'
    }, follow_redirects=False)
    
    return client


class TestHealthEndpoint:
    """Test health check endpoint"""

    def test_health_returns_200(self, client):
        """Health endpoint should return 200"""
        response = client.get('/health')
        assert response.status_code == 200

    def test_health_returns_json(self, client):
        """Health endpoint should return JSON"""
        response = client.get('/health')
        data = json.loads(response.data)
        assert 'status' in data
        assert data['status'] == 'ok'


class TestATSDetector:
    """Test ATS type detection"""

    def test_ats_detector_page_loads(self, client):
        """ATS detector page should load"""
        response = client.get('/ats-detector')
        assert response.status_code == 200

    def test_detect_workday(self, client):
        """Should detect Workday ATS"""
        response = client.post('/api/ats/detect',
            data=json.dumps({'job_description': 'Apply via Workday at company.wd5.myworkdayjobs.com'}),
            content_type='application/json')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['detected']['type'] == 'workday'

    def test_detect_greenhouse(self, client):
        """Should detect Greenhouse ATS"""
        response = client.post('/api/ats/detect',
            data=json.dumps({'job_description': 'Submit via Greenhouse: boards.greenhouse.io/company'}),
            content_type='application/json')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['detected']['type'] == 'greenhouse'

    def test_detect_taleo(self, client):
        """Should detect Taleo ATS"""
        response = client.post('/api/ats/detect',
            data=json.dumps({'job_description': 'Apply on Taleo: oracle.com/taleo/company'}),
            content_type='application/json')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['detected']['type'] == 'taleo'

    def test_detect_lever(self, client):
        """Should detect Lever ATS"""
        response = client.post('/api/ats/detect',
            data=json.dumps({'job_description': 'Submit through lever.co/jobs/company'}),
            content_type='application/json')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['detected']['type'] == 'lever'

    def test_detect_unknown(self, client):
        """Should return unknown for unrecognized ATS"""
        response = client.post('/api/ats/detect',
            data=json.dumps({'job_description': 'No specific ATS mentioned'}),
            content_type='application/json')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['detected']['type'] == 'unknown'

    def test_detect_empty_input(self, client):
        """Should return error for empty input"""
        response = client.post('/api/ats/detect',
            data=json.dumps({}),
            content_type='application/json')
        assert response.status_code == 400

    def test_detect_returns_tips(self, client):
        """Should return optimization tips"""
        response = client.post('/api/ats/detect',
            data=json.dumps({'job_description': 'Apply via Workday'}),
            content_type='application/json')
        data = json.loads(response.data)
        assert 'tips' in data
        assert len(data['tips']) > 0


class TestPricingPage:
    """Test pricing page"""

    def test_pricing_page_loads(self, client):
        """Pricing page should load"""
        response = client.get('/pricing')
        assert response.status_code == 200

    def test_pricing_contains_plans(self, client):
        """Pricing page should contain plan options"""
        response = client.get('/pricing')
        assert b'Free' in response.data
        assert b'Pro' in response.data
        assert b'Lifetime' in response.data


class TestHomepage:
    """Test homepage"""

    def test_homepage_redirects_when_not_logged_in(self, client):
        """Homepage should redirect to register when not logged in"""
        response = client.get('/')
        assert response.status_code == 302

    def test_homepage_loads_when_logged_in(self, logged_in_client):
        """Homepage should load when logged in"""
        response = logged_in_client.get('/')
        assert response.status_code == 200

    def test_homepage_contains_features(self, logged_in_client):
        """Homepage should list all features"""
        response = logged_in_client.get('/')
        assert b'ATS Score' in response.data
        assert b'ATS Type Detector' in response.data
        assert b'Interview' in response.data
        assert b'Salary' in response.data


class TestJobTracker:
    """Test job application tracker"""

    def test_tracker_requires_login(self, client):
        """Tracker should require login"""
        response = client.get('/tracker')
        assert response.status_code == 302

    def test_add_application_requires_auth(self, client):
        """Adding application should require authentication"""
        response = client.post('/api/tracker/applications',
            data=json.dumps({
                'company': 'Google',
                'position': 'Software Engineer'
            }),
            content_type='application/json')
        assert response.status_code == 401

    def test_get_applications_requires_auth(self, client):
        """Getting applications should require authentication"""
        response = client.get('/api/tracker/applications')
        assert response.status_code == 401

    def test_get_stats_requires_auth(self, client):
        """Getting stats should require authentication"""
        response = client.get('/api/tracker/stats')
        assert response.status_code == 401


class TestEventTracking:
    """Test event tracking"""

    def test_track_event(self, client):
        """Should track events"""
        response = client.post('/api/track',
            data=json.dumps({
                'event_type': 'page_view',
                'event_data': {'page': 'home'}
            }),
            content_type='application/json')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'ok'


class TestModeAnalytics:
    """Test analytics endpoint"""

    def test_get_mode_analytics_requires_auth(self, client):
        """Getting analytics should require authentication"""
        response = client.get('/api/analytics/modes')
        assert response.status_code == 401


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
