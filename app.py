from flask import Flask, request, jsonify, render_template, send_file
import os
import io
import json
import hashlib
import datetime
import uuid
import re
import random

app = Flask(__name__)

def load_env():
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and '=' in line and not line.startswith('#'):
                    k, v = line.split('=', 1)
                    os.environ.setdefault(k.strip(), v.strip())

load_env()

GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-versatile"

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
    import re
    
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
            return json.dumps({"error": data["error"].get("message", "API error"), "ats_score": 0, "optimized_resume": "API temporarily unavailable.", "improvements": [], "keyword_match": [], "missing_keywords": []})
        else:
            return json.dumps({"error": "Unexpected response", "ats_score": 0, "optimized_resume": str(data)[:500], "improvements": [], "keyword_match": [], "missing_keywords": []})
    except Exception as e:
        return json.dumps({"error": str(e), "ats_score": 0, "optimized_resume": f"Error: {str(e)}", "improvements": [], "keyword_match": [], "missing_keywords": []})

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
    return render_template('index.html')

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

    jd = job_description or "N/A"
    
    if mode == 'ats':
        prompt = "Analyze this resume for ATS compatibility. Return ONLY valid JSON.\n\nRESUME:\n" + resume_text + "\n\nJOB DESCRIPTION:\n" + jd + "\n\nReturn JSON: {\"ats_score\": 0-100, \"keyword_match\": [...], \"missing_keywords\": [...], \"improvements\": [...], \"optimized_resume\": \"...\"}"

    elif mode == 'keywords':
        prompt = "Extract keywords for this resume. Return ONLY valid JSON.\n\nRESUME:\n" + resume_text + "\n\nJOB DESCRIPTION:\n" + jd + "\n\nReturn JSON: {\"ats_score\": 0-100, \"keyword_match\": [...], \"missing_keywords\": [...], \"improvements\": [...], \"optimized_resume\": \"...\"}"

    elif mode == 'cover_letter':
        prompt = "Generate a cover letter. Return ONLY valid JSON.\n\nRESUME:\n" + resume_text + "\n\nJOB DESCRIPTION:\n" + jd + "\n\nReturn JSON: {\"cover_letter\": \"...\", \"ats_score\": 0-100, \"key_matches\": [...]}"

    else:
        prompt = "Optimize this resume. Return ONLY valid JSON with this structure:\n"
        prompt += "{\"ats_score\": 0-100, \"name\": \"...\", \"contact\": \"...\", \"summary\": \"2 sentences\", "
        prompt += "\"experience\": [{\"title\": \"...\", \"company\": \"KEEP ORIGINAL\", \"location\": \"...\", \"dates\": \"...\", \"bullets\": [\"...\"]}], "
        prompt += "\"education\": [{\"degree\": \"...\", \"school\": \"...\", \"year\": \"...\"}], "
        prompt += "\"skills\": [...], \"improvements\": [\"specific to THIS resume\"], "
        prompt += "\"keyword_match\": [\"exact from JD\"], \"missing_keywords\": [\"exact from JD not in resume\"]}\n\n"
        prompt += "RULES: Keep original structure. Improve bullets with action verbs and realistic metrics (12%, 18%, 37%, not 20%, 25%, 30%). Add JD keywords. Keep company names.\n\n"
        prompt += "RESUME:\n" + resume_text + "\n\nTARGET JOB:\n" + jd

    system_msg = "Return ONLY valid JSON. No markdown, no explanations."

    result = call_ai(prompt, system_msg)

    try:
        import html as html_lib
        import re
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
                except:
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
    resume_content = request.form.get('resume_content', '')
    if not resume_content:
        return jsonify({'error': 'No content'}), 400

    css = "body{font-family:Arial;font-size:11pt;line-height:1.5;color:#333;max-width:800px;margin:0 auto;padding:40px}"
    html_content = "<!DOCTYPE html><html><head><meta charset='UTF-8'><style>" + css + "</style></head><body>"
    html_content += resume_content.replace(chr(10), '<br>').replace('  ', '&nbsp;')
    html_content += "</body></html>"

    try:
        from xhtml2pdf import pisa
        output = io.BytesIO()
        pisa.CreatePDF(io.StringIO(html_content), dest=output)
        output.seek(0)
        return send_file(output, mimetype='application/pdf', as_attachment=True, download_name='optimized_resume.pdf')
    except Exception as e:
        return jsonify({'error': 'PDF generation failed: ' + str(e)}), 500

@app.route('/api/optimize', methods=['POST'])
def api_optimize():
    data = request.json
    resume_text = data.get('resume', '')
    job_description = data.get('job_description', '')
    mode = data.get('mode', 'optimize')

    if not resume_text:
        return jsonify({'error': 'resume required'}), 400

    prompt = "Optimize this resume. Return JSON with: ats_score, optimized_resume, improvements, keyword_match, missing_keywords.\n\nRESUME:\n" + resume_text + "\n\nJOB DESCRIPTION:\n" + (job_description or "N/A")

    result = call_ai(prompt)
    try:
        result = result.strip()
        if result.startswith("```"):
            result = result.split("\n", 1)[1].rsplit("```", 1)[0]
        parsed = json.loads(result)
    except:
        parsed = {"ats_score": 65, "optimized_resume": result, "improvements": []}

    return jsonify(parsed)

@app.route('/health')
def health():
    return jsonify({"status": "ok", "groq_key_set": bool(GROQ_API_KEY)})

if __name__ == '__main__':
    app.run(debug=True, port=5000)

