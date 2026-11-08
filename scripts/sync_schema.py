import asyncpg
import asyncio

async def main():
    conn = await asyncpg.connect('postgresql://postgres:lpdr%24A10207@db.yjdnjmfqhgnjmpgxktvc.supabase.co:5432/postgres')
    
    # 1. Add user_id to scans if missing
    await conn.execute("""
        ALTER TABLE public.scans 
        ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES public.users(id) ON DELETE CASCADE;
    """)
    print("Added user_id to public.scans")

    # 2. Add findings_count to scans if missing
    await conn.execute("""
        ALTER TABLE public.scans 
        ADD COLUMN IF NOT EXISTS findings_count INT NOT NULL DEFAULT 0;
    """)
    print("Added findings_count to public.scans")

    # 3. Add stage_message to scans if missing
    await conn.execute("""
        ALTER TABLE public.scans 
        ADD COLUMN IF NOT EXISTS stage_message TEXT DEFAULT 'Queued for security scan';
    """)
    print("Added stage_message to public.scans")

    # 4. Check reports columns
    await conn.execute("""
        ALTER TABLE public.reports 
        ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
        ADD COLUMN IF NOT EXISTS domain_id UUID REFERENCES public.domains(id) ON DELETE CASCADE,
        ADD COLUMN IF NOT EXISTS summary_json JSONB DEFAULT '{}'::jsonb;
    """)
    print("Checked public.reports columns")

    # 5. Reload PostgREST schema cache
    await conn.execute("NOTIFY pgrst, 'reload schema';")
    print("Reloaded PostgREST schema cache!")

    await conn.close()

if __name__ == '__main__':
    asyncio.run(main())
