"""AI/LLM integration service"""
import os
import json
import logging
from typing import Optional
import requests as std_requests

logger = logging.getLogger(__name__)

GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-versatile"


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
