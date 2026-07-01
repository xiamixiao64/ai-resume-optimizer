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
        prompt = f"""Analyze this resume for ATS (Applicant Tracking System) compatibility.

RESUME:
{resume_text}

{"JOB DESCRIPTION (for targeting):" + chr(10) + job_description if job_description else ""}

Return a JSON response with:
1. "ats_score": number 0-100
2. "keyword_match": list of matched keywords
3. "missing_keywords": list of important missing keywords
4. "format_issues": list of formatting problems
5. "improvements": list of specific improvements to make
6. "optimized_resume": the full optimized resume text

Return ONLY valid JSON, no markdown."""

    elif mode == 'keywords':
        prompt = f"""Extract and suggest keywords for this resume to match job requirements.

RESUME:
{resume_text}

JOB DESCRIPTION:
{job_description or "N/A"}

Return a JSON response with:
1. "current_keywords": list of keywords already in resume
2. "suggested_keywords": list of keywords to add
3. "industry_terms": list of industry-specific terms to include
4. "action_verbs": list of stronger action verbs to use
5. "optimized_resume": the full resume with keywords integrated

Return ONLY valid JSON, no markdown."""

    else:
        prompt = f"""Optimize this resume for maximum impact and ATS compatibility.

RESUME:
{resume_text}

{"JOB DESCRIPTION (target this role):" + chr(10) + job_description if job_description else ""}

Provide:
1. An optimized version of the resume
2. ATS score (0-100)
3. List of improvements made
4. Keywords matched/missing
5. Specific bullet point improvements

Return a JSON response with:
1. "ats_score": number
2. "optimized_resume": the full optimized resume
3. "improvements": list of improvements
4. "keyword_match": list
5. "missing_keywords": list
6. "bullet_improvements": list of before/after bullet points

Return ONLY valid JSON, no markdown."""

    system_msg = """You are an expert resume writer and ATS optimization specialist with 15+ years of experience.
Analyze resumes thoroughly and provide actionable, specific improvements.
Always return valid JSON with the fields requested."""

    result = call_ai(prompt, system_msg)

    try:
        result = result.strip()
        if result.startswith("```"):
            result = result.split("\n", 1)[1].rsplit("```", 1)[0]
        data = json.loads(result)
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
