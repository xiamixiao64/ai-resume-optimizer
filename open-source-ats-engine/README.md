# ATS Engine - Open Source Resume Analyzer

A Python library for analyzing resumes against ATS (Applicant Tracking Systems).

## Features

- **12 ATS Type Detection**: Identify which ATS system a job posting uses (Workday, Taleo, Greenhouse, Lever, iCIMS, etc.)
- **Resume Scoring**: Get a 0-100 score for ATS compatibility
- **Keyword Matching**: Semantic matching between resume and job description
- **X-Y-Z Format Detection**: Check if bullet points follow the impact format
- **Portfolio Link Detection**: Check for GitHub, LinkedIn, and personal website links

## Installation

```bash
pip install ats-engine
```

Or install from source:

```bash
git clone https://github.com/yourusername/ats-engine.git
cd ats-engine
pip install -e .
```

## Quick Start

```python
from ats_engine import ATSEngine

engine = ATSEngine()

# Analyze a resume
resume_text = """
John Doe
john@example.com | (555) 123-4567

EXPERIENCE
Software Engineer | Google | 2020-2023
- Led development of React dashboard serving 10M users
- Increased API performance by 40% through optimization
- Managed team of 5 engineers

EDUCATION
BS Computer Science | Stanford University | 2020

SKILLS
Python, JavaScript, React, AWS, Docker
"""

job_description = """
Senior Software Engineer at Tech Company
Requirements: Python, React, AWS, 5+ years experience
"""

result = engine.analyze(resume_text, job_description)

print(f"ATS Score: {result['ats_score']}/100")
print(f"Detected ATS: {result['ats_type']['type']}")
print(f"Improvements: {result['improvements']}")
```

## ATS Type Detection

```python
# Detect which ATS a job posting uses
jd_text = "Apply through Workday at company.wd5.myworkdayjobs.com"
ats_type = engine.identify_ats(jd_text)

print(f"ATS: {ats_type['type']}")  # Output: ATS: workday
print(f"Tips: {ats_type['tips']}")
```

## Supported ATS Systems

| ATS System | Patterns Detected |
|------------|-------------------|
| Workday | workday, myworkdayjobs, wd5.myworkday, wday.com |
| Taleo | taleo, oracle.com/taleo, talent.oracle |
| Greenhouse | greenhouse.io, boards.greenhouse, greenhouse.com |
| Lever | lever.co, jobs.lever |
| iCIMS | icims.com, jobs.icims |
| SmartRecruiters | smartrecruiters, smartrecruiters.com |
| BambooHR | bamboohr.com, bamboo hr |
| SuccessFactors | successfactors, sap.com/careers |
| JobVite | jobvite.com, jobvite |
| ApplicantStack | applicantstack.com, applicantstack |
| Bullhorn | bullhorn.com, bullhorn |
| ClearCompany | clearcompany.com, clearcompany |

## Score Breakdown

The analysis returns scores for each category:

```python
result = engine.analyze(resume_text, jd_text)

# Score breakdown
print(result['breakdown'])
# {
#     'formatting': {'score': 85, 'issues': [...]},
#     'keywords': {'score': 72, 'matched': [...], 'missing': [...]},
#     'semantic_match': {'score': 68, 'text_similarity': 45.2, ...},
#     'experience': {'score': 90, 'issues': [...], 'xyz_count': 3},
#     'education': {'score': 100, 'issues': []},
#     'contact': {'score': 75, 'issues': [...]},
#     'portfolio': {'score': 50, 'issues': [...], 'links': [...]}
# }
```

## X-Y-Z Format

The engine checks if bullet points follow the X-Y-Z impact format:

- **X**: What you did (action verb)
- **Y**: How you did it (method/tools)
- **Z**: The result (quantified impact)

Example:
- ❌ "Worked on frontend development"
- ✅ "Built React component library reducing load time by 40%"

## Use Cases

- **Job Seekers**: Check your resume before applying
- **Career Coaches**: Analyze client resumes
- **Recruiters**: Verify resume quality
- **Developers**: Build resume optimization tools

## API Reference

### `ATSEngine()`

Create a new engine instance.

### `engine.analyze(resume_text, jd_text)`

Analyze a resume against a job description.

**Parameters:**
- `resume_text` (str): The resume content
- `jd_text` (str): The job description

**Returns:**
- `dict`: Analysis result with score, breakdown, improvements, and ATS type

### `engine.identify_ats(jd_text)`

Identify which ATS system a job posting uses.

**Parameters:**
- `jd_text` (str): The job description or URL

**Returns:**
- `dict`: ATS type, confidence, and tips

### `engine.check_formatting(resume_text)`

Check resume formatting compatibility.

### `engine.check_keywords(resume_text, jd_text)`

Check keyword matching between resume and job description.

### `engine.check_experience(resume_text)`

Check work experience quality and X-Y-Z format.

### `engine.check_education(resume_text)`

Check education section.

### `engine.check_contact(resume_text)`

Check contact information.

### `engine.check_portfolio(resume_text)`

Check for portfolio and online presence links.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built as part of [ResumeForge AI](https://resumeforge.ai)
- Inspired by the need for transparent, open-source resume analysis tools
