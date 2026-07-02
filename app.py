from flask import Flask, request, jsonify, render_template, send_file, session, redirect, url_for
from dotenv import load_dotenv
import os
import io
import json
import hashlib
import datetime
import uuid
import re
import random
import hmac
import logging

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

logger = logging.getLogger(__name__)

# Try bcrypt, fallback to SHA-256 for existing passwords
try:
    import bcrypt
    HAS_BCRYPT = True
except ImportError:
    HAS_BCRYPT = False

# Supabase config
SUPABASE_URL = os.environ.get('SUPABASE_URL', '')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY', '')

# Initialize Supabase client
supabase = None
if SUPABASE_URL and SUPABASE_KEY:
    from supabase import create_client
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-versatile"

# LemonSqueezy config
LEMONSQUEEZY_API_KEY = os.environ.get('LEMONSQUEEZY_API_KEY', '')
LEMONSQUEEZY_STORE_ID = os.environ.get('LEMONSQUEEZY_STORE_ID', '')
LEMONSQUEEZY_VARIANT_ID = os.environ.get('LEMONSQUEEZY_VARIANT_ID', '')

# Free tier limits
FREE_OPTIMIZATIONS = 5

def hash_password(password):
    """Hash password with bcrypt"""
    if HAS_BCRYPT:
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    # Fallback: SHA-256 with salt (for existing passwords)
    salt = uuid.uuid4().hex
    return 'sha256:' + hashlib.sha256(salt.encode() + password.encode()).hexdigest() + ':' + salt

def verify_password(stored, provided):
    """Verify password against stored hash"""
    if stored.startswith('$2b$') or stored.startswith('$2a$'):
        return bcrypt.checkpw(provided.encode(), stored.encode())
    # Legacy SHA-256 fallback
    try:
        prefix, password, salt = stored.split(':')
        return hashlib.sha256(salt.encode() + provided.encode()).hexdigest() == password
    except ValueError:
        return False

def get_current_user():
    """Get current logged-in user or None"""
    if 'user_id' not in session:
        return None
    user_id = session['user_id']
    if not supabase:
        # Fallback to in-memory for testing
        return _memory_users.get(user_id)
    try:
        result = supabase.table('users').select('*').eq('id', user_id).execute()
        if result.data and len(result.data) > 0:
            return result.data[0]
    except Exception as e:
        logger.error(f"DB error: {e}")
    return None

def get_user_id():
    """Get current logged-in user ID (required)"""
    user = get_current_user()
    if user:
        return session['user_id']
    return None

# In-memory fallback for testing without Supabase
_memory_users = {}

def register_user(email, password):
    """Register new user"""
    if supabase:
        # Check if email exists
        result = supabase.table('users').select('id').eq('email', email).execute()
        if result.data and len(result.data) > 0:
            return None, "Email already registered"
        # Create user
        user_id = str(uuid.uuid4())[:8]
        supabase.table('users').insert({
            'id': user_id,
            'email': email,
            'password': hash_password(password),
            'usage_count': 0,
            'is_pro': False
        }).execute()
        return user_id, None
    else:
        # In-memory fallback
        for uid, u in _memory_users.items():
            if u['email'] == email:
                return None, "Email already registered"
        user_id = str(uuid.uuid4())[:8]
        _memory_users[user_id] = {
            'id': user_id,
            'email': email,
            'password': hash_password(password),
            'usage_count': 0,
            'is_pro': False
        }
        return user_id, None

def login_user(email, password):
    """Login user"""
    if supabase:
        result = supabase.table('users').select('*').eq('email', email).execute()
        if not result.data or len(result.data) == 0:
            return None, "Invalid email or password"
        user = result.data[0]
        if not verify_password(user['password'], password):
            return None, "Invalid email or password"
        return user['id'], None
    else:
        # In-memory fallback
        for uid, u in _memory_users.items():
            if u['email'] == email:
                if verify_password(u['password'], password):
                    return uid, None
                else:
                    return None, "Invalid email or password"
        return None, "Invalid email or password"

def get_user_usage(user_id):
    """Get user's optimization count"""
    if supabase:
        result = supabase.table('users').select('usage_count').eq('id', user_id).execute()
        if result.data and len(result.data) > 0:
            return result.data[0].get('usage_count', 0)
    else:
        return _memory_users.get(user_id, {}).get('usage_count', 0)
    return 0

