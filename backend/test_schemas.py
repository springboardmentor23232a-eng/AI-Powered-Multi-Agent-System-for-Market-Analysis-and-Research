
from schemas import UserCreate, UserLogin
from pydantic import ValidationError


# Test 1: Valid registration data
print("TEST 1: Valid registration")

try:
    user = UserCreate(
        full_name="Debajit Pramanick",
        email="debajit@example.com",
        password="StrongPassword123",
        confirm_password="StrongPassword123"
    )

    print("Registration data is valid!")

except ValidationError as e:
    print(e)


# Test 2: Password mismatch
print("\nTEST 2: Password mismatch")

try:
    user = UserCreate(
        full_name="Debajit Pramanick",
        email="debajit@example.com",
        password="StrongPassword123",
        confirm_password="DifferentPassword123"
    )

    print("Registration data is valid!")

except ValidationError:
    print("Validation failed: Passwords do not match!")


# Test 3: Invalid email
print("\nTEST 3: Invalid email")

try:
    user = UserLogin(
        email="invalid-email",
        password="StrongPassword123"
    )

    print("Login data is valid!")

except ValidationError:
    print("Validation failed: Invalid email address!")
