"""
Inspect real column names in Supabase users table.
Run from qippsystem/ root:
    python backend\scripts\inspect_users_table.py
"""
import asyncio, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

async def main():
    from sqlalchemy import text
    from app.database import engine

    async with engine.connect() as conn:
        result = await conn.execute(text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'users'
            ORDER BY ordinal_position
        """))
        rows = result.fetchall()
        print("\n=== users table columns ===")
        for row in rows:
            print(f"  {row.column_name:35s} {row.data_type:20s} nullable={row.is_nullable}")
        print()

if __name__ == "__main__":
    asyncio.run(main())
