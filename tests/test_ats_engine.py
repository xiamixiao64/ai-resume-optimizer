# tests/test_ats_engine.py
import pytest
from ats_engine import ATSEngine

def test_atsengine_initialization():
    engine = ATSEngine()
    assert engine.weights == {
        "formatting": 20,
        "keywords": 35,
        "experience": 25,
        "education": 10,
        "contact": 10
    }

def test_analyze_returns_dict():
    engine = ATSEngine()
    result = engine.analyze("Test resume", "Test JD")
    assert isinstance(result, dict)
    assert "ats_score" in result
    assert "breakdown" in result
    assert "improvements" in result

def test_formatting_check_ideal():
    engine = ATSEngine()
    resume = """
John Doe
john@email.com | (555) 123-4567 | LinkedIn: linkedin.com/in/johndoe

EXPERIENCE
Software Engineer | Google | 2020-2023
- Led development of microservices architecture
- Increased system performance by 40%

EDUCATION
BS Computer Science | Stanford University | 2020

SKILLS
Python, JavaScript, React, AWS, Docker
"""
    result = engine.check_formatting(resume)
    assert result["score"] >= 80
    assert len(result["issues"]) == 0

def test_formatting_check_issues():
    engine = ATSEngine()
    resume = """
John Doe
john@email.com

EXPERIENCE
- Did stuff
- Helped with things
- Was responsible for stuff
"""
    result = engine.check_formatting(resume)
    assert result["score"] < 80
    assert len(result["issues"]) > 0

def test_keywords_perfect_match():
    engine = ATSEngine()
    resume = """
Skills: Python, JavaScript, React, AWS, Docker, Git
"""
    jd = """
Requirements: Python, JavaScript, React, AWS, Docker, Git
"""
    result = engine.check_keywords(resume, jd)
    assert result["score"] >= 90
    assert len(result["missing"]) == 0

def test_keywords_partial_match():
    engine = ATSEngine()
    resume = """
Skills: Python, JavaScript
"""
    jd = """
Requirements: Python, JavaScript, React, AWS, Docker
"""
    result = engine.check_keywords(resume, jd)
    assert 40 <= result["score"] <= 80
    assert len(result["missing"]) >= 2
    assert "react" in result["missing"]