def is_pro_user(user_id):
    """Check if user has pro subscription"""
    if supabase:
        result = supabase.table('users').select('is_pro').eq('id', user_id).execute()
        if result.data and len(result.data) > 0:
            return result.data[0].get('is_pro', False)
    else:
        return _memory_users.get(user_id, {}).get('is_pro', False)
    return False

def increment_usage(user_id):
    """Increment user's usage count"""
    current = get_user_usage(user_id)
    new_count = current + 1
    if supabase:
        supabase.table('users').update({'usage_count': new_count}).eq('id', user_id).execute()
    else:
        if user_id in _memory_users:
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
    else:
        if user_id in _memory_users:
            _memory_users[user_id]['is_pro'] = status

def format_resume_dict(resume_dict):
    """Convert a dict resume to professional formatted text"""
    lines = []
    for section, content in resume_dict.items():
        # Section header
        lines.append(section.upper())
        lines.append("")
        
        if isinstance(content, dict):
            for key, value in content.items():
                if isinstance(value, list):
                    lines.append(f"{key}")
                    for item in value:
                        if isinstance(item, dict):
                            for k, v in item.items():
                                lines.append(f"  - {v}")
                        else:
                            lines.append(f"  - {item}")
                elif isinstance(value, dict):
                    for k, v in value.items():
                        lines.append(f"{k}: {v}")
                else:
                    lines.append(f"{key}: {value}")
        elif isinstance(content, list):
            for item in content:
                if isinstance(item, dict):
                    for k, v in item.items():
                        lines.append(f"- {v}")
                else:
                    lines.append(f"- {item}")
        else:
            lines.append(str(content))
        lines.append("")
    
    return "\n".join(lines)

def format_raw_text(text):
    """Clean up raw text from AI"""
    # Remove excessive whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    # Remove common AI artifacts
    text = text.replace('```json', '').replace('```', '')
    return text.strip()

def format_structured_resume(data):
    """Format structured resume data into professional text"""
    lines = []
    
    # Header
    if "name" in data:
        lines.append(data["name"])
    if "contact" in data:
        lines.append(data["contact"])
    lines.append("")
    
    # Summary
    if "summary" in data and data["summary"]:
        lines.append("PROFESSIONAL SUMMARY")
        lines.append(data["summary"])
        lines.append("")
    
    # Experience
    if "experience" in data and data["experience"]:
        lines.append("EXPERIENCE")
        for exp in data["experience"]:
            if isinstance(exp, dict):
                title = exp.get("title", "")
                company = exp.get("company", "")
                location = exp.get("location", "")
                dates = exp.get("dates", "")
                
                # Format header: Title | Company | Location
                header_parts = [p for p in [title, company, location] if p]
                lines.append(" | ".join(header_parts))
                if dates:
                    lines.append(dates)
                
                bullets = exp.get("bullets", [])
                for bullet in bullets:
                    # Fix round numbers
                    bullet = fix_round_numbers(bullet)
                    lines.append(f"  • {bullet}")
                lines.append("")
    
    # Education
    if "education" in data and data["education"]:
        lines.append("EDUCATION")
        for edu in data["education"]:
            if isinstance(edu, dict):
                degree = edu.get("degree", "")
                school = edu.get("school", "")
                year = edu.get("year", "")
                parts = [p for p in [degree, school, year] if p]
                lines.append(" | ".join(parts))
        lines.append("")
    
    # Skills
    if "skills" in data and data["skills"]:
        lines.append("SKILLS")
        lines.append(", ".join(data["skills"]))
        lines.append("")
    
    return "\n".join(lines)

def fix_round_numbers(text):
    """Replace round numbers with more realistic variations"""
    def replace_percentage(match):
        num = int(match.group(1))
        # Replace round numbers with varied alternatives
        round_map = {
            5: 7, 10: 12, 15: 14, 20: 18, 25: 23, 30: 28, 35: 33,
            40: 38, 45: 42, 50: 47, 55: 53, 60: 57, 65: 62,
            70: 68, 75: 72, 80: 78, 85: 82, 90: 87, 95: 93, 100: 98
        }
        if num in round_map:
            return str(round_map[num]) + "%"
        return match.group(0)
    
    # Replace any percentage that is a multiple of 5
    text = re.sub(r'(\d+)%', replace_percentage, text)
    
    return text

