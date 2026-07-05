"""Core optimization routes"""
import os
import io
import json
import re
import uuid
import hashlib
import datetime
import hmac
import logging
from flask import Blueprint, request, jsonify, render_template, send_file, session, redirect, url_for
from ats_engine import ATSEngine
from services.ai import call_ai, parse_ai_json, parse_pdf
from services.storage import (
    get_user_by_id, get_user_id, check_usage_limit, increment_usage,
    check_and_increment_usage,
    get_user_usage, is_pro_user, set_pro_status, track_event, save_history,
    FREE_OPTIMIZATIONS
)
from services.constants import TECH_KEYWORDS_DISPLAY, DEFAULT_SKILLS, EMAIL_PATTERN, PHONE_PATTERN

logger = logging.getLogger(__name__)
optimize_bp = Blueprint('optimize', __name__)
ats_engine = ATSEngine()

LEMONSQUEEZY_API_KEY = os.environ.get('LEMONSQUEEZY_API_KEY', '')
LEMONSQUEEZY_STORE_ID = os.environ.get('LEMONSQUEEZY_STORE_ID', '')
LEMONSQUEEZY_VARIANT_ID = os.environ.get('LEMONSQUEEZY_VARIANT_ID', '')


def expand_skills(skills: list, job_description: str) -> list:
    """Expand skills list based on job description keywords.

    Args:
        skills: Current list of skills.
        job_description: Job description text to extract keywords from.

    Returns:
        Expanded list of skills including matched keywords.
    """
    skills = list(skills) if skills else []
    if job_description:
        jd_lower = job_description.lower()
        for skill in TECH_KEYWORDS_DISPLAY:
            if skill.lower() in jd_lower and skill not in skills:
                skills.append(skill)
    if len(skills) < 8:
        for skill in DEFAULT_SKILLS:
            if skill not in skills and len(skills) < 8:
                skills.append(skill)
    return skills


def format_structured_resume(data: dict) -> str:
    """Format structured resume data into readable text.

    Args:
        data: Dictionary containing resume sections (name, contact, summary, etc.)

    Returns:
        Formatted resume text.
    """
    lines = []
    if data.get("name"):
        lines.append(data["name"])
    if data.get("contact"):
        lines.append(data["contact"])
    lines.append("")
    if data.get("summary"):
        lines.append("PROFESSIONAL SUMMARY")
        lines.append(data["summary"])
        lines.append("")
    if data.get("experience"):
        lines.append("EXPERIENCE")
        for exp in data["experience"]:
            title = exp.get("title", "")
            company = exp.get("company", "")
            dates = exp.get("dates", "")
            lines.append(f"{title} | {company} | {dates}")
            for bullet in exp.get("bullets", []):
                lines.append(f"- {bullet}")
            lines.append("")
    if data.get("education"):
        lines.append("EDUCATION")
        for edu in data["education"]:
            lines.append(f"{edu.get('degree', '')} | {edu.get('school', '')} | {edu.get('year', '')}")
        lines.append("")
    if data.get("skills"):
        lines.append("SKILLS")
        lines.append(", ".join(data["skills"]))
    return "\n".join(lines)


def format_resume_dict(resume_dict):
    """Convert a dict resume to formatted text"""
    lines = []
    for section, content in resume_dict.items():
        lines.append(section.upper())
        lines.append("")
        if isinstance(content, dict):
            for k, v in content.items():
                lines.append(f"{k}: {v}")
        elif isinstance(content, list):
            for item in content:
                lines.append(f"- {item}")
        else:
            lines.append(str(content))
        lines.append("")
    return "\n".join(lines)


def format_raw_text(text):
    """Ensure text is properly formatted"""
    return text.strip() if text else ""


def generate_specific_improvements(data):
    """Generate improvements based on resume content"""
    improvements = []
    skills = data.get("skills", [])
    summary = data.get("summary", "")
    experience = data.get("experience", [])

    if experience:
        for exp in experience[:2]:
            bullets = exp.get("bullets", [])
            has_metric = any(re.search(r'\d+%|\$[\d,]+|\d+ (users|customers|projects)', b) for b in bullets)
            if not has_metric and bullets:
                improvements.append(f"Add quantified impact to {exp.get('company', 'your role')}: include metrics like revenue, users, or efficiency gains")

    if not skills or len(skills) < 8:
        improvements.append("Expand skills section with 3-5 more technologies from job description")

    if summary:
        improvements.append("Tailor summary to mention specific job title from description")

    return improvements[:4]


