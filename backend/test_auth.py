
from auth import (
    hash_password,
    verify_password,
    create_access_token,
    verify_access_token
)


# TEST 1: Password hashing
print("TEST 1: Password hashing")

password = "StrongPassword123"

hashed_password = hash_password(password)

assert hashed_password != password

print("Password hashed successfully!")


# TEST 2: Password verification
print("\nTEST 2: Password verification")

correct = verify_password(password, hashed_password)
incorrect = verify_password("WrongPassword123", hashed_password)

assert correct is True
assert incorrect is False

print("Correct password verified!")
print("Incorrect password rejected!")


# TEST 3: JWT creation
print("\nTEST 3: JWT token creation")

token = create_access_token({
    "sub": "test-user-1"
})

assert isinstance(token, str)

print("JWT token generated successfully!")


# TEST 4: JWT verification
print("\nTEST 4: JWT token verification")

payload = verify_access_token(token)

assert payload["sub"] == "test-user-1"

print("JWT token verified successfully!")
print("User ID:", payload["sub"])


print("\nAll authentication tests passed!")


import jwt

from datetime import datetime, timedelta, timezone
from config import JWT_SECRET_KEY, JWT_ALGORITHM


# Create an already expired token
expired_token = jwt.encode(
    {
        "sub": "test-user-1",
        "exp": datetime.now(timezone.utc) - timedelta(minutes=1)
    },
    JWT_SECRET_KEY,
    algorithm=JWT_ALGORITHM
)

print("\nTEST 5: Expired JWT token")

try:
    verify_access_token(expired_token)
    print("ERROR: Expired token was accepted!")

except jwt.ExpiredSignatureError:
    print("Expired token rejected successfully!")
