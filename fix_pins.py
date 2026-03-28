#!/usr/bin/env python3
"""
Test PIN hashing and update database if needed
Run this in your backend virtual environment
"""

import asyncio
import os
import sys
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select, update
from passlib.context import CryptContext
from dotenv import load_dotenv
import re
import ssl

# Load env
load_dotenv()

# Setup auth
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,
)

# Setup database
DATABASE_URL = os.getenv("DATABASE_URL", "")

if DATABASE_URL.startswith("postgresql://"):
    ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
elif DATABASE_URL.startswith("postgresql+asyncpg://"):
    ASYNC_DATABASE_URL = DATABASE_URL
else:
    ASYNC_DATABASE_URL = DATABASE_URL

# Remove query params
ASYNC_DATABASE_URL = re.sub(r'[&?]sslmode=[^&]*', '', ASYNC_DATABASE_URL)
ASYNC_DATABASE_URL = re.sub(r'[&?]channel_binding=[^&]*', '', ASYNC_DATABASE_URL)
ASYNC_DATABASE_URL = ASYNC_DATABASE_URL.rstrip('?&')

print(f"📊 Database URL: {ASYNC_DATABASE_URL[:50]}...")

# SSL
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

# Engine
engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=False,
    future=True,
    poolclass=None,
    connect_args={"ssl": ssl_context},
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def fix_pins():
    """Fix PIN hashes in database"""
    print("\n🔧 PIN Hash Verification Tool\n")
    print("=" * 60)

    # Test PIN locally first
    test_pin = "123456"
    hashed = pwd_context.hash(test_pin)
    print(f"\n1️⃣  Generated hash for '123456':")
    print(f"   {hashed}")
    print(f"   Verifies: {pwd_context.verify(test_pin, hashed)} ✅")

    # Connect and check database
    async with AsyncSessionLocal() as session:
        print(f"\n2️⃣  Checking database users...")

        # Import models
        from models import User

        result = await session.execute(select(User))
        users = result.scalars().all()

        print(f"   Found {len(users)} users:")
        for user in users:
            print(f"   - {user.phone}: {user.name} ({user.role})")
            
            # Test if PIN "123456" works with current hash
            try:
                is_valid = pwd_context.verify(test_pin, user.pin_hash)
                status = "✅ WORKS" if is_valid else "❌ MISMATCH"
                print(f"     Hash: {user.pin_hash[:30]}...")
                print(f"     PIN '123456' verification: {status}")
            except Exception as e:
                print(f"     ❌ Error: {e}")

        # Option to fix
        print(f"\n3️⃣  Fixing ALL user PIN hashes to '123456'...")
        try:
            # Update all users with the correct hash
            stmt = update(User).values(pin_hash=hashed)
            result = await session.execute(stmt)
            await session.commit()
            print(f"   ✅ Updated {result.rowcount} users with correct PIN hash")
        except Exception as e:
            print(f"   ❌ Error updating: {e}")
            await session.rollback()
            return False

        # Verify fix
        print(f"\n4️⃣  Verifying fix...")
        result = await session.execute(select(User))
        users = result.scalars().all()

        for user in users:
            try:
                is_valid = pwd_context.verify(test_pin, user.pin_hash)
                status = "✅" if is_valid else "❌"
                print(f"   {user.phone}: {status}")
            except Exception as e:
                print(f"   {user.phone}: ❌ {e}")

    print(f"\n✅ Done!\n")
    return True


if __name__ == "__main__":
    try:
        success = asyncio.run(fix_pins())
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
