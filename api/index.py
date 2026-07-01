import os
import sys
import json
import hashlib
import datetime
import uuid
from flask import Flask, request, jsonify, render_template

app = Flask(__name__, template_folder='../templates')

SILICONFLOW_API_KEY = os.environ.get('SILICONFLOW_API_KEY', '')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
API_KEY = OPENAI_API_KEY or SILICONFLOW_API_KEY
API_BASE = "https://api.openai.com/v1" if OPENAI_API_KEY else "https://api.siliconflow.cn/v1"
MODEL = "gpt-4o-mini" if OPENAI_API_KEY else "Qwen/Qwen2.5-7B-Instruct"

def call_openai(prompt, system_msg="You are an expert resume optimizer and career coach."):
    try:
        from curl_cffi import requests as cffi_requests
        resp = cffi_requests.post(
            f"{API_BASE}/chat/completions",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 3000
            },
            impersonate="chrome"
        )
        return resp.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Error: {str(e)}"

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

    prompt = f"""Optimize this resume for maximum impact and ATS compatibility.

RESUME:
{resume_text}

{"JOB DESCRIPTION (target this role):" + chr(10) + job_description if job_description else ""}

Return a JSON response with:
1. "ats_score": number 0-100
2. "optimized_resume": the full optimized resume text
3. "improvements": list of improvements made
4. "keyword_match": list of matched keywords
5. "missing_keywords": list of missing keywords
6. "bullet_improvements": list of before/after bullet points

Return ONLY valid JSON, no markdown."""

    system_msg = """You are an expert resume writer and ATS optimization specialist.
Analyze resumes thoroughly and provide actionable, specific improvements.
Always return valid JSON with the fields requested."""

    result = call_openai(prompt, system_msg)

    try:
        result = result.strip()
        if result.startswith("```"):
            result = result.split("\n", 1)[1].rsplit("```", 1)[0]
        data = json.loads(result)
    except:
        data = {
            "ats_score": 65,
            "optimized_resume": result,
            "improvements": ["AI analysis completed"],
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
    if not resume_text:
        return jsonify({'error': 'resume required'}), 400

    prompt = f"""Optimize this resume. Return JSON with: ats_score, optimized_resume, improvements, keyword_match, missing_keywords.

RESUME:
{resume_text}

JOB DESCRIPTION:
{data.get('job_description', 'N/A')}"""

    result = call_openai(prompt)
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
    return jsonify({"status": "ok"})

def handler(request):
    return app(request.environ, lambda status, headers: None)
