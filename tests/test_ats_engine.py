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

def test_experience_strong():
    engine = ATSEngine()
    resume = """
EXPERIENCE
Senior Software Engineer | Meta | 2021-2024
- Led development of React-based dashboard serving 10M users
- Increased API performance by 45% through optimization
- Managed team of 5 engineers across 3 projects

Software Engineer | Startup | 2019-2021
- Built microservices architecture handling 1M requests/day
- Reduced infrastructure costs by 30% using AWS
"""
    result = engine.check_experience(resume)
    assert result["score"] >= 80
    assert len(result["issues"]) == 0

def test_experience_weak():
    engine = ATSEngine()
    resume = """
EXPERIENCE
Worked at company
- Did stuff
- Helped with things
- Was responsible for things
"""
    result = engine.check_experience(resume)
    assert result["score"] < 60
    assert len(result["issues"]) >= 2

# ---- Education Tests ----

def test_education_complete():
    engine = ATSEngine()
    resume = """
EDUCATION
BS Computer Science | Stanford University | 2020
GPA: 3.8/4.0
"""
    result = engine.check_education(resume)
    assert result["score"] >= 80

def test_education_missing_degree():
    engine = ATSEngine()
    resume = """
EDUCATION
Stanford University | 2020
"""
    result = engine.check_education(resume)
    assert result["score"] < 80
    assert any("学位" in i for i in result["issues"])

def test_education_no_section():
    engine = ATSEngine()
    resume = """
John Doe
Software Engineer
"""
    result = engine.check_education(resume)
    assert result["score"] == 50

# ---- Contact Tests ----

def test_contact_complete():
    engine = ATSEngine()
    resume = """
John Doe
john@email.com | (555) 123-4567 | San Francisco, CA
LinkedIn: linkedin.com/in/johndoe | GitHub: github.com/johndoe
"""
    result = engine.check_contact(resume)
    assert result["score"] >= 90

def test_contact_incomplete():
    engine = ATSEngine()
    resume = """
John Doe
"""
    result = engine.check_contact(resume)
    assert result["score"] < 50

def test_contact_partial():
    engine = ATSEngine()
    resume = """
John Doe
john@email.com | (555) 123-4567
"""
    result = engine.check_contact(resume)
    assert 50 <= result["score"] <= 75
    assert len(result["issues"]) >= 1

# ---- ATS Type Identification Tests ----

def test_identify_workday():
    engine = ATSEngine()
    jd = "Apply at https://wd5.myworkdayjobs.com/en-US/Google"
    result = engine.identify_ats(jd)
    assert result["type"] == "workday"
    assert result["confidence"] > 0.7

def test_identify_lever():
    engine = ATSEngine()
    jd = "Apply at https://jobs.lever.co/company/123"
    result = engine.identify_ats(jd)
    assert result["type"] == "lever"

def test_identify_greenhouse():
    engine = ATSEngine()
    jd = "Apply at https://boards.greenhouse.io/company"
    result = engine.identify_ats(jd)
    assert result["type"] == "greenhouse"
    assert result["confidence"] > 0.7

def test_identify_icims():
    engine = ATSEngine()
    jd = "Apply at https://jobs.icims.com/company"
    result = engine.identify_ats(jd)
    assert result["type"] == "icims"
    assert result["confidence"] > 0.7

def test_identify_taleo():
    engine = ATSEngine()
    jd = "Apply at https://oracle.com/taleo/company"
    result = engine.identify_ats(jd)
    assert result["type"] == "taleo"
    assert result["confidence"] > 0.7

def test_identify_smartrecruiters():
    engine = ATSEngine()
    jd = "Apply at https://smartrecruiters.com/company"
    result = engine.identify_ats(jd)
    assert result["type"] == "smartrecruiters"
    assert result["confidence"] > 0.7

def test_identify_unknown():
    engine = ATSEngine()
    jd = "Please send your resume to hr@company.com"
    result = engine.identify_ats(jd)
    assert result["type"] == "unknown"

# ---- Full Analysis Tests ----

