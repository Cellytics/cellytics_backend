"""
Migration script to add validation and finance confirmation columns to cell_reports table.
Run this script with: python migrate_add_validation_columns.py
"""

import asyncio
from sqlalchemy import text
from database import get_async_engine

async def migrate():
    engine = get_async_engine()
    
    migration_sql = """
    ALTER TABLE cell_reports
    ADD COLUMN IF NOT EXISTS is_validated BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS validated_by_id UUID REFERENCES users(id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS validated_at TIMESTAMP WITH TIME ZONE,
    ADD COLUMN IF NOT EXISTS finance_confirmed BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS finance_confirmed_by_id UUID REFERENCES users(id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS finance_confirmed_at TIMESTAMP WITH TIME ZONE;
    """
    
    async with engine.begin() as conn:
        await conn.execute(text(migration_sql))
        print("✓ Migration completed successfully!")
        print("✓ Added: is_validated, validated_by_id, validated_at")
        print("✓ Added: finance_confirmed, finance_confirmed_by_id, finance_confirmed_at")

if __name__ == "__main__":
    asyncio.run(migrate())
