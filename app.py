from flask import Flask, request, jsonify, render_template, send_file
import os
import io
import json
import hashlib
import datetime
import uuid
import re

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
        prompt = f"""You are a senior technical recruiter at a FAANG company. Analyze this resume for a specific job.

RESUME:
{resume_text}

TARGET JOB:
{job_description or "N/A"}

TASK: Return a JSON with the OPTIMIZED resume and analysis.

RULES FOR BULLET POINTS:
1. Start with strong action verbs: Architected, Led, Implemented, Optimized, Reduced, Increased, Delivered, Designed, Built, Automated
2. Add realistic, modest metrics (not round numbers like 30% or 95%):
   - Instead of "improved performance" → "Reduced API response time from 2s to 800ms"
   - Instead of "worked on team" → "Collaborated with 4 engineers on cross-functional sprint team"
   - Instead of "fixed bugs" → "Resolved 15+ production bugs, reducing incident tickets by 40%"
3. Include specific technologies mentioned in the resume
4. Add keywords from job description naturally

RULES FOR SUMMARY:
- 2 sentences max
- Mention years of experience + top skills + career goal
- Tailor to the job description

RULES FOR IMPROVEMENTS:
- Be SPECIFIC: "Add quantifiable metric to 2nd bullet point in ABC Corp section"
- Not generic: "Add metrics" or "Use action verbs"

RULES FOR KEYWORDS:
- Extract EXACT words from job description that appear in resume
- List words from job description NOT in resume

JSON STRUCTURE:
{{
  "ats_score": <0-100>,
  "name": "<candidate name>",
  "contact": "<email | phone | linkedin>",
  "summary": "<2 sentence professional summary>",
  "experience": [
    {{
      "title": "<job title>",
      "company": "<company>",
      "location": "<city, state>",
      "dates": "<MMM YYYY - MMM YYYY or Present>",
      "bullets": ["<enhanced bullet 1>", "<enhanced bullet 2>"]
    }}
  ],
  "education": [
    {{
      "degree": "<degree>",
      "school": "<school>",
      "year": "<year>"
    }}
  ],
  "skills": ["<skill1>", "<skill2>", ...],
  "improvements": ["<specific improvement 1>", "<specific improvement 2>", ...],
  "keyword_match": ["<exact keyword from JD>"],
  "missing_keywords": ["<exact keyword from JD not in resume>"]
}}"""

RULES:
1. Keep ALL original information - enhance, don't remove
2. Improve bullet points with action verbs and metrics
3. Add keywords from job description naturally
4. Return ONLY valid JSON"""

    system_msg = """You are a senior technical recruiter who has reviewed 50,000+ resumes and hired 500+ engineers at FAANG companies.

You know exactly what makes a resume pass ATS filters and impress hiring managers.

Your approach:
1. Be SPECIFIC - exact metrics, exact technologies, exact company names
2. Be REALISTIC - modest improvements, not fabricated numbers
3. Be RELEVANT - tailor everything to the job description
4. Be CONCISE - every word must earn its place

Return ONLY valid JSON. No markdown, no explanations."""

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

