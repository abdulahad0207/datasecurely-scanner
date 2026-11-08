import asyncpg
import asyncio

async def main():
    conn = await asyncpg.connect('postgresql://postgres:lpdr%24A10207@db.yjdnjmfqhgnjmpgxktvc.supabase.co:5432/postgres')
    rows = await conn.fetch("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_schema = 'public' AND table_name = 'scans';
    """)
    print("Columns in scans:")
    for r in rows:
        print(f"  {r['column_name']} ({r['data_type']})")

    # If stage_message is missing, add it
    col_names = [r['column_name'] for r in rows]
    if 'stage_message' not in col_names:
        print("Adding stage_message column to public.scans...")
        await conn.execute("ALTER TABLE public.scans ADD COLUMN stage_message TEXT DEFAULT 'Queued for security scan';")
        print("Added stage_message!")

    # Check findings table columns
    f_rows = await conn.fetch("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_schema = 'public' AND table_name = 'findings';
    """)
    print("Columns in findings:")
    for r in f_rows:
        print(f"  {r['column_name']} ({r['data_type']})")

    # Check reports table columns
    rep_rows = await conn.fetch("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_schema = 'public' AND table_name = 'reports';
    """)
    print("Columns in reports:")
    for r in rep_rows:
        print(f"  {r['column_name']} ({r['data_type']})")

    # Notify PostgREST to reload schema cache
    await conn.execute("NOTIFY pgrst, 'reload schema';")
    print("Reloaded PostgREST schema cache!")

    await conn.close()

if __name__ == '__main__':
    asyncio.run(main())
