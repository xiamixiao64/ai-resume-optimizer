-- ResumeForge AI - Supabase Database Schema
-- Run this in Supabase SQL Editor

-- 用户表
CREATE TABLE IF NOT EXISTS users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL,
  usage_count INTEGER DEFAULT 0,
  is_pro BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT NOW()
);

-- 事件追踪表
CREATE TABLE IF NOT EXISTS events (
  id SERIAL PRIMARY KEY,
  user_id UUID,
  event_type TEXT NOT NULL,
  event_data JSONB DEFAULT '{}',
  created_at TIMESTAMP DEFAULT NOW()
);

-- 优化历史表
CREATE TABLE IF NOT EXISTS optimizations (
  id TEXT PRIMARY KEY,
  user_id UUID,
  resume_text TEXT,
  job_description TEXT,
  mode TEXT,
  result JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);

-- 求职申请追踪表
CREATE TABLE IF NOT EXISTS job_applications (
  id TEXT PRIMARY KEY,
  user_id UUID,
  company TEXT NOT NULL,
  position TEXT NOT NULL,
  job_url TEXT,
  notes TEXT,
  status TEXT DEFAULT 'applied',
  ats_score INTEGER,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_events_user_id ON events(user_id);
CREATE INDEX IF NOT EXISTS idx_events_created_at ON events(created_at);
CREATE INDEX IF NOT EXISTS idx_optimizations_user_id ON optimizations(user_id);
CREATE INDEX IF NOT EXISTS idx_job_applications_user_id ON job_applications(user_id);

-- 启用Row Level Security (可选)
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE events ENABLE ROW LEVEL SECURITY;
ALTER TABLE optimizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE job_applications ENABLE ROW LEVEL SECURITY;
