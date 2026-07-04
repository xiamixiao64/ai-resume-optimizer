import requests
import re

base_url = 'https://ai-resume-optimizerai-resume-optimizer.onrender.com'

print('=== Testing Live Application ===')
print()

# Create session
session = requests.Session()

# Test pages
pages = ['/health', '/register', '/login', '/ats-detector', '/pricing', '/tutorial']
for page in pages:
    try:
        resp = session.get(f'{base_url}{page}', timeout=30)
        print(f'{page}: {resp.status_code}')
    except Exception as e:
        print(f'{page}: ERROR - {e}')

print()
print('=== Registration Test ===')

# Get register page
resp = session.get(f'{base_url}/register', timeout=30)
print('Register page:', resp.status_code)

# Get CSRF token
csrf_match = re.search(r'csrf_token.*?value="([^"]+)"', resp.text)
csrf_token = csrf_match.group(1) if csrf_match else ''
print('CSRF token found:', bool(csrf_token))

if csrf_token:
    # Try to register
    resp = session.post(f'{base_url}/register', data={
        'email': 'testuser2026@gmail.com',
        'password': 'TestPass123!',
        'csrf_token': csrf_token
    }, timeout=30)
    print('Register response:', resp.status_code)
    
    # Check for error message
    error_match = re.search(r'class="error"[^>]*>(.*?)</div>', resp.text)
    if error_match:
        print('Error:', error_match.group(1))
    else:
        print('No error message found')

print()
print('=== Login Test ===')

# Get login page
resp = session.get(f'{base_url}/login', timeout=30)
print('Login page:', resp.status_code)

# Get CSRF token
csrf_match = re.search(r'csrf_token.*?value="([^"]+)"', resp.text)
csrf_token = csrf_match.group(1) if csrf_match else ''
print('CSRF token found:', bool(csrf_token))

if csrf_token:
    # Try to login
    resp = session.post(f'{base_url}/login', data={
        'email': 'testuser2026@gmail.com',
        'password': 'TestPass123!',
        'csrf_token': csrf_token
    }, timeout=30)
    print('Login response:', resp.status_code)
    
    # Check for error message
    error_match = re.search(r'class="error"[^>]*>(.*?)</div>', resp.text)
    if error_match:
        print('Error:', error_match.group(1))
    else:
        print('No error message found')

print()
print('=== Test Complete ===')
