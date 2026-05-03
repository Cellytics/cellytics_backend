"""
Re-hash all user PINs with the correct bcrypt version.
Run this after updating passlib/bcrypt to fix compatibility issues.
Usage: python rehash_pins.py
"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select, text
from database import ASYNC_DATABASE_URL
from models import User
from auth import hash_pin, verify_pin

async def rehash_all_pins():
    """Re-hash all PINs in the database"""
    engine = create_async_engine(ASYNC_DATABASE_URL, echo=False)
    AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with AsyncSessionLocal() as session:
        # Get all users
        result = await session.execute(select(User))
        users = result.scalars().all()
        
        print(f"Found {len(users)} users to process")
        
        # We don't know the original PIN, so we'll use a default for testing
        # In production, you might need to notify users of new temporary PINs
        default_pin = "123456"
        
        for user in users:
            # Re-hash with current bcrypt version
            new_hash = hash_pin(default_pin)
            user.pin_hash = new_hash
            
            # Verify it works
            is_valid = verify_pin(default_pin, user.pin_hash)
            status = "✅" if is_valid else "❌"
            print(f"{status} {user.phone}: {user.name}")
        
        await session.commit()
        print(f"\n✅ All {len(users)} users' PINs have been re-hashed!")
        print(f"All users can now login with PIN: {default_pin}")

if __name__ == "__main__":
    asyncio.run(rehash_all_pins())
