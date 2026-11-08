-- Migration: 007_update_users_plan_constraint.sql
-- Description: Expand users.plan to TEXT with CHECK constraint supporting 'free', 'full', 'pro', 'business', and 'monitor'

-- 1. Ensure column is TEXT type (converting from legacy userplan enum if needed)
ALTER TABLE public.users ALTER COLUMN plan DROP DEFAULT;
ALTER TABLE public.users ALTER COLUMN plan TYPE TEXT USING plan::text;
ALTER TABLE public.users ALTER COLUMN plan SET DEFAULT 'free';

-- 2. Drop existing constraint if it exists
ALTER TABLE public.users DROP CONSTRAINT IF EXISTS users_plan_check;

-- 3. Add the updated CHECK constraint with all supported billing tiers
ALTER TABLE public.users ADD CONSTRAINT users_plan_check 
    CHECK (plan IN ('free', 'full', 'pro', 'business', 'monitor'));