@optimize_bp.route('/tutorial')
def tutorial():
    """Render tutorial page"""
    user = get_user_by_id(session.get('user_id'))
    return render_template('tutorial.html', user=user)


@optimize_bp.route('/refund-policy')
def refund_policy():
    """Render refund policy page"""
    user = get_user_by_id(session.get('user_id'))
    return render_template('refund_policy.html', user=user)


@optimize_bp.route('/privacy-policy')
def privacy_policy():
    """Render privacy policy page"""
    user = get_user_by_id(session.get('user_id'))
    return render_template('privacy_policy.html', user=user)


@optimize_bp.route('/terms')
def terms_of_service():
    """Render terms of service page"""
    user = get_user_by_id(session.get('user_id'))
    return render_template('terms_of_service.html', user=user)


@optimize_bp.route('/')
def index():
    user = get_user_by_id(session.get('user_id'))
    if not user:
        return redirect(url_for('auth.register'))

    # Track page view
    track_event(user['id'], 'page_view', {'page': 'home'})

    # A/B testing for CTA
    import random
    ab_test = session.get('ab_cta', random.choice(['A', 'B', 'C']))
    session['ab_cta'] = ab_test

    cta_options = {
        'A': "Optimize My Resume — It's Free",
        'B': "Get Your ATS Score — Free",
        'C': "Beat the ATS — Start Free"
    }

    return render_template('index.html', user=user, cta_text=cta_options[ab_test], ab_variant=ab_test)


@optimize_bp.route('/upload', methods=['POST'])
def upload_file():
    if 'resume_file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    file = request.files['resume_file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'Only PDF files are supported'}), 400
    header = file.read(4)
    file.seek(0)
    if header != b'%PDF':
        return jsonify({'error': 'Invalid PDF file'}), 400
    text = parse_pdf(file)
    if text.startswith('Error'):
        return jsonify({'error': text}), 400
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', text)
    return jsonify({'resume_text': text, 'filename': file.filename})


@optimize_bp.route('/api/free-scan', methods=['POST'])
def free_scan():
    """Free ATS scan without authentication - returns basic scoring only."""
    resume_text = request.form.get('resume_text', '')
    job_description = request.form.get('job_description', '')

    if not resume_text:
        return jsonify({'error': 'Please paste your resume'}), 400

    # Run basic ATS analysis without AI
    jd = job_description or "N/A"
    ats_result = ats_engine.analyze(resume_text, jd)

    # Return basic results without full optimization
    return jsonify({
        'ats_score': ats_result['ats_score'],
        'score_breakdown': {
            'keyword_match': ats_result['breakdown']['keywords']['score'],
            'formatting': ats_result['breakdown']['formatting']['score'],
            'experience_quality': ats_result['breakdown']['experience']['score'],
            'education_relevance': ats_result['breakdown']['education']['score']
        },
        'matched_keywords': ats_result['breakdown']['keywords']['matched'][:10],
        'missing_keywords': ats_result['breakdown']['keywords']['missing'][:10],
        'improvements': ats_result['improvements'][:5],
        'ats_type': ats_result['ats_type'],
        'personal_info_issues': ats_result['breakdown'].get('personal_info', {}).get('issues', []),
        'is_free': True,
        'message': 'Sign up for full optimization with AI rewrite and detailed analysis!'
    })


