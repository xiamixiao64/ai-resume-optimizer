# ResumeForge AI

AI-powered resume optimizer that beats ATS systems.

## Features

- ATS Score Analysis (0-100)
- Smart Keyword Matching
- AI-Powered Resume Rewrite
- Job Description Targeting
- One-Click Copy

## Quick Start

```bash
pip install -r requirements.txt
export OPENAI_API_KEY=your-key-here
python app.py
```

Visit http://localhost:5000

## API

```bash
curl -X POST http://localhost:5000/api/optimize \
  -H "Content-Type: application/json" \
  -d '{"resume": "your resume text", "job_description": "job desc"}'
```
