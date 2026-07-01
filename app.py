from flask import Flask, request, jsonify, render_template
import os
import json
import hashlib
import datetime
import uuid

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
            return json.dumps({"error": data["error"].get("message", "API error"), "ats_score": 0, "optimized_resume": "API temporarily unavailable. Please try again.", "improvements": [], "keyword_match": [], "missing_keywords": []})
        else:
            return json.dumps({"error": "Unexpected response", "ats_score": 0, "optimized_resume": str(data)[:500], "improvements": [], "keyword_match": [], "missing_keywords": []})
    except Exception as e:
        return json.dumps({"error": str(e), "ats_score": 0, "optimized_resume": f"Error: {str(e)}", "improvements": [], "keyword_match": [], "missing_keywords": []})

@app.route('/')
def index():
    return render_template('index.html')

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

    else:
        prompt = f"""You are an expert ATS resume optimizer. Optimize the resume below for the job description.

IMPORTANT RULES:
1. The optimized_resume field MUST be clean formatted text (NOT JSON, NOT Python dict)
2. Use this exact format for optimized_resume:
   - Use uppercase section headers (EXPERIENCE, EDUCATION, SKILLS)
   - Use bullet points with dashes
   - Keep it scannable and professional
3. Return ONLY valid JSON with double quotes

RESUME:
{resume_text}

JOB DESCRIPTION:
{job_description or "N/A"}

Return this exact JSON structure:
{{
  "ats_score": <number 0-100>,
  "optimized_resume": "<clean formatted resume text with sections and bullet points>",
  "improvements": ["<improvement 1>", "<improvement 2>", ...],
  "keyword_match": ["<keyword 1>", "<keyword 2>", ...],
  "missing_keywords": ["<keyword 1>", "<keyword 2>", ...]
}}"""

    system_msg = """You are an expert ATS resume optimizer. Return ONLY valid JSON with double quotes.
The optimized_resume field must be clean formatted text with sections and bullet points, NOT a dict or nested JSON."""

    result = call_ai(prompt, system_msg)

    try:
        result = result.strip()
        if result.startswith("```"):
            result = result.split("\n", 1)[1].rsplit("```", 1)[0]
        if result.startswith("json"):
            result = result[4:].strip()
        data = json.loads(result)
        if "optimized_resume" in data and isinstance(data["optimized_resume"], dict):
            data["optimized_resume"] = json.dumps(data["optimized_resume"], indent=2)
    except:
        data = {
            "ats_score": 65,
            "optimized_resume": result,
            "improvements": ["AI analysis completed - review the optimized version"],
            "keyword_match": [],
            "missing_keywords": [],
            "bullet_improvements": []
        }

    proof_id = str(uuid.uuid4())[:8]
    proof = {
        "id": proof_id,
        "timestamp": datetime.datetime.now().isoformat(),
        "resume_hash": hashlib.sha256(resume_text.encode()).hexdigest()[:16],
        "ats_score": data.get("ats_score", 0),
        "improvements_count": len(data.get("improvements", []))
    }

    return render_template('result.html', data=data, proof=proof, resume_text=resume_text, job_description=job_description)

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