@optimize_bp.route('/optimize', methods=['POST'])
def optimize():
    resume_text = request.form.get('resume_text', '')
    job_description = request.form.get('job_description', '')
    mode = request.form.get('mode', 'optimize')

    if not resume_text:
        return jsonify({'error': 'Please paste your resume'}), 400

    user_id = get_user_id()
    if not user_id:
        return jsonify({'error': 'Please register/login first'}), 401
    if not check_and_increment_usage(user_id):
        return jsonify({'error': 'Free limit reached. Please upgrade to Pro.'}), 403

    track_event(user_id, 'optimize_start', {'mode': mode})

    jd = job_description or "N/A"

    if mode == 'ats':
        ats_result = ats_engine.analyze(resume_text, jd)
        ai_prompt = f"""基于以下 ATS 分析结果，提供针对性的深度建议。

简历 ATS 评分：{ats_result['ats_score']}/100
主要问题：{', '.join(ats_result['improvements'][:3])}
缺失关键词：{', '.join(ats_result['breakdown']['keywords']['missing'][:5])}

评分标准：
- HIGH (80-100): 完全符合ATS要求，关键词匹配度高
- MEDIUM (60-79): 基本符合，有改进空间
- LOW (0-59): 需要重大改进

公平性约束：
- 评分不应基于姓名、学校名称、地点
- 只关注技能、经验、项目质量
- 每个评分必须给出具体证据

返回严格JSON（不要添加任何其他文本）：
{{
  "optimized_resume": "针对主要问题优化后的完整简历文本",
  "bullet_analysis": [
    {{"original": "原始bullet", "optimized": "优化后", "change": "改了什么", "reason": "为什么改"}}
  ],
  "keyword_suggestions": ["建议添加的关键词1", "关键词2"],
  "extra_improvements": ["额外的深度改进建议"]
}}

规则：
1. 针对评分最低的维度重点优化
2. 补充缺失的关键词到简历中
3. 优化bullet points的量化数据和动词
4. 不要编造数据
5. 每个建议必须给出具体原因"""
        ai_data = parse_ai_json(call_ai(ai_prompt, "你是ATS优化专家。只返回严格JSON，无markdown。"))

        data = {
            "ats_score": ats_result["ats_score"],
            "score_breakdown": {
                "keyword_match": ats_result["breakdown"]["keywords"]["score"],
                "formatting": ats_result["breakdown"]["formatting"]["score"],
                "experience_quality": ats_result["breakdown"]["experience"]["score"],
                "education_relevance": ats_result["breakdown"]["education"]["score"]
            },
            "keyword_match": ats_result["breakdown"]["keywords"]["matched"],
            "missing_keywords": ats_result["breakdown"]["keywords"]["missing"],
            "improvements": ats_result["improvements"],
            "ats_type": ats_result["ats_type"],
            "optimized_resume": ai_data.get("optimized_resume", ""),
            "bullet_analysis": ai_data.get("bullet_analysis", [])
        }
    elif mode == 'keywords':
        prompt = """分析这份简历与目标职位的关键词匹配度。逐个技能检查匹配情况。

RESUME:
""" + resume_text + """

JOB DESCRIPTION:
""" + jd + """

返回严格JSON（不要添加任何其他文本）：
{
  "ats_score": 75,
  "score_breakdown": {
    "keyword_match": 70,
    "formatting": 80,
    "experience_quality": 75,
    "education_relevance": 70
  },
  "keyword_match": ["Python", "JavaScript"],
  "missing_keywords": ["React", "AWS"],
  "keyword_suggestions": [
    {"keyword": "React", "importance": "high", "where_to_add": "Skills section or Experience bullets"}
  ],
  "improvements": ["Add React to your skills section", "Include AWS projects in experience"],
  "optimized_resume": "优化后的完整简历文本"
}

规则：
1. 从JD提取所有关键技能和要求
2. 逐个检查是否在简历中出现
3. score_breakdown 各维度 0-100 分，必须包含所有4个维度
4. 不要编造内容"""
        system_msg = "你是关键词分析专家。只返回严格JSON，无markdown，无解释。"
        data = parse_ai_json(call_ai(prompt, system_msg))
    elif mode == 'cover_letter':
        prompt = """基于这份简历和目标职位，生成一封专业的求职信。

RESUME:
""" + resume_text + """

JOB DESCRIPTION:
""" + jd + """

返回严格JSON：
{
  "cover_letter": "完整求职信（3-4段，专业语气，针对具体职位）",
  "ats_score": 75,
  "key_matches": ["简历与职位匹配的关键技能"],
  "personalization_points": ["针对该公司的个性化内容"]
}

规则：
1. 求职信要针对具体公司和职位
2. 强调最相关的2-3个经验
3. 展示对公司的了解
4. 专业但不生硬"""
        system_msg = "你是职业顾问。返回严格JSON。"
        data = parse_ai_json(call_ai(prompt, system_msg))
    elif mode == 'interview':
        # Extract key skills for personalized questions
        skills = []
        common_skills = ['python', 'java', 'javascript', 'react', 'aws', 'docker', 'sql', 'git', 'node.js', 'django', 'flask', 'kubernetes']
        for skill in common_skills:
            if skill in resume_text.lower():
                skills.append(skill)

        # Get questions from knowledge base
        from services.interview_knowledge import generate_interview_prep
        kb_data = generate_interview_prep(skills, "technical")

        # Also get AI-generated questions for personalization
        prompt = f"""Based on this resume and job description, generate 2-3 additional personalized interview questions.

RESUME:
{resume_text[:500]}

JOB DESCRIPTION:
{jd[:300]}

KEY SKILLS: {', '.join(skills[:5]) if skills else 'Not specified'}

Return strict JSON:
{{
  "extra_technical": [
    {{"question": "Question about specific project or skill from resume", "answer_guide": "Answer guidance", "difficulty": "medium"}}
  ],
  "extra_behavioral": [
    {{"question": "Behavioral question based on their experience", "answer_guide": "STAR method guidance", "category": "problem-solving"}}
  ]
}}

RULES:
1. Reference SPECIFIC projects/skills from the resume
2. Be unique - not generic template questions
3. Focus on their actual experience"""
        system_msg = "Generate personalized interview questions. Return strict JSON only."
        ai_data = parse_ai_json(call_ai(prompt, system_msg))

        # Merge knowledge base with AI-generated questions
        data = {
            "technical_questions": kb_data.get("technical_questions", []) + ai_data.get("extra_technical", []),
            "behavioral_questions": kb_data.get("behavioral_questions", []) + ai_data.get("extra_behavioral", []),
            "company_questions": kb_data.get("company_questions", []),
            "your_questions": kb_data.get("your_questions", []),
            "tips": kb_data.get("tips", [])
        }
    elif mode == 'salary':
        # Extract experience years
        import re
        years_match = re.search(r'(\d+)\+?\s*(?:years?|yrs?)', resume_text.lower())
        years = int(years_match.group(1)) if years_match else 2

        # Extract skills
        skills = []
        common_skills = ['python', 'java', 'javascript', 'react', 'aws', 'docker', 'sql', 'node.js', 'django', 'flask', 'kubernetes', 'golang', 'go']
        for skill in common_skills:
            if skill in resume_text.lower():
                skills.append(skill)

        prompt = f"""Analyze this resume and estimate salary range based on market data.

RESUME:
{resume_text}

JOB DESCRIPTION:
{jd}

EXPERIENCE YEARS: {years}
KEY SKILLS: {', '.join(skills[:5]) if skills else 'Not specified'}

Return strict JSON:
{{
  "salary_range": {{
    "minimum": 80000,
    "recommended": 100000,
    "maximum": 130000,
    "currency": "USD"
  }},
  "market_analysis": "Detailed analysis of current market rates for this role based on experience, skills, and location",
  "factors": [
    {{"factor": "Factor affecting salary", "impact": "high/medium/low", "explanation": "Specific explanation"}}
  ],
  "negotiation_tips": [
    {{"tip": "Negotiation strategy", "example": "Exact script to use"}}
  ],
  "total_compensation": {{
    "base_salary": "Base salary amount",
    "equity": "Stock options/equity details",
    "bonus": "Bonus structure",
    "benefits": "Benefits package"
  }},
  "red_flags": ["Red flags in salary offers to watch for"]
}}

CRITICAL RULES:
1. Salary MUST be in USD
2. Base salary on REAL market data for {years} years experience
3. Consider location (US average unless specified)
4. Include specific negotiation scripts
5. Break down total compensation realistically"""
        system_msg = "You are a compensation expert with access to 2025-2026 market salary data. Provide accurate, data-driven salary estimates. Return strict JSON only."
        data = parse_ai_json(call_ai(prompt, system_msg))
        data = validate_salary_output(data)
    else:
        prompt = """你是资深ATS优化专家和职业顾问。分析并优化这份简历。

RESUME:
""" + resume_text + """

TARGET JOB:
""" + jd + """

评分标准（每个维度0-100分）：
- HIGH (80-100): 完全符合ATS要求，无需改进
- MEDIUM (60-79): 基本符合，有改进空间
- LOW (0-59): 需要重大改进

公平性约束：
- 评分不应基于姓名、学校名称、地理位置
- 只关注技能匹配度、经验相关性、项目质量
- 每个评分必须给出具体证据

返回严格JSON格式（不要添加任何其他文本）：
{
  "ats_score": 82,
  "score_breakdown": {
    "keyword_match": 85,
    "formatting": 90,
    "experience_quality": 78,
    "education_relevance": 80
  },
  "name": "姓名",
  "contact": "联系方式",
  "summary": "优化后的专业摘要（2-3句话，突出最相关的经验）",
  "experience": [
    {
      "title": "职位",
      "company": "公司名（保持原样）",
      "location": "地点",
      "dates": "时间",
      "bullets": [
        "Led development of React-based dashboard serving 10M monthly active users",
        "Increased API performance by 45% through database optimization"
      ],
      "bullet_analysis": [
        {"original": "Worked on the dashboard project", "optimized": "Led development of React-based dashboard serving 10M monthly active users", "change": "Added quantified impact and power verb", "reason": "ATS systems prioritize quantified achievements and action verbs"}
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
2. 【最重要】绝对不要修改任何数字！保留所有百分比、金额、用户数等数字原样不动
3. 如果简历中没有量化数据，不要编造——改为建议用户添加
4. 只优化非数字内容：动词、句式结构、关键词
5. 使用有力动词：Led, Built, Increased, Reduced, Delivered, Launched
6. 添加JD中的相关关键词（包括软技能：teamwork, communication, leadership）
7. bullet点以行动动词开头
8. 每个bullet说明具体改了什么、为什么改
9. score_breakdown 各维度 0-100 分，必须包含所有4个维度
10. 软技能关键词必须翻译成英文：teamwork, communication, leadership, problem-solving
11. 每个改进建议必须给出具体原因和预期效果"""
        system_msg = "You are an expert ATS optimization specialist. Return strict JSON only. ALL keywords MUST be in English, never translate to Chinese. Scores must be based on evidence, not personal characteristics."
        data = parse_ai_json(call_ai(prompt, system_msg))

        # Post-process
        if "skills" in data and job_description:
            data["skills"] = expand_skills(data.get("skills", []), job_description)
        if "name" in data:
            data["optimized_resume"] = format_structured_resume(data)
        elif "optimized_resume" in data and isinstance(data["optimized_resume"], dict):
            data["optimized_resume"] = format_resume_dict(data["optimized_resume"])

        # Validate no fabricated data
        if "optimized_resume" in data and data["optimized_resume"]:
            from services.ai import validate_no_fabrication
            data["optimized_resume"] = validate_no_fabrication(resume_text, data["optimized_resume"])
        for field in ["ats_score", "optimized_resume", "improvements", "keyword_match", "missing_keywords"]:
            if field not in data:
                data[field] = [] if field in ["improvements", "keyword_match", "missing_keywords"] else (65 if field == "ats_score" else "")
        if data.get("experience") or data.get("skills") or data.get("summary"):
            specific_improvements = generate_specific_improvements(data)
            if specific_improvements:
                data["improvements"] = specific_improvements

    if not data:
        data = {"ats_score": 65, "optimized_resume": "", "improvements": [], "keyword_match": [], "missing_keywords": []}

    proof_id = str(uuid.uuid4())[:8]
    proof = {
        "id": proof_id,
        "timestamp": datetime.datetime.now().isoformat(),
        "resume_hash": hashlib.sha256(resume_text.encode()).hexdigest()[:16],
        "ats_score": data.get("ats_score", 0),
        "improvements_count": len(data.get("improvements", []))
    }

    track_event(user_id, 'optimize_complete', {
        'mode': mode,
        'score': data.get("ats_score", 0),
        'has_job_description': bool(job_description),
        'resume_length': len(resume_text),
        'improvements_count': len(data.get("improvements", []))
    })
    save_history({
        'id': proof_id, 'user_id': user_id,
        'resume_text': resume_text[:2000], 'job_description': jd[:1000],
        'mode': mode, 'result': {'ats_score': data.get("ats_score", 0), 'improvements': data.get("improvements", [])},
        'created_at': datetime.datetime.now().isoformat()
    })

    if mode == 'cover_letter':
        return render_template('cover_letter.html', data=data, proof=proof, resume_text=resume_text, job_description=job_description)
    elif mode == 'interview':
        return render_template('interview.html', data=data, proof=proof, resume_text=resume_text, job_description=job_description)
    elif mode == 'salary':
        return render_template('salary.html', data=data, proof=proof, resume_text=resume_text, job_description=job_description)
    return render_template('result.html', data=data, proof=proof, resume_text=resume_text, job_description=job_description)


