-- ResumeForge AI - Supabase Schema
-- Run this in Supabase SQL Editor

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    usage_count INTEGER DEFAULT 0,
    is_pro BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- Optimization history table
CREATE TABLE IF NOT EXISTS optimizations (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id),
    resume_text TEXT,
    job_description TEXT,
    mode TEXT,
    result JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_opt_user ON optimizations(user_id);
CREATE INDEX IF NOT EXISTS idx_opt_created ON optimizations(created_at);

-- Events tracking table
CREATE TABLE IF NOT EXISTS events (
    id SERIAL PRIMARY KEY,
    user_id TEXT,
    event_type TEXT NOT NULL,
    event_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_evt_type ON events(event_type);
CREATE INDEX IF NOT EXISTS idx_evt_created ON events(created_at);
CREATE INDEX IF NOT EXISTS idx_evt_user ON events(user_id);

-- Enable Row Level Security (recommended for production)
-- ALTER TABLE users ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE optimizations ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE events ENABLE ROW LEVEL SECURITY;
