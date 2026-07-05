"""AI/LLM integration service"""
import os
import json
import logging
import random
from typing import Optional, Dict, List
import requests as std_requests

logger = logging.getLogger(__name__)

GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = os.environ.get('GROQ_MODEL', 'llama-3.3-70b-versatile')


def call_ai(prompt: str, system_msg: str = "You are an expert resume optimizer and career coach.") -> Optional[str]:
    """Call Groq AI API for resume optimization.

    Args:
        prompt: The user prompt to send to the AI.
        system_msg: System message defining AI behavior.

    Returns:
        AI response text, or None if the call fails.
    """
    try:
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
        if resp.status_code != 200:
            logger.error(f"Groq API HTTP {resp.status_code}: {resp.text[:200]}")
            return None
        try:
            data = resp.json()
        except ValueError:
            logger.error(f"Groq API returned non-JSON: {resp.text[:200]}")
            return None
        if "choices" in data and len(data["choices"]) > 0:
            return data["choices"][0]["message"]["content"]
        elif "error" in data:
            logger.error(f"Groq API error: {data['error']}")
        else:
            logger.error(f"Unexpected Groq response: {str(data)[:200]}")
    except Exception as e:
        logger.error(f"AI call failed: {e}")

    return None


def parse_ai_json(result: Optional[str]) -> dict:
    """Extract JSON from AI response, handling markdown code blocks.

    Args:
        result: AI response text that may contain JSON.

    Returns:
        Parsed JSON as dictionary, or empty dict if parsing fails.
    """
    import html as html_lib
    import re

    if not result:
        return {}

    result = result.strip()
    result = html_lib.unescape(result)
    code_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', result, re.DOTALL)
    if code_match:
        result = code_match.group(1).strip()
    json_start = result.find('{')
    json_end = result.rfind('}')
    if json_start != -1 and json_end != -1 and json_end > json_start:
        try:
            return json.loads(result[json_start:json_end + 1])
        except json.JSONDecodeError:
            pass
    return {}


def parse_pdf(file) -> str:
    """Extract text from PDF file.

    Args:
        file: PDF file object.

    Returns:
        Extracted text content, or error message if parsing fails.
    """
    try:
        import pdfplumber
        with pdfplumber.open(file) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() or ""
            return text.strip()
    except Exception as e:
        return f"Error parsing PDF: {str(e)}"


def validate_resume_output(data: dict) -> dict:
    """Validate and format AI resume optimization output.

    Args:
        data: Raw AI output dictionary.

    Returns:
        Validated and formatted dictionary.
    """
    required_fields = ['ats_score', 'optimized_resume', 'improvements']
    for field in required_fields:
        if field not in data:
            data[field] = [] if field in ['improvements', 'keyword_match', 'missing_keywords'] else 0

    # Validate ATS score
    if isinstance(data.get('ats_score'), (int, float)):
        data['ats_score'] = max(0, min(100, int(data['ats_score'])))
    else:
        data['ats_score'] = 65

    # Validate improvements
    if not isinstance(data.get('improvements'), list):
        data['improvements'] = []
    data['improvements'] = data['improvements'][:10]

    # Ensure optimized_resume is string
    if not isinstance(data.get('optimized_resume'), str):
        data['optimized_resume'] = str(data.get('optimized_resume', ''))

    return data


def validate_interview_output(data: dict) -> dict:
    """Validate and format AI interview preparation output.

    Args:
        data: Raw AI output dictionary.

    Returns:
        Validated and formatted dictionary.
    """
    default_data = {
        'technical_questions': [],
        'behavioral_questions': [],
        'company_questions': [],
        'your_questions': [],
        'tips': []
    }

    for key in default_data:
        if key not in data:
            data[key] = default_data[key]
        elif not isinstance(data[key], list):
            data[key] = []

    # Ensure each question has required fields
    for key in ['technical_questions', 'behavioral_questions']:
        for i, q in enumerate(data[key]):
            if not isinstance(q, dict):
                data[key][i] = {'question': str(q), 'answer_guide': '', 'difficulty': 'medium'}
            else:
                q.setdefault('question', '')
                q.setdefault('answer_guide', '')
                q.setdefault('difficulty', 'medium')

    for q in data.get('your_questions', []):
        if not isinstance(q, dict):
            q = {'question': str(q), 'purpose': ''}

    return data