@optimize_bp.route('/export/pdf', methods=['POST'])
def export_pdf():
    import html as html_lib
    resume_content = request.form.get('resume_content', '')
    template = request.form.get('template', 'modern')
    if not resume_content:
        return jsonify({'error': 'No content'}), 400

    # Read template CSS
    template_css = ""
    css_path = os.path.join(os.path.dirname(__file__), '..', 'static', 'templates.css')
    try:
        with open(css_path, 'r') as f:
            template_css = f.read()
    except Exception:
        pass

    # Convert text to structured HTML
    lines = resume_content.split('\n')
    html_body = ""
    in_list = False
    for line in lines:
        line = line.strip()
        if not line:
            if in_list:
                html_body += "</ul>"
                in_list = False
            continue
        if line.isupper() and len(line) > 2:
            if in_list:
                html_body += "</ul>"
                in_list = False
            html_body += f"<h2>{html_lib.escape(line)}</h2>"
        elif line.startswith('- ') or line.startswith('• '):
            if not in_list:
                html_body += "<ul>"
                in_list = True
            html_body += f"<li>{html_lib.escape(line[2:])}</li>"
        elif '|' in line and any(kw in line.lower() for kw in ['experience', 'engineer', 'developer', 'manager', 'analyst', 'specialist']):
            parts = [p.strip() for p in line.split('|')]
            html_body += f"<h3>{html_lib.escape(parts[0])}</h3>"
            if len(parts) > 1:
                html_body += f"<p class='dates'>{html_lib.escape(' | '.join(parts[1:]))}</p>"
        else:
            if re.search(EMAIL_PATTERN, line) or 'linkedin' in line.lower() or 'phone' in line.lower():
                html_body += f"<p class='contact'>{html_lib.escape(line)}</p>"
            else:
                html_body += f"<p>{html_lib.escape(line)}</p>"
    if in_list:
        html_body += "</ul>"

    html_content = f"""<!DOCTYPE html>
<html><head><meta charset='UTF-8'>
<style>{template_css}</style>
</head><body>
<div class="resume-template template-{template}">
{html_body}
</div></body></html>"""

    try:
        from xhtml2pdf import pisa
        output = io.BytesIO()
        pisa.CreatePDF(io.StringIO(html_content), dest=output)
        output.seek(0)
        return send_file(output, mimetype='application/pdf', as_attachment=True, download_name=f'resume_{template}.pdf')
    except Exception as e:
        logger.error(f"PDF generation failed: {e}")
        return jsonify({'error': 'PDF generation failed'}), 500


