-- Migration: 003_findings_schema.sql
-- Description: Findings table with Row Level Security (RLS) and unique fingerprint constraint

CREATE TABLE IF NOT EXISTS public.findings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    scan_id UUID NOT NULL REFERENCES public.scans(id) ON DELETE CASCADE,
    source_tool TEXT NOT NULL,
    template_id TEXT NOT NULL,
    title TEXT NOT NULL,
    severity TEXT NOT NULL CHECK (severity IN ('info', 'low', 'medium', 'high', 'critical')),
    host TEXT NOT NULL,
    evidence TEXT,
    raw_ref TEXT,
    ai_json JSONB,
    fingerprint TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    CONSTRAINT unique_scan_fingerprint UNIQUE (scan_id, fingerprint)
);

-- Indexes for performant lookups
CREATE INDEX IF NOT EXISTS idx_findings_scan_id ON public.findings(scan_id);
CREATE INDEX IF NOT EXISTS idx_findings_severity ON public.findings(severity);
CREATE INDEX IF NOT EXISTS idx_findings_fingerprint ON public.findings(fingerprint);

-- Enable RLS for findings
ALTER TABLE public.findings ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view findings for own scans"
    ON public.findings FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.scans
            WHERE scans.id = findings.scan_id
            AND scans.user_id = auth.uid()
        )
    );
