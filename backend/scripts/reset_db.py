#!/usr/bin/env python3
"""
Reset database: drop all tables and recreate schema.

Usage:
  cd backend && source venv/bin/activate
  python scripts/reset_db.py
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import settings
from app.core.database import Base


async def main():
    print("WARNING: This will delete ALL data in the database!")
    print(f"Database: {settings.DATABASE_URL}")

    # Confirm before proceeding
    if "--force" not in sys.argv:
        response = input("Are you sure you want to continue? (yes/no): ")
        if response.lower() not in ["yes", "y"]:
            print("Operation cancelled.")
            return

    engine = create_async_engine(settings.DATABASE_URL)

    print("\nDropping all tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    print("[OK] All tables dropped.")

    print("\nRecreating tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("[OK] Tables recreated.")

    await engine.dispose()

    print("\n✓ Database reset complete!")
    print("\nNext steps:")
    print("  - Run 'python scripts/init_db.py' to initialize with test data")
    print("  - Or run 'python scripts/seed.py' for sample recipes")


if __name__ == "__main__":
    asyncio.run(main())
