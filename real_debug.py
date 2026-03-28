"""
REAL DEBUG SCRIPT - Run this in your venv to see what's actually broken

python real_debug.py
"""

import bcrypt
import sys

print("=" * 70)
print("REAL DEBUGGING - Figure out what's actually wrong")
print("=" * 70)

# Test 1: Can bcrypt work?
print("\n[TEST 1] Can bcrypt hash and verify?")
print("-" * 70)

try:
    test_pin = "123456"
    new_hash = bcrypt.hashpw(test_pin.encode('utf-8'), bcrypt.gensalt(rounds=12))
    print(f"✅ Hash created: {new_hash.decode()[:40]}...")
    
    is_valid = bcrypt.checkpw(test_pin.encode('utf-8'), new_hash)
    print(f"✅ Verify works: {is_valid}")
except Exception as e:
    print(f"❌ ERROR: {e}")
    sys.exit(1)

# Test 2: Test with ACTUAL database hashes
print("\n[TEST 2] Test hashes that are supposedly in your database")
print("-" * 70)

database_hashes = {
    'kMX6ef7dVxNx hash': '$2b$12$kMX6ef7dVxNx/VjKaAtB6.oY.ffbccrvFg8nnO52UO2frrSgwxI2W',
    'LQv3c1yq hash': '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5YmMxSUriS3H2',
}

pin = "123456"
all_failed = True

for name, hash_val in database_hashes.items():
    try:
        result = bcrypt.checkpw(pin.encode('utf-8'), hash_val.encode('utf-8'))
        status = "✅ WORKS" if result else "❌ WRONG PIN"
        print(f"{name}: {status}")
        if result:
            all_failed = False
    except Exception as e:
        print(f"{name}: ❌ ERROR: {e}")

# Test 3: Generate a working hash
print("\n[TEST 3] Generate a fresh hash that will 100% work")
print("-" * 70)

fresh_hash = bcrypt.hashpw(b"123456", bcrypt.gensalt(12)).decode()
print(f"Fresh hash: {fresh_hash}")

is_valid = bcrypt.checkpw(b"123456", fresh_hash.encode('utf-8'))
print(f"Verify fresh: {is_valid}")

# Test 4: Show what to do
print("\n" + "=" * 70)
print("[TEST 4] SOLUTION")
print("=" * 70)

if all_failed:
    print("\n⚠️  YOUR DATABASE HASHES ARE BAD OR CORRUPT")
    print("\n👉 UPDATE YOUR DATABASE WITH THIS HASH:")
    print(f"\nUPDATE users SET pin_hash = '{fresh_hash}' WHERE is_active = true;\n")
    print("Then restart FastAPI and try login again.")
else:
    print("\n✅ Your database hash should work!")
    print("\nThe problem is in YOUR CODE, not the hash.")
    print("Check that verify_pin() is being called correctly.")

# Test 5: Show current auth.py
print("\n" + "=" * 70)
print("[TEST 5] Check your verify_pin function")
print("=" * 70)

try:
    from auth import verify_pin
    test_result = verify_pin("123456", fresh_hash)
    print(f"verify_pin('123456', fresh_hash) = {test_result}")
    
    if not test_result:
        print("\n❌ verify_pin() is returning False even with a fresh hash!")
        print("This means your verify_pin() function is broken.")
except Exception as e:
    print(f"❌ Can't import verify_pin: {e}")

print("\n" + "=" * 70)
print("END DEBUG")
print("=" * 70)
