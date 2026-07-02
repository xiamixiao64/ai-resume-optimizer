# ResumeForge AI - Setup Guide

## 1. Supabase Setup (Database)

### Step 1: Create Supabase Account
1. Go to https://supabase.com
2. Sign up for free
3. Create a new project

### Step 2: Get API Keys
1. Go to Project Settings → API
2. Copy:
   - Project URL (looks like: https://xxxxx.supabase.co)
   - Anon Key (public key)

### Step 3: Create Users Table
1. Go to SQL Editor
2. Paste the contents of `supabase-schema.sql`
3. Click "Run"

## 2. Environment Variables

Create `.env` file:
```bash
cp .env.example .env
```

Edit `.env`:
```
GROQ_API_KEY=your-groq-api-key
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=your-anon-key
FLASK_SECRET_KEY=any-random-string
```

## 3. Run Locally

```bash
pip install -r requirements.txt
python app.py
```

Visit http://localhost:5000

## 4. Deploy to Vercel

1. Push to GitHub
2. Go to vercel.com
3. Import your repo
4. Add environment variables in Vercel dashboard
5. Deploy

## 5. LemonSqueezy Setup (Optional - for payments)

1. Go to https://www.lemonsqueezy.com
2. Create account
3. Create a product ($9.9/month)
4. Get API Key, Store ID, Variant ID
5. Add to `.env`
6. Set webhook URL in LemonSqueezy: `https://your-domain.vercel.app/api/webhook`
