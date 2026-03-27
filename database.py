# database.py - Database Connection and Session Management

import os
import ssl
import re
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from dotenv import load_dotenv

load_dotenv()

# Get database URL
DATABASE_URL = os.getenv("DATABASE_URL", "")

# Normalize: ensure we always use postgresql+asyncpg://
if DATABASE_URL.startswith("postgresql://"):
    ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
elif DATABASE_URL.startswith("postgresql+asyncpg://"):
    ASYNC_DATABASE_URL = DATABASE_URL
else:
    ASYNC_DATABASE_URL = DATABASE_URL

# Strip query params that asyncpg doesn't understand
ASYNC_DATABASE_URL = re.sub(r'[&?]sslmode=[^&]*', '', ASYNC_DATABASE_URL)
ASYNC_DATABASE_URL = re.sub(r'[&?]channel_binding=[^&]*', '', ASYNC_DATABASE_URL)
ASYNC_DATABASE_URL = ASYNC_DATABASE_URL.rstrip('?&')

# SSL context for Neon.tech (required)
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

# Create async engine
engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=False,  # Set to True to see SQL queries
    future=True,
    poolclass=NullPool,  # Use NullPool for serverless/free tier compatibility
    connect_args={"ssl": ssl_context},
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for FastAPI to get database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Initialize database (if needed for testing)"""
    async with engine.begin() as conn:
        # Tables already created via schema.sql, so nothing needed here
        pass


async def close_db():
    """Close database connection"""
    await engine.dispose()

















# # database.py - Database Connection and Session Management

# import os
# from typing import AsyncGenerator
# from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
# from sqlalchemy.pool import NullPool
# from dotenv import load_dotenv

# load_dotenv()

# # Get database URL (convert postgresql:// to postgresql+asyncpg://)
# DATABASE_URL = os.getenv("DATABASE_URL")
# if DATABASE_URL and DATABASE_URL.startswith("postgresql://"):
#     ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
# else:
#     ASYNC_DATABASE_URL = DATABASE_URL

# # Create async engine
# engine = create_async_engine(
#     ASYNC_DATABASE_URL,
#     echo=False,  # Set to True to see SQL queries
#     future=True,
#     pool_pre_ping=True,
#     poolclass=NullPool,  # Use NullPool for serverless/free tier compatibility
# )

# # Create async session factory
# AsyncSessionLocal = async_sessionmaker(
#     engine,
#     class_=AsyncSession,
#     expire_on_commit=False,
#     autocommit=False,
#     autoflush=False,
# )


# async def get_session() -> AsyncGenerator[AsyncSession, None]:
#     """Dependency for FastAPI to get database session"""
#     async with AsyncSessionLocal() as session:
#         try:
#             yield session
#         finally:
#             await session.close()


# async def init_db():
#     """Initialize database (if needed for testing)"""
#     async with engine.begin() as conn:
#         # Tables already created via schema.sql, so nothing needed here
#         pass


# async def close_db():
#     """Close database connection"""
#     await engine.dispose()