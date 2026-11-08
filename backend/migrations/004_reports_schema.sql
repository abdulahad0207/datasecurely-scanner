-- Migration: 004_reports_schema.sql
-- Description: Reports table with Row Level Security (RLS)

CREATE TABLE IF NOT EXISTS public.reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    scan_id UUID NOT NULL REFERENCES public.scans(id) ON DELETE CASCADE,
    language TEXT NOT NULL DEFAULT 'en' CHECK (language IN ('en', 'hi-Latn')),
    pdf_url TEXT,
    html_url TEXT,
    summary_json JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    CONSTRAINT unique_scan_language UNIQUE (scan_id, language)
);

CREATE INDEX IF NOT EXISTS idx_reports_scan_id ON public.reports(scan_id);

-- Enable RLS for reports
ALTER TABLE public.reports ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view reports for own scans"
    ON public.reports FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.scans
            WHERE scans.id = reports.scan_id
            AND scans.user_id = auth.uid()
        )
    );
