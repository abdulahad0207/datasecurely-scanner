-- Migration: 006_monitoring_schema.sql
-- Description: Continuous Monitoring & Vulnerability Diffing schema with Row Level Security (RLS)

-- 1. Add monitoring columns to domains
ALTER TABLE public.domains ADD COLUMN IF NOT EXISTS is_monitored BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE public.domains ADD COLUMN IF NOT EXISTS last_monitored_at TIMESTAMPTZ;

-- 2. Scan Diffs table
CREATE TABLE IF NOT EXISTS public.scan_diffs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    scan_id UUID NOT NULL REFERENCES public.scans(id) ON DELETE CASCADE,
    previous_scan_id UUID REFERENCES public.scans(id) ON DELETE SET NULL,
    domain_id UUID NOT NULL REFERENCES public.domains(id) ON DELETE CASCADE,
    grade_change TEXT NOT NULL DEFAULT 'unchanged' CHECK (grade_change IN ('improved', 'degraded', 'unchanged', 'first_scan')),
    new_findings_count INTEGER NOT NULL DEFAULT 0,
    resolved_findings_count INTEGER NOT NULL DEFAULT 0,
    persistent_findings_count INTEGER NOT NULL DEFAULT 0,
    diff_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    CONSTRAINT unique_scan_diff UNIQUE (scan_id)
);

CREATE INDEX IF NOT EXISTS idx_scan_diffs_domain_id ON public.scan_diffs(domain_id);
CREATE INDEX IF NOT EXISTS idx_scan_diffs_scan_id ON public.scan_diffs(scan_id);

-- Enable RLS for scan_diffs
ALTER TABLE public.scan_diffs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view diffs for own domains"
    ON public.scan_diffs FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.domains
            WHERE domains.id = scan_diffs.domain_id
            AND domains.user_id = auth.uid()
        )
    );
