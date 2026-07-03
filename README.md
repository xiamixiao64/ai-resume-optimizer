# ResumeForge AI

AI-powered resume optimizer that beats ATS systems.

## Features

- ATS Score Analysis (0-100)
- Smart Keyword Matching
- AI-Powered Resume Rewrite
- Job Description Targeting
- One-Click Copy
- Free tier (5 optimizations)
- Pro subscription ($9.9/month)

## Quick Start

```bash
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API keys
python app.py
```

Visit http://localhost:5000

## Environment Variables

```bash
# Required
GROQ_API_KEY=your-groq-api-key

# Optional (for payments)
LEMONSQUEEZY_API_KEY=your-lemonsqueezy-api-key
LEMONSQUEEZY_STORE_ID=your-store-id
LEMONSQUEEZY_VARIANT_ID=your-variant-id
FLASK_SECRET_KEY=your-secret-key
```

## API

```bash
curl -X POST http://localhost:5000/api/optimize \
  -H "Content-Type: application/json" \
  -d '{"resume": "your resume text", "job_description": "job desc"}'
```

## Payment Setup (LemonSqueezy)

1. Create account at https://www.lemonsqueezy.com
2. Create a product ($9.9/month subscription)
3. Get API key, Store ID, and Variant ID
4. Add to .env file
5. Set up webhook URL: `https://your-domain.com/api/webhook`