def test_full_analysis():
    engine = ATSEngine()
    resume = """
John Doe
john@email.com | (555) 123-4567 | LinkedIn: linkedin.com/in/johndoe

EXPERIENCE
Senior Software Engineer | Google | 2021-2024
- Led development of microservices architecture serving 10M users
- Increased API performance by 45% through optimization
- Managed team of 5 engineers across 3 projects

EDUCATION
BS Computer Science | Stanford University | 2020

SKILLS
Python, JavaScript, React, AWS, Docker, Git
"""
    jd = """
Requirements: Python, JavaScript, React, AWS, Docker
"""
    result = engine.analyze(resume, jd)

    assert "ats_score" in result
    assert 0 <= result["ats_score"] <= 100
    assert "breakdown" in result
    assert "formatting" in result["breakdown"]
    assert "keywords" in result["breakdown"]
    assert "experience" in result["breakdown"]
    assert "education" in result["breakdown"]
    assert "contact" in result["breakdown"]
    assert "improvements" in result
    assert isinstance(result["improvements"], list)
    assert "ats_type" in result

def test_full_analysis_score_is_weighted():
    engine = ATSEngine()
    resume = """
John Doe
john@email.com | (555) 123-4567 | San Francisco, CA
LinkedIn: linkedin.com/in/johndoe

EXPERIENCE
Software Engineer | Tech Corp | 2020-2023
- Built REST APIs serving 1M daily requests
- Reduced response time by 60%
- Led team of 4 engineers

EDUCATION
BS Computer Science | MIT | 2020

SKILLS
Python, JavaScript, React, AWS, Docker, Git
"""
    jd = "Requirements: Python, JavaScript, React, AWS"
    result = engine.analyze(resume, jd)

    breakdown = result["breakdown"]
    total_from_breakdown = (
        breakdown["formatting"]["score"] * engine.weights["formatting"] / 100 +
        breakdown["keywords"]["score"] * engine.weights["keywords"] / 100 +
        breakdown["experience"]["score"] * engine.weights["experience"] / 100 +
        breakdown["education"]["score"] * engine.weights["education"] / 100 +
        breakdown["contact"]["score"] * engine.weights["contact"] / 100
    )
    assert result["ats_score"] == round(total_from_breakdown)

def test_full_analysis_improvements_prioritized():
    engine = ATSEngine()
    resume = "Just some random text without proper format"
    jd = "Requirements: Python, JavaScript, React"
    result = engine.analyze(resume, jd)

    assert len(result["improvements"]) > 0
    assert len(result["improvements"]) <= 6

# ---- Edge Cases ----

def test_empty_resume():
    engine = ATSEngine()
    result = engine.analyze("", "Job description")
    assert result["ats_score"] < 50
    assert len(result["improvements"]) > 0

def test_empty_jd():
    engine = ATSEngine()
    result = engine.analyze("John Doe\njohn@email.com\nEXPERIENCE\n- Built stuff", "")
    assert result["ats_score"] >= 50

def test_long_resume():
    engine = ATSEngine()
    resume = "EXPERIENCE\n" + "\n".join(["- " + "word " * 25 for _ in range(60)])
    result = engine.analyze(resume, "Python developer")
    assert any("过长" in i for i in result["breakdown"]["formatting"]["issues"])

def test_only_contact():
    engine = ATSEngine()
    resume = "john@email.com | (555) 123-4567 | LinkedIn: linkedin.com/in/john"
    result = engine.analyze(resume, "Python developer")
    assert result["breakdown"]["contact"]["score"] >= 75

def test_chinese_resume():
    from tests.test_data import STRONG_RESUME_CN
    engine = ATSEngine()
    result = engine.analyze(STRONG_RESUME_CN, "Python developer")
    assert 0 <= result["ats_score"] <= 100
    assert "breakdown" in result

# ---- Performance Tests ----

import time

def test_performance():
    from tests.test_data import STRONG_RESUME, JD_WITH_ATS
    engine = ATSEngine()

    start = time.time()
    for _ in range(100):
        engine.analyze(STRONG_RESUME, JD_WITH_ATS)
    end = time.time()

    avg_time = (end - start) / 100
    assert avg_time < 0.1  # <100ms per analysis