@optimize_bp.route('/api/optimize', methods=['POST'])
def api_optimize():
    user_id = get_user_id()
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401
    if not check_and_increment_usage(user_id):
        return jsonify({'error': 'Usage limit reached'}), 403
    data = request.json
    if not data:
        return jsonify({'error': 'Invalid JSON'}), 400
    resume_text = data.get('resume', '')
    job_description = data.get('job_description', '')
    mode = data.get('mode', 'optimize')
    if not resume_text:
        return jsonify({'error': 'resume required'}), 400
    prompt = "Optimize this resume. Return JSON with: ats_score, optimized_resume, improvements, keyword_match, missing_keywords.\n\nRESUME:\n" + resume_text + "\n\nJOB DESCRIPTION:\n" + (job_description or "N/A")
    result = call_ai(prompt)
    parsed = parse_ai_json(result)
    if not parsed:
        parsed = {"ats_score": 65, "optimized_resume": "", "improvements": []}

    # Validate and clamp output
    if "ats_score" in parsed:
        parsed["ats_score"] = max(0, min(100, int(parsed["ats_score"])))
    if "optimized_resume" not in parsed:
        parsed["optimized_resume"] = resume_text
    if "improvements" not in parsed:
        parsed["improvements"] = []
    if "keyword_match" not in parsed:
        parsed["keyword_match"] = []
    if "missing_keywords" not in parsed:
        parsed["missing_keywords"] = []

    return jsonify(parsed)


