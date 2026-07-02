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
