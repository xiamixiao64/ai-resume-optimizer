"""
ATS Engine - Open Source Resume Analyzer

A Python library for analyzing resumes against ATS (Applicant Tracking Systems).
"""

import sys
import os

# Try to import from the main project's ats_engine.py (root level)
# This avoids code duplication when used within the project
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _root not in sys.path:
    sys.path.insert(0, _root)

try:
    # Import from root ats_engine.py (the authoritative version)
    import importlib
    _mod = importlib.import_module("ats_engine")
    ATSEngine = _mod.ATSEngine
except (ImportError, AttributeError):
    # Standalone mode: use local implementation
    from .engine import ATSEngine

__version__ = "1.0.0"
__author__ = "ResumeForge AI"

__all__ = ["ATSEngine"]