@optimize_bp.route('/health')
def health():
    return jsonify({"status": "ok"})


@optimize_bp.route('/api/usage')
def get_usage():
    user_id = get_user_id()
    if not user_id:
        return jsonify({'error': 'Not logged in'}), 401
    usage = get_user_usage(user_id)
    is_pro = is_pro_user(user_id)
    remaining = max(0, FREE_OPTIMIZATIONS - usage) if not is_pro else -1
    return jsonify({
        'usage_count': usage, 'free_limit': FREE_OPTIMIZATIONS,
        'remaining': remaining, 'is_pro': is_pro, 'user_id': user_id
    })


@optimize_bp.route('/api/track', methods=['POST'])
def track_event_api():
    """Track user behavior events from frontend"""
    user_id = get_user_id()
    data = request.json
    event_type = data.get('event_type', '')
    event_data = data.get('event_data', {})

    if user_id and event_type:
        track_event(user_id, event_type, event_data)

    return jsonify({'status': 'ok'})


@optimize_bp.route('/api/analytics/modes')
def get_mode_analytics():
    """Get mode usage analytics (admin only)"""
    import os
    user_id = get_user_id()
    if not user_id:
        return jsonify({'error': 'Not logged in'}), 401

    user = get_user_by_id(user_id)
    admin_email = os.environ.get('ADMIN_EMAIL', '')
    if not user or user.get('email') != admin_email:
        return jsonify({'error': 'Unauthorized'}), 403

    from services.storage import get_admin_stats
    stats = get_admin_stats()

    # Count mode usage from events
    mode_counts = {}
    for event in stats.get('event_counts', {}):
        if 'optimize' in event:
            mode = event.split('_')[-1] if '_' in event else 'unknown'
            mode_counts[mode] = stats['event_counts'][event]

    return jsonify({
        'total_users': stats['total_users'],
        'total_events': stats['total_events'],
        'mode_usage': mode_counts
    })


