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
GROQ_MODEL = "llama-3.1-8b-instant"

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
    
    # Replace common round percentages
    replacements = {
        '50%': '47%', '25%': '23%', '30%': '28%', '20%': '18%',
        '100%': '98%', '75%': '72%', '40%': '38%', '60%': '57%',
        '95%': '93%', '80%': '78%', '10%': '12%', '5%': '7%',
        '15%': '14%', '35%': '33%', '45%': '42%', '55%': '53%',
        '65%': '62%', '70%': '68%', '85%': '82%', '90%': '87%',
    }
    
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    return text

def generate_specific_improvements(data):
    """Generate specific improvements based on resume content"""
    improvements = []
    
    # Check experience section
    if "experience" in data and data["experience"]:
        for i, exp in enumerate(data["experience]):
            if isinstance(exp, dict):
                bullets = exp.get("bullets", [])
                for j, bullet in enumerate(bullets):
                    # Check if bullet has metrics
                    if not any(c.isdigit() for c in bullet):
                        improvements.append(f"Add quantifiable metric to {exp.get('company', 'company')} bullet point {j+1}")
                    # Check if bullet starts with action verb
                    if not bullet[0].isupper():
                        improvements.append(f"Start bullet point with action verb in {exp.get('company', 'company')} section")
    
    # Check skills section
    if "skills" in data and data["skills"]:
        skills = data["skills"]
        if len(skills) < 5:
            improvements.append("Add more relevant technical skills to skills section")
    
    # Check summary
    if "summary" in data and data["summary"]:
        if len(data["summary"].split()) > 30:
            improvements.append("Shorten professional summary to 2 sentences max")
    
    # Limit to 4 most important
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

    if mode == 'ats':
        prompt = f"""Analyze this resume for ATS compatibility. Return ONLY valid JSON with double quotes.

RESUME:
{resume_text}

{("JOB DESCRIPTION: " + job_description) if job_description else ""}

Return this exact JSON:
{{
  "ats_score": <number 0-100>,
  "keyword_match": ["keyword1", "keyword2"],
  "missing_keywords": ["keyword1", "keyword2"],
  "improvements": ["improvement1", "improvement2"],
  "optimized_resume": "<clean formatted resume text>"
}}"""

    elif mode == 'keywords':
        prompt = f"""Extract and suggest keywords for this resume. Return ONLY valid JSON with double quotes.

RESUME:
{resume_text}

JOB DESCRIPTION:
{job_description or "N/A"}

Return this exact JSON:
{{
  "ats_score": <number 0-100>,
  "keyword_match": ["existing keyword1", "existing keyword2"],
  "missing_keywords": ["suggested keyword1", "suggested keyword2"],
  "improvements": ["suggestion1", "suggestion2"],
  "optimized_resume": "<clean formatted resume with keywords integrated>"
}}"""

    elif mode == 'cover_letter':
        prompt = f"""Generate a professional cover letter for this candidate applying to this job.

CANDIDATE RESUME:
{resume_text}

JOB DESCRIPTION:
{job_description or "N/A"}

Write a compelling 3-paragraph cover letter:
1. Opening: Hook with enthusiasm and role fit
2. Body: Match 2-3 key skills to job requirements with specific examples
3. Closing: Call to action and thank you

Return ONLY valid JSON with double quotes:
{{
  "cover_letter": "<the full cover letter text>",
  "ats_score": <number 0-100>,
  "key_matches": ["skill match 1", "skill match 2", "skill match 3"]
}}"""

    else:
        prompt = f"""You are a senior technical recruiter. Optimize this resume for the job.

RESUME:
{resume_text}

TARGET JOB:
{job_description or "N/A"}

RULES:

1. BULLET POINTS - Start with action verb, add realistic metrics:
   - Use varied numbers: 12%, 18%, 37%, 45% (NOT 20%, 25%, 30%, 50%)
   - Use ranges: "15-20%", "3x-4x", "10K-15K"
   - Use specific counts: "12 features", "8 microservices", "40+ PRs"
   - Example: "Optimized API response time from 2.3s to 890ms, reducing user churn by 18%"

2. IMPROVEMENTS - Be SPECIFIC to THIS resume:
   - "Add quantifiable metric to WeChat mini-program bullet point"
   - "Reorder skills to put Python first (matching job description)"
   - "Add cloud platform experience (AWS/Azure) if available"
   - NOT: "Learn TensorFlow" or "Explore machine learning"

3. KEEP original company names - never change them
   - If resume says "Personal Projects", keep it
   - If resume says "ABC Corp", keep it

4. SUMMARY - 2 sentences max, tailored to job:
   - Years of experience + top 3 skills + career goal
   - Match keywords from job description

JSON STRUCTURE:
{{
  "ats_score": <0-100>,
  "name": "<name>",
  "contact": "<contact>",
  "summary": "<2 sentence summary>",
  "experience": [
    {{
      "title": "<title>",
      "company": "<company - KEEP ORIGINAL>",
      "location": "<location>",
      "dates": "<dates>",
      "bullets": ["<enhanced bullet>", ...]
    }}
  ],
  "education": [...],
  "skills": [...],
  "improvements": ["<specific to THIS resume>"],
  "keyword_match": ["<exact from JD>"],
  "missing_keywords": ["<exact from JD not in resume>"]
}}"""

RULES:
1. Keep ALL original information - enhance, don't remove
2. Improve bullet points with action verbs and metrics
3. Add keywords from job description naturally
4. Return ONLY valid JSON"""

    system_msg = """You are a senior technical recruiter who has reviewed 50,000+ resumes.

CRITICAL RULES:
1. METRICS must be realistic and varied:
   - Use: 12%, 18%, 37%, 45%, 15-20%, 3x-4x, 10K-15K
   - NEVER use: 20%, 25%, 30%, 50%, 100% (too round, looks fake)
2. IMPROVEMENTS must be specific to the resume content:
   - "Add metric to WeChat project bullet point"
   - "Reorder skills to match job description"
   - NOT "Learn TensorFlow" or "Explore machine learning"
3. KEEP original company names - never change them
4. Return ONLY valid JSON"""

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
        
        # Generate specific improvements if AI improvements are generic
        if data.get("improvements") and len(data["improvements"]) > 0:
            if any("add" in imp.lower() and "metric" in imp.lower() for imp in data["improvements"]):
                # AI improvements are too generic, generate specific ones
                data["improvements"] = generate_specific_improvements(data)
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

    html_content = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<style>
body {{ font-family: Arial, sans-serif; font-size: 11pt; line-height: 1.5; color: #333; max-width: 800px; margin: 0 auto; padding: 40px; }}
h1 {{ font-size: 18pt; margin-bottom: 5px; color: #1a1a1a; }}
h2 {{ font-size: 13pt; border-bottom: 1px solid #333; padding-bottom: 3px; margin-top: 20px; color: #1a1a1a; text-transform: uppercase; }}
p {{ margin: 3px 0; }}
ul {{ margin: 5px 0; padding-left: 20px; }}
li {{ margin: 2px 0; }}
.contact {{ color: #555; font-size: 10pt; margin-bottom: 15px; }}
</style></head><body>
{resume_content.replace(chr(10), '<br>').replace('  ', '&nbsp;')}
</body></html>"""

    try:
        from xhtml2pdf import pisa
        output = io.BytesIO()
        pisa.CreatePDF(io.StringIO(html_content), dest=output)
        output.seek(0)
        return send_file(output, mimetype='application/pdf', as_attachment=True, download_name='optimized_resume.pdf')
    except Exception as e:
        return jsonify({'error': f'PDF generation failed: {str(e)}'}), 500

@app.route('/api/optimize', methods=['POST'])
def api_optimize():
    data = request.json
    resume_text = data.get('resume', '')
    job_description = data.get('job_description', '')
    mode = data.get('mode', 'optimize')

    if not resume_text:
        return jsonify({'error': 'resume required'}), 400

    prompt = f"""Optimize this resume. Return JSON with: ats_score, optimized_resume, improvements, keyword_match, missing_keywords.

RESUME:
{resume_text}

JOB DESCRIPTION:
{job_description or 'N/A'}"""

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