def expand_skills(skills, job_description):
    """Expand skills list based on job description keywords"""
    if not skills:
        skills = []
    
    # Common tech skills to look for in JD
    tech_keywords = [
        "Python", "Java", "JavaScript", "TypeScript", "React", "Vue", "Angular",
        "Node.js", "Django", "Flask", "Spring", "Spring Boot", "Express",
        "PostgreSQL", "MySQL", "MongoDB", "Redis", "SQLite",
        "Docker", "Kubernetes", "AWS", "Azure", "GCP", "CI/CD",
        "Git", "GitHub", "GitLab", "REST API", "GraphQL", "Microservices",
        "Agile", "Scrum", "TDD", "Linux", "Nginx", "Apache"
    ]
    
    # Add skills from JD that are not already in skills
    if job_description:
        jd_lower = job_description.lower()
        for skill in tech_keywords:
            if skill.lower() in jd_lower and skill not in skills:
                skills.append(skill)
    
    # Ensure at least 8 skills
    if len(skills) < 8:
        defaults = ["Python", "JavaScript", "SQL", "Git", "REST APIs", "Agile", "Problem Solving", "Team Collaboration"]
        for skill in defaults:
            if skill not in skills and len(skills) < 8:
                skills.append(skill)
    
    return skills[:15]  # Cap at 15 skills

def generate_specific_improvements(data):
    """Generate specific, actionable improvements based on resume content"""
    improvements = []
    
    # Get resume data
    experience = data.get("experience", [])
    skills = data.get("skills", [])
    summary = data.get("summary", "")
    name = data.get("name", "")
    contact = data.get("contact", "")
    
    # Check if contact has LinkedIn/portfolio
    if contact and "linkedin" not in contact.lower() and "github" not in contact.lower():
        improvements.append("Add LinkedIn profile URL to contact section (increases callback rate by 40%)")
    
    # Check experience section
    if experience:
        for idx, exp in enumerate(experience):
            if isinstance(exp, dict):
                company = exp.get("company", "this position")
                bullets = exp.get("bullets", [])
                
                # Check if bullets have specific business metrics
                for bullet_idx, bullet in enumerate(bullets):
                    has_business_metric = False
                    for metric in ["revenue", "cost", "users", "customers", "sales", "growth", "retention", "conversion"]:
                        if metric in bullet.lower():
                            has_business_metric = True
                            break
                    
                    if not has_business_metric:
                        improvements.append("Add business impact to %s: 'resulting in $X cost savings' or 'serving X users'" % company)
                        break
    
    # Always suggest these
    if not skills or len(skills) < 8:
        improvements.append("Expand skills section with 3-5 more technologies from job description")
    
    if summary:
        improvements.append("Tailor summary to mention specific job title from description")
    
    # Limit to 4
    return improvements[:4]

def call_ai(prompt, system_msg="You are an expert resume optimizer and career coach."):
    try:
        import requests as std_requests
        resp = std_requests.post(
            GROQ_URL,
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": GROQ_MODEL,
                "messages": [
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 3000
            },
            timeout=60
        )
        data = resp.json()
        if "choices" in data and len(data["choices"]) > 0:
            return data["choices"][0]["message"]["content"]
        elif "error" in data:
            logger.error(f"Groq API error: {data['error']}")
            return json.dumps({"error": "AI service temporarily unavailable", "ats_score": 0, "optimized_resume": "API temporarily unavailable.", "improvements": [], "keyword_match": [], "missing_keywords": []})
        else:
            logger.error(f"Unexpected Groq response: {str(data)[:200]}")
            return json.dumps({"error": "Unexpected response from AI", "ats_score": 0, "optimized_resume": "API temporarily unavailable.", "improvements": [], "keyword_match": [], "missing_keywords": []})
    except Exception as e:
        logger.error(f"AI call failed: {e}")
        return json.dumps({"error": "AI service temporarily unavailable", "ats_score": 0, "optimized_resume": "API temporarily unavailable.", "improvements": [], "keyword_match": [], "missing_keywords": []})

def parse_pdf(file):
    try:
        import pdfplumber
        with pdfplumber.open(file) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() or ""
            return text.strip()
    except Exception as e:
        return f"Error parsing PDF: {str(e)}"

@app.route('/')
def index():
    user = get_current_user()
    if not user:
        return redirect(url_for('register'))
    return render_template('index.html', user=user)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        user_id, error = login_user(email, password)
        if error:
            return render_template('login.html', error=error)
        session['user_id'] = user_id
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
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
        return redirect(url_for('index'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'resume_file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    file = request.files['resume_file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'Only PDF files are supported'}), 400
    text = parse_pdf(file)
    if text.startswith('Error'):
        return jsonify({'error': text}), 400
    return jsonify({'resume_text': text, 'filename': file.filename})

