"""
Reset a user's password in Supabase.
Run from qippsystem/ root:
    python backend\scripts\reset_password.py

Defaults to resetting admin@qipp.nhs.uk password to: Admin1234!
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# ── Configure these ────────────────────────────────────────────────────────────
TARGET_EMAIL = "Marvel@southyorkshire.icb.nhs.uk"   # Change to whichever user you want
NEW_PASSWORD = "QippTest2026!"
# ──────────────────────────────────────────────────────────────────────────────


async def main():
    from sqlalchemy import text
    from app.database import engine
    from app.core.security import hash_password

    hashed = hash_password(NEW_PASSWORD)

    print(f"\n  Resetting password for: {TARGET_EMAIL}")
    print(f"  New password will be:   {NEW_PASSWORD}\n")

    async with engine.begin() as conn:
        result = await conn.execute(
            text("UPDATE users SET password_hash = :pw WHERE LOWER(email) = LOWER(:email) RETURNING id, email, role"),
            {"pw": hashed, "email": TARGET_EMAIL},
        )
        row = result.fetchone()
        if row:
            print(f"  ✅ Password reset for: {row.email} (role: {row.role})")
            print(f"\n  Login at: http://localhost:8000/api/docs")
            print(f"  Email:    {TARGET_EMAIL}")
            print(f"  Password: {NEW_PASSWORD}\n")
        else:
            print(f"  ❌ User not found: {TARGET_EMAIL}")
            print(f"     Check spelling — emails are case-insensitive.\n")


if __name__ == "__main__":
    asyncio.run(main())
