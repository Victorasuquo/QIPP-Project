"""
Phase 0 — Database Connection Verification
Run: python scripts/verify_connections.py

Checks:
  1. PostgreSQL (Supabase) — counts rows in icbs, ods_organisations, interventions
  2. MongoDB Atlas — counts documents in opportunities, tariff_prices, patients
"""
import asyncio
import sys
import os

# Make sure we can import from app/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


async def verify_postgres():
    print("\n🐘 Testing PostgreSQL (Supabase)...")
    try:
        from sqlalchemy import text
        from app.database import engine

        async with engine.connect() as conn:
            checks = {
                "icbs": "SELECT COUNT(*) FROM icbs",
                "ods_organisations": "SELECT COUNT(*) FROM ods_organisations",
                "interventions": "SELECT COUNT(*) FROM interventions",
                "pcns": "SELECT COUNT(*) FROM pcns",
            }
            for table, query in checks.items():
                result = await conn.execute(text(query))
                count = result.scalar()
                print(f"   ✅ {table}: {count:,} rows")

    except Exception as e:
        print(f"   ❌ PostgreSQL connection FAILED: {e}")
        return False

    print("   📡 PostgreSQL connection OK")
    return True


async def verify_mongodb():
    print("\n🍃 Testing MongoDB Atlas...")
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        from app.config import settings

        client = AsyncIOMotorClient(settings.MONGODB_URI, serverSelectionTimeoutMS=5000)
        db = client[settings.MONGODB_DB_NAME]

        # Ping
        await client.admin.command("ping")

        checks = ["opportunities", "tariff_prices", "patients", "patient_analytics", "medications"]
        for col in checks:
            count = await db[col].count_documents({})
            print(f"   ✅ {col}: {count:,} documents")

        client.close()

    except Exception as e:
        print(f"   ❌ MongoDB connection FAILED: {e}")
        return False

    print("   📡 MongoDB connection OK")
    return True


async def main():
    print("=" * 55)
    print("  QIPP Phase 0 — Connection Verification")
    print("=" * 55)

    pg_ok = await verify_postgres()
    mg_ok = await verify_mongodb()

    print("\n" + "=" * 55)
    if pg_ok and mg_ok:
        print("  ✅  ALL CONNECTIONS HEALTHY — ready for Phase 1!")
    else:
        print("  ❌  Some connections failed — check .env and network")
    print("=" * 55)


if __name__ == "__main__":
    asyncio.run(main())
