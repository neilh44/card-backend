-- ============================================================
-- CardCraft — Supabase Schema
-- Run this in: Supabase Dashboard → SQL Editor → New Query
-- ============================================================


-- ── Orders Table ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS orders (
    id                  UUID PRIMARY KEY,
    user_id             UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    session_id          TEXT,
    selected_design_id  TEXT NOT NULL,
    pdf_url             TEXT NOT NULL,
    status              TEXT NOT NULL DEFAULT 'completed',
    user_info           JSONB NOT NULL DEFAULT '{}',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index for fast user order lookups
CREATE INDEX IF NOT EXISTS orders_user_id_idx ON orders(user_id);
CREATE INDEX IF NOT EXISTS orders_created_at_idx ON orders(created_at DESC);


-- ── Row Level Security ────────────────────────────────────────
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;

-- Service role (backend) can do everything
CREATE POLICY "Service role full access"
    ON orders
    FOR ALL
    USING (true)
    WITH CHECK (true);

-- Authenticated users can view their own orders
CREATE POLICY "Users can view own orders"
    ON orders
    FOR SELECT
    TO authenticated
    USING (auth.uid() = user_id);


-- ── Storage Bucket ─────────────────────────────────────────────
-- Run this separately or create manually in Storage dashboard:
-- Bucket name: card-pdfs
-- Public: true

INSERT INTO storage.buckets (id, name, public)
VALUES ('card-pdfs', 'card-pdfs', true)
ON CONFLICT (id) DO NOTHING;

-- Allow public read of PDFs
CREATE POLICY "Public PDF read"
    ON storage.objects
    FOR SELECT
    USING (bucket_id = 'card-pdfs');

-- Allow service role to upload PDFs
CREATE POLICY "Service role upload"
    ON storage.objects
    FOR INSERT
    WITH CHECK (bucket_id = 'card-pdfs');