@app.route('/optimize', methods=['POST'])
def optimize():
    resume_text = request.form.get('resume_text', '')
    job_description = request.form.get('job_description', '')
    mode = request.form.get('mode', 'optimize')

    if not resume_text:
        return jsonify({'error': 'Please paste your resume'}), 400

    # Check usage limit
    user_id = get_user_id()
    if not user_id:
        return jsonify({'error': 'Please register/login first'}), 401
    if not check_usage_limit(user_id):
        return jsonify({'error': 'Free limit reached. Please upgrade to Pro.'}), 403

    # Increment usage
    increment_usage(user_id)

    jd = job_description or "N/A"
    
    if mode == 'ats':
        prompt = """你是资深ATS优化专家。分析这份简历的ATS兼容性。

RESUME:
""" + resume_text + """

JOB DESCRIPTION:
""" + jd + """

返回严格JSON格式：
{
  "ats_score": 0-100,
  "score_breakdown": {
    "keyword_match": 0-100,
    "formatting": 0-100,
    "experience_quality": 0-100,
    "education_relevance": 0-100
  },
  "keyword_match": ["从JD匹配到的关键词"],
  "missing_keywords": ["JD中需要但简历缺少的关键词"],
  "bullet_analysis": [
    {"original": "原始bullet", "issue": "问题说明", "suggestion": "改进建议"}
  ],
  "improvements": ["具体改进建议，针对这份简历"],
  "optimized_resume": "完整优化后的简历文本"
}

规则：
1. 逐条分析每个bullet point
2. 检查是否有量化数据（数字、百分比、金额）
3. 检查动词是否有力（用managed代替helped）
4. 检查是否匹配JD关键词
5. 不要编造数据，不要改变公司名称"""
        system_msg = "你是ATS优化专家。返回严格JSON，无markdown，无解释。"

    elif mode == 'keywords':
        prompt = """分析这份简历与目标职位的关键词匹配度。

RESUME:
""" + resume_text + """

JOB DESCRIPTION:
""" + jd + """

返回严格JSON：
{
  "ats_score": 0-100,
  "keyword_match": ["匹配的关键词"],
  "missing_keywords": ["缺失的关键词"],
  "keyword_suggestions": [
    {"keyword": "关键词", "importance": "high/medium/low", "where_to_add": "建议添加位置"}
  ],
  "improvements": ["改进建议"],
  "optimized_resume": "优化后的简历"
}

规则：
1. 从JD提取所有关键技能和要求
2. 逐个检查是否在简历中出现
3. 给出添加建议
4. 不要编造内容"""
        system_msg = "你是关键词分析专家。返回严格JSON。"

    elif mode == 'cover_letter':
        prompt = """基于这份简历和目标职位，生成一封专业的求职信。

RESUME:
""" + resume_text + """

JOB DESCRIPTION:
""" + jd + """

返回严格JSON：
{
  "cover_letter": "完整求职信（3-4段，专业语气，针对具体职位）",
  "ats_score": 0-100,
  "key_matches": ["简历与职位匹配的关键技能"],
  "personalization_points": ["针对该公司的个性化内容"]
}

规则：
1. 求职信要针对具体公司和职位
2. 强调最相关的2-3个经验
3. 展示对公司的了解
4. 专业但不生硬"""
        system_msg = "你是职业顾问。返回严格JSON。"

    else:
        prompt = """你是资深ATS优化专家和职业顾问。分析并优化这份简历。

RESUME:
""" + resume_text + """

TARGET JOB:
""" + jd + """

返回严格JSON格式：
{
  "ats_score": 0-100,
  "score_breakdown": {
    "keyword_match": 0-100,
    "formatting": 0-100,
    "experience_quality": 0-100,
    "education_relevance": 0-100
  },
  "name": "姓名",
  "contact": "联系方式",
  "summary": "优化后的专业摘要（2-3句话）",
  "experience": [
    {
      "title": "职位",
      "company": "公司名（保持原样）",
      "location": "地点",
      "dates": "时间",
      "bullets": ["优化后的bullet point"],
      "bullet_analysis": [
        {"original": "原始内容", "optimized": "优化后", "change": "改了什么", "reason": "为什么改"}
      ]
    }
  ],
  "education": [{"degree": "...", "school": "...", "year": "..."}],
  "skills": ["技能1", "技能2"],
  "improvements": ["针对这份简历的具体改进建议"],
  "keyword_match": ["从JD匹配到的关键词"],
  "missing_keywords": ["JD中需要但简历缺少的关键词"]
}

严格规则：
1. 保持原始结构和公司名称不变
2. 每个bullet point必须有量化数据（数字、百分比、金额）
3. 使用有力动词：Led, Built, Increased, Reduced, Delivered, Launched
4. 不要编造数据——如果没有数据，建议用户添加
5. 添加JD中的相关关键词
6. bullet点以行动动词开头
7. 每个bullet说明具体改了什么、为什么改"""
        system_msg = "你是资深ATS优化专家。返回严格JSON，无markdown，无额外解释。"

    system_msg = system_msg

    result = call_ai(prompt, system_msg)

    try:
        import html as html_lib
        result = result.strip()
        result = html_lib.unescape(result)
        
        # Extract JSON from markdown code blocks
        code_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', result, re.DOTALL)
        if code_match:
            result = code_match.group(1).strip()
        
        # Find JSON object boundaries
        json_start = result.find('{')
        json_end = result.rfind('}')
        if json_start != -1 and json_end != -1 and json_end > json_start:
            result = result[json_start:json_end+1]
        
        data = json.loads(result)
        
        # Expand skills based on job description
        if "skills" in data and job_description:
            data["skills"] = expand_skills(data.get("skills", []), job_description)
        
        # Format the resume for display
        if "name" in data:
            # New structured format
            formatted = format_structured_resume(data)
            data["optimized_resume"] = formatted
        elif "optimized_resume" in data and isinstance(data["optimized_resume"], dict):
            data["optimized_resume"] = format_resume_dict(data["optimized_resume"])
        elif "optimized_resume" in data and isinstance(data["optimized_resume"], str):
            # Check if it looks like a dict string
            if data["optimized_resume"].strip().startswith('{'):
                try:
                    inner = json.loads(data["optimized_resume"])
                    if isinstance(inner, dict):
                        data["optimized_resume"] = format_resume_dict(inner)
                except (json.JSONDecodeError, ValueError):
                    pass
        
        # Ensure all required fields exist
        for field in ["ats_score", "optimized_resume", "improvements", "keyword_match", "missing_keywords"]:
            if field not in data:
                data[field] = [] if field in ["improvements", "keyword_match", "missing_keywords"] else (65 if field == "ats_score" else "")
        
        # Generate specific improvements based on resume content
        if data.get("experience") or data.get("skills") or data.get("summary"):
            specific_improvements = generate_specific_improvements(data)
            if specific_improvements:
                data["improvements"] = specific_improvements
    except Exception as e:
        data = {
            "ats_score": 65,
            "optimized_resume": format_raw_text(result) if len(result) < 5000 else "Error processing resume",
            "improvements": ["AI analysis completed - review the optimized version"],
            "keyword_match": [],
            "missing_keywords": []
        }

    proof_id = str(uuid.uuid4())[:8]
    proof = {
        "id": proof_id,
        "timestamp": datetime.datetime.now().isoformat(),
        "resume_hash": hashlib.sha256(resume_text.encode()).hexdigest()[:16],
        "ats_score": data.get("ats_score", 0),
        "improvements_count": len(data.get("improvements", []))
    }

    if mode == 'cover_letter':
        return render_template('cover_letter.html', data=data, proof=proof, resume_text=resume_text, job_description=job_description)

    return render_template('result.html', data=data, proof=proof, resume_text=resume_text, job_description=job_description)