@optimize_bp.route('/pricing')
def pricing_page():
    """Pricing page with multiple tiers"""
    user = get_user_by_id(session.get('user_id'))
    return render_template('pricing.html', user=user)


@optimize_bp.route('/api/create-checkout', methods=['POST'])
def create_checkout():
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
                        'custom_data': {'user_id': get_user_id()}
                    }
                }
            }
        )
        data = resp.json()
        if 'data' in data and 'attributes' in data['data']:
            return jsonify({'checkout_url': data['data']['attributes']['url']})
        return jsonify({'error': 'Failed to create checkout', 'details': data}), 500
    except Exception as e:
        logger.error(f"Checkout error: {e}")
        return jsonify({'error': 'An error occurred while processing your request'}), 500


@optimize_bp.route('/api/webhook', methods=['POST'])
def webhook():
    webhook_secret = os.environ.get('LEMONSQUEEZY_WEBHOOK_SECRET', '')
    if not webhook_secret:
        logger.warning("LEMONSQUEEZY_WEBHOOK_SECRET not set - webhook rejected")
        return jsonify({'error': 'Webhook secret not configured'}), 500
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


@optimize_bp.route('/api/check-usage', methods=['POST'])
def check_usage():
    user_id = get_user_id()
    if not user_id:
        return jsonify({'error': 'Not logged in', 'allowed': False}), 401
    can_use = check_usage_limit(user_id)
    return jsonify({
        'allowed': can_use,
        'remaining': max(0, FREE_OPTIMIZATIONS - get_user_usage(user_id)) if not is_pro_user(user_id) else -1,
        'is_pro': is_pro_user(user_id)
    })
