"""
Check what users exist in Supabase so we know what email/password to use for login.
Run from qippsystem/ root:
    python backend\scripts\check_users.py
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


async def main():
    from sqlalchemy import text
    from app.database import engine

    print("\n" + "=" * 60)
    print("  Supabase Users Table — Login Credentials Check")
    print("=" * 60)

    async with engine.connect() as conn:
        # Show all users
        result = await conn.execute(text("""
            SELECT 
                id,
                email,
                first_name,
                last_name,
                role,
                is_active,
                tenant_id,
                practice_ods_code,
                created_at
            FROM users
            ORDER BY created_at
        """))
        rows = result.fetchall()

        if not rows:
            print("\n  ❌  No users found in the database!")
            print("  → Run: python backend\\scripts\\seed_south_yorkshire.py")
        else:
            print(f"\n  Found {len(rows)} user(s):\n")
            for row in rows:
                print(f"  Email    : {row.email}")
                print(f"  Name     : {row.first_name or ''} {row.last_name}")
                print(f"  Role     : {row.role}")
                print(f"  Active   : {row.is_active}")
                print(f"  Tenant   : {row.tenant_id}")
                print(f"  Created  : {row.created_at}")
                print("  " + "-" * 40)

        # Also show hashed password hint
        if rows:
            print("\n  NOTE: Passwords are bcrypt-hashed in the DB.")
            print("  If you don't know the password, run the reset script below.\n")

    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
