-- Migration: 002_scans_schema.sql
-- Description: Scans table and Row Level Security (RLS)

CREATE TABLE IF NOT EXISTS public.scans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    domain_id UUID NOT NULL REFERENCES public.domains(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    profile TEXT NOT NULL DEFAULT 'free' CHECK (profile IN ('free', 'full', 'monitor')),
    status TEXT NOT NULL DEFAULT 'queued' CHECK (status IN ('queued', 'recon', 'scanning', 'scoring', 'completed', 'failed', 'cancelled')),
    progress INT NOT NULL DEFAULT 0 CHECK (progress >= 0 AND progress <= 100),
    stage_message TEXT DEFAULT 'Queued for security scan',
    grade TEXT CHECK (grade IN ('A', 'B', 'C', 'D', 'F', NULL)),
    findings_count INT NOT NULL DEFAULT 0,
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- Indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_scans_user_id ON public.scans(user_id);
CREATE INDEX IF NOT EXISTS idx_scans_domain_id ON public.scans(domain_id);
CREATE INDEX IF NOT EXISTS idx_scans_status ON public.scans(status);

-- Enable RLS for scans
ALTER TABLE public.scans ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own scans"
    ON public.scans FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can create own scans"
    ON public.scans FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own scans"
    ON public.scans FOR UPDATE
    USING (auth.uid() = user_id);