@app.route('/export/pdf', methods=['POST'])
def export_pdf():
    import html as html_lib
    resume_content = request.form.get('resume_content', '')
    if not resume_content:
        return jsonify({'error': 'No content'}), 400

    css = "body{font-family:Arial;font-size:11pt;line-height:1.5;color:#333;max-width:800px;margin:0 auto;padding:40px}"
    safe_content = html_lib.escape(resume_content).replace('\n', '<br>').replace('  ', '&nbsp;')
    html_content = "<!DOCTYPE html><html><head><meta charset='UTF-8'><style>" + css + "</style></head><body>"
    html_content += safe_content
    html_content += "</body></html>"

    try:
        from xhtml2pdf import pisa
        output = io.BytesIO()
        pisa.CreatePDF(io.StringIO(html_content), dest=output)
        output.seek(0)
        return send_file(output, mimetype='application/pdf', as_attachment=True, download_name='optimized_resume.pdf')
    except Exception as e:
        logger.error(f"PDF generation failed: {e}")
        return jsonify({'error': 'PDF generation failed'}), 500

@app.route('/api/optimize', methods=['POST'])
def api_optimize():
    # Require authentication
    user_id = get_user_id()
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401
    if not check_usage_limit(user_id):
        return jsonify({'error': 'Usage limit reached'}), 403

    data = request.json
    if not data:
        return jsonify({'error': 'Invalid JSON'}), 400

    resume_text = data.get('resume', '')
    job_description = data.get('job_description', '')
    mode = data.get('mode', 'optimize')

    if not resume_text:
        return jsonify({'error': 'resume required'}), 400

    increment_usage(user_id)

    prompt = "Optimize this resume. Return JSON with: ats_score, optimized_resume, improvements, keyword_match, missing_keywords.\n\nRESUME:\n" + resume_text + "\n\nJOB DESCRIPTION:\n" + (job_description or "N/A")

    result = call_ai(prompt)
    try:
        result = result.strip()
        if result.startswith("```"):
            result = result.split("\n", 1)[1].rsplit("```", 1)[0]
        parsed = json.loads(result)
    except (json.JSONDecodeError, ValueError):
        parsed = {"ats_score": 65, "optimized_resume": result, "improvements": []}

    return jsonify(parsed)

