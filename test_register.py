import requests
import re

base_url = 'https://ai-resume-optimizerai-resume-optimizer.onrender.com'

# Get CSRF token from register page
print('=== Getting CSRF token ===')
session = requests.Session()
resp = session.get(f'{base_url}/register', timeout=30)
print('Register page status:', resp.status_code)

# Extract CSRF token
csrf_match = re.search(r'csrf_token.*?value="([^"]+)"', resp.text)
if csrf_match:
    csrf_token = csrf_match.group(1)
    print('CSRF token found:', csrf_token[:20] + '...')
    
    # Register with CSRF token
    print()
    print('=== Registering with CSRF token ===')
    resp = session.post(f'{base_url}/register', data={
        'email': 'testuser2026@gmail.com',
        'password': 'TestPass123!',
        'csrf_token': csrf_token
    }, allow_redirects=True, timeout=30)
    print('Register status:', resp.status_code)
    print('Final URL:', resp.url)
    
    # Login
    print()
    print('=== Getting login CSRF token ===')
    resp = session.get(f'{base_url}/login', timeout=30)
    csrf_match = re.search(r'csrf_token.*?value="([^"]+)"', resp.text)
    if csrf_match:
        csrf_token = csrf_match.group(1)
        print('CSRF token found:', csrf_token[:20] + '...')
        
        print()
        print('=== Logging in ===')
        resp = session.post(f'{base_url}/login', data={
            'email': 'testuser2026@gmail.com',
            'password': 'TestPass123!',
            'csrf_token': csrf_token
        }, allow_redirects=True, timeout=30)
        print('Login status:', resp.status_code)
        print('Final URL:', resp.url)
        
        # Test ATS Detector
        print()
        print('=== Testing ATS Detector ===')
        resp = session.get(f'{base_url}/ats-detector', timeout=30)
        print('ATS Detector:', resp.status_code)
        
        # Test Pricing
        resp = session.get(f'{base_url}/pricing', timeout=30)
        print('Pricing:', resp.status_code)
        
        # Test Tutorial
        resp = session.get(f'{base_url}/tutorial', timeout=30)
        print('Tutorial:', resp.status_code)
else:
    print('CSRF token not found')
    print('Page content preview:', resp.text[:500])