def validate_salary_output(data: dict) -> dict:
    """Validate and format AI salary estimation output.

    Args:
        data: Raw AI output dictionary.

    Returns:
        Validated and formatted dictionary.
    """
    default_data = {
        'salary_range': {'minimum': 50000, 'recommended': 75000, 'maximum': 100000, 'currency': 'USD'},
        'market_analysis': '',
        'factors': [],
        'negotiation_tips': [],
        'total_compensation': {},
        'red_flags': []
    }

    for key in default_data:
        if key not in data:
            data[key] = default_data[key]

    # Validate salary range
    sr = data.get('salary_range', {})
    if not isinstance(sr, dict):
        sr = default_data['salary_range']
    sr.setdefault('minimum', 50000)
    sr.setdefault('recommended', 75000)
    sr.setdefault('maximum', 100000)
    sr.setdefault('currency', 'USD')
    data['salary_range'] = sr

    # Ensure minimum < recommended < maximum
    if sr['minimum'] > sr['recommended']:
        sr['minimum'] = sr['recommended'] - 10000
    if sr['recommended'] > sr['maximum']:
        sr['maximum'] = sr['recommended'] + 20000

    return data


def generate_personalized_questions(resume_text: str, jd_text: str) -> List[Dict]:
    """Generate personalized interview questions based on resume content.

    Args:
        resume_text: Resume content.
        jd_text: Job description.

    Returns:
        List of personalized questions.
    """
    # Extract skills from resume
    skills = []
    common_skills = ['python', 'java', 'javascript', 'react', 'aws', 'docker', 'sql', 'git']
    for skill in common_skills:
        if skill in resume_text.lower():
            skills.append(skill)

    # Generate skill-based questions
    skill_questions = []
    for skill in skills[:3]:
        skill_questions.append({
            'question': f'Describe your experience with {skill}. What projects have you worked on?',
            'answer_guide': f'Use the STAR method. Mention specific projects where you used {skill}, the challenges you faced, and the results you achieved.',
            'difficulty': 'medium'
        })

    return skill_questions


def add_randomness(data: dict) -> dict:
    """Add slight randomness to make outputs feel more natural.

    Args:
        data: Output dictionary.

    Returns:
        Modified dictionary with random variations.
    """
    # Randomize tips order slightly
    if 'tips' in data and isinstance(data['tips'], list) and len(data['tips']) > 2:
        if random.random() > 0.5:
            first = data['tips'][0]
            data['tips'][0] = data['tips'][1]
            data['tips'][1] = first

    # Add slight variation to scores
    if 'ats_score' in data and isinstance(data['ats_score'], int):
        variation = random.randint(-2, 2)
        data['ats_score'] = max(0, min(100, data['ats_score'] + variation))

    return data


def validate_no_fabrication(original_text: str, optimized_text: str) -> str:
    """Validate that AI hasn't fabricated data in optimized resume.

    Args:
        original_text: Original resume text.
        optimized_text: AI-optimized resume text.

    Returns:
        Validated text with fabricated data removed.
    """
    import re

    # Extract ALL numbers from original text
    original_numbers = set(re.findall(r'\d+', original_text))
    original_percentages = set(re.findall(r'(\d+)%', original_text))
    original_dollars = set(re.findall(r'\$[\d,]+', original_text))

    # Check for fabricated percentages
    percentages = re.findall(r'(\d+)%', optimized_text)
    for pct in percentages:
        if pct not in original_percentages and pct not in original_numbers:
            optimized_text = optimized_text.replace(f"{pct}%", "[USER_DATA]")

    # Check for fabricated dollar amounts
    dollar_amounts = re.findall(r'\$[\d,]+', optimized_text)
    for amt in dollar_amounts:
        clean_amt = amt.replace('$', '').replace(',', '')
        if clean_amt not in original_numbers and amt not in original_dollars:
            optimized_text = optimized_text.replace(amt, "[USER_DATA]")

    # Check for fabricated user counts
    user_counts = re.findall(r'(\d+)\s*(users|customers|employees|team)', optimized_text, re.IGNORECASE)
    for count, unit in user_counts:
        if count not in original_numbers:
            optimized_text = optimized_text.replace(f"{count} {unit}", f"[USER_DATA] {unit}")

    return optimized_text


def extract_original_numbers(text: str) -> dict:
    """Extract all numbers from original resume for validation.

    Args:
        text: Resume text.

    Returns:
        Dictionary with extracted numbers and their contexts.
    """
    import re

    numbers = {
        'percentages': re.findall(r'(\d+)%', text),
        'dollar_amounts': re.findall(r'\$[\d,]+', text),
        'user_counts': re.findall(r'(\d+)\s*(users|customers|employees)', text, re.IGNORECASE),
        'years': re.findall(r'(\d+)\s*(years?|yrs?)', text, re.IGNORECASE)
    }

    return numbers