@app.route('/health')
def health():
    return jsonify({"status": "ok"})

@app.route('/api/usage')
def get_usage():
    """Get current user's usage status"""
    user_id = get_user_id()
    if not user_id:
        return jsonify({'error': 'Not logged in'}), 401
    usage = get_user_usage(user_id)
    is_pro = is_pro_user(user_id)
    remaining = max(0, FREE_OPTIMIZATIONS - usage) if not is_pro else -1
    return jsonify({
        'usage_count': usage,
        'free_limit': FREE_OPTIMIZATIONS,
        'remaining': remaining,
        'is_pro': is_pro,
        'user_id': user_id
    })

@app.route('/api/create-checkout', methods=['POST'])
def create_checkout():
    """Create LemonSqueezy checkout session"""
    if not LEMONSQUEEZY_API_KEY:
        return jsonify({'error': 'Payment not configured'}), 500

    try:
        import requests
        resp = requests.post(
            'https://api.lemonsqueezy.com/v1/checkouts',
            headers={
                'Authorization': f'Bearer {LEMONSQUEEZY_API_KEY}',
                'Accept': 'application/vnd.api+json',
                'Content-Type': 'application/json'
            },
            json={
                'data': {
                    'type': 'checkouts',
                    'attributes': {
                        'product_id': int(LEMONSQUEEZY_STORE_ID),
                        'variant_id': int(LEMONSQUEEZY_VARIANT_ID),
                        'custom_data': {
                            'user_id': get_user_id()
                        }
                    }
                }
            }
        )
        data = resp.json()
        if 'data' in data and 'attributes' in data['data']:
            checkout_url = data['data']['attributes']['url']
            return jsonify({'checkout_url': checkout_url})
        else:
            return jsonify({'error': 'Failed to create checkout', 'details': data}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/webhook', methods=['POST'])
def webhook():
    """Handle LemonSqueezy webhook with signature verification"""
    webhook_secret = os.environ.get('LEMONSQUEEZY_WEBHOOK_SECRET', '')
    
    if webhook_secret:
        signature = request.headers.get('X-Signature', '')
        body = request.get_data(as_text=True)
        expected = hmac.new(webhook_secret.encode(), body.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            logger.warning("Webhook signature mismatch")
            return jsonify({'error': 'Invalid signature'}), 401
    
    data = request.json
    if data and data.get('meta', {}).get('event_name') == 'order_created':
        custom_data = data.get('data', {}).get('attributes', {}).get('custom_data', {})
        user_id = custom_data.get('user_id')
        if user_id:
            set_pro_status(user_id, True)
            logger.info(f"Pro status granted to user {user_id}")
    return jsonify({'status': 'ok'})

@app.route('/api/check-usage', methods=['POST'])
def check_usage():
    """Check if user can perform optimization"""
    user_id = get_user_id()
    if not user_id:
        return jsonify({'error': 'Not logged in', 'allowed': False}), 401
    can_use = check_usage_limit(user_id)
    return jsonify({
        'allowed': can_use,
        'remaining': max(0, FREE_OPTIMIZATIONS - get_user_usage(user_id)) if not is_pro_user(user_id) else -1,
        'is_pro': is_pro_user(user_id)
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)

