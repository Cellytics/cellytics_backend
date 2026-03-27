# auth.py - Authentication Service

import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from uuid import UUID
import jwt
from passlib.context import CryptContext
from dotenv import load_dotenv

load_dotenv()

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

# Security
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-super-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 30

# Password context for bcrypt
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,
)


# ═══════════════════════════════════════════════════════════════════════════════
# PIN HASHING
# ═══════════════════════════════════════════════════════════════════════════════

def hash_pin(pin: str) -> str:
    """Hash a PIN using bcrypt"""
    return pwd_context.hash(pin)


def verify_pin(pin: str, pin_hash: str) -> bool:
    """Verify a PIN against its hash"""
    try:
        return pwd_context.verify(pin, pin_hash)
    except:
        return False


# ═══════════════════════════════════════════════════════════════════════════════
# JWT TOKEN MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════════

def create_access_token(
    subject: str,  # Usually user_id
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create JWT access token"""
    if expires_delta is None:
        expires_delta = timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)

    expire = datetime.utcnow() + expires_delta
    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "iat": datetime.utcnow(),
    }

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify JWT token and return payload"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def decode_token(token: str) -> Optional[str]:
    """Decode token and return user_id (subject)"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        return user_id
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# DEFAULT PIN FOR NEW USERS
# ═══════════════════════════════════════════════════════════════════════════════

def get_default_pin() -> str:
    """Get default PIN for new users"""
    return "123456"


def hash_default_pin() -> str:
    """Get hashed default PIN"""
    return hash_pin(get_default_pin())