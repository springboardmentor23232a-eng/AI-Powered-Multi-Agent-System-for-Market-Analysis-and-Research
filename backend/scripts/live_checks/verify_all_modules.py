import time
import requests
import sys
from pathlib import Path

BASE_BACKEND = "http://127.0.0.1:8000"
BASE_FRONTEND = "http://localhost:5173"

print("=" * 60)
print("RUNNING COMPREHENSIVE END-TO-END TEST ON ALL MODULES")
print("=" * 60)

results = []

def record(test_name: str, passed: bool, detail: str = ""):
    status_str = "PASS" if passed else "FAIL"
    results.append((test_name, status_str, detail))
    print(f"[{status_str}] {test_name}: {detail}")

# 1. Health & Root Endpoints
try:
    r = requests.get(f"{BASE_BACKEND}/api/health", timeout=5)
    record("Health Check (/api/health)", r.status_code == 200 and r.json().get("status") == "ok", f"HTTP {r.status_code}")
except Exception as e:
    record("Health Check (/api/health)", False, str(e))

try:
    r = requests.get(f"{BASE_BACKEND}/", timeout=5)
    record("Root Welcome Endpoint (/)", r.status_code == 200 and "docs_url" in r.json(), f"HTTP {r.status_code}")
except Exception as e:
    record("Root Welcome Endpoint (/)", False, str(e))

try:
    r = requests.get(f"{BASE_BACKEND}/docs", timeout=5)
    record("Swagger UI Documentation (/docs)", r.status_code == 200 and "swagger-ui" in r.text.lower(), f"HTTP {r.status_code}")
except Exception as e:
    record("Swagger UI Documentation (/docs)", False, str(e))

# 2. Frontend Server Accessibility
try:
    r = requests.get(BASE_FRONTEND, timeout=5)
    record("Frontend Dev Server (http://localhost:5173)", r.status_code == 200, f"HTTP {r.status_code}")
except Exception as e:
    record("Frontend Dev Server (http://localhost:5173)", False, str(e))

# 3. User Registration Flow (Module 1 Scope)
test_email = f"analyst_{int(time.time())}@infosys.com"
valid_reg_payload = {
    "fullName": "Market Analyst Lead",
    "email": test_email,
    "password": "SecurePassword123!",
    "confirmPassword": "SecurePassword123!",
}

try:
    r = requests.post(f"{BASE_BACKEND}/api/auth/register", json=valid_reg_payload, timeout=5)
    data = r.json()
    user_id = data.get("data", {}).get("user_id")
    passed = r.status_code == 201 and data.get("status") == "success" and "password_hash" not in str(data)
    record("User Registration (Valid Payload)", passed, f"HTTP {r.status_code}, Generated User ID: {user_id}")
except Exception as e:
    record("User Registration (Valid Payload)", False, str(e))

# Duplicate Email Conflict Prevention
try:
    r = requests.post(f"{BASE_BACKEND}/api/auth/register", json=valid_reg_payload, timeout=5)
    passed = r.status_code == 409
    record("Registration Duplicate Email Conflict", passed, f"HTTP {r.status_code}, Conflict handled: {passed}")
except Exception as e:
    record("Registration Duplicate Email Conflict", False, str(e))

# Password Mismatch Validation
mismatch_payload = valid_reg_payload.copy()
mismatch_payload["email"] = f"mismatch_{int(time.time())}@infosys.com"
mismatch_payload["confirmPassword"] = "WrongMismatch999!"
try:
    r = requests.post(f"{BASE_BACKEND}/api/auth/register", json=mismatch_payload, timeout=5)
    passed = r.status_code == 422
    record("Registration Password Mismatch Rejection", passed, f"HTTP {r.status_code}, Detail: {r.json().get('detail')}")
except Exception as e:
    record("Registration Password Mismatch Rejection", False, str(e))

# Weak Password Validation (Missing Uppercase/Digit)
weak_payload = valid_reg_payload.copy()
weak_payload["email"] = f"weak_{int(time.time())}@infosys.com"
weak_payload["password"] = "alllowercase"
weak_payload["confirmPassword"] = "alllowercase"
try:
    r = requests.post(f"{BASE_BACKEND}/api/auth/register", json=weak_payload, timeout=5)
    passed = r.status_code == 422
    record("Registration Weak Password Rejection", passed, f"HTTP {r.status_code}, Detail: {r.json().get('detail')}")
except Exception as e:
    record("Registration Weak Password Rejection", False, str(e))

# 4. User Authentication Flow (Login)
try:
    login_payload = {"email": test_email, "password": "SecurePassword123!"}
    r = requests.post(f"{BASE_BACKEND}/api/auth/login", json=login_payload, timeout=5)
    passed = r.status_code == 200 and r.json().get("status") == "success"
    record("User Login (Valid Credentials)", passed, f"HTTP {r.status_code}, Status: {r.json().get('status')}")
except Exception as e:
    record("User Login (Valid Credentials)", False, str(e))

try:
    invalid_login = {"email": test_email, "password": "WrongPassword999!"}
    r = requests.post(f"{BASE_BACKEND}/api/auth/login", json=invalid_login, timeout=5)
    passed = r.status_code == 401
    record("User Login (Invalid Password Rejection)", passed, f"HTTP {r.status_code}")
except Exception as e:
    record("User Login (Invalid Password Rejection)", False, str(e))

# 5. Stock Research & Analysis Endpoints
try:
    r = requests.get(f"{BASE_BACKEND}/api/stocks/search?q=INFY", timeout=5)
    passed = r.status_code == 200 and len(r.json()) > 0
    record("Stock Symbol Search (/api/stocks/search)", passed, f"HTTP {r.status_code}, Results: {len(r.json())}")
except Exception as e:
    record("Stock Symbol Search (/api/stocks/search)", False, str(e))

try:
    r = requests.get(f"{BASE_BACKEND}/api/stocks/INFY.NS/overview", timeout=10)
    passed = r.status_code == 200 and "current_price" in r.json()
    price = r.json().get("current_price")
    curr = r.json().get("currency", "INR")
    record("Stock Overview (/api/stocks/{symbol}/overview)", passed, f"HTTP {r.status_code}, INFY.NS Price: {price} {curr}")
except Exception as e:
    record("Stock Overview (/api/stocks/{symbol}/overview)", False, str(e))

try:
    r = requests.get(f"{BASE_BACKEND}/api/stocks/INFY.NS/history?period=1mo", timeout=10)
    history = r.json().get("history", [])
    passed = r.status_code == 200 and len(history) > 0
    record("Stock Historical Prices (/api/stocks/{symbol}/history)", passed, f"HTTP {r.status_code}, Data points: {len(history)}")
except Exception as e:
    record("Stock Historical Prices (/api/stocks/{symbol}/history)", False, str(e))

# 6. Database Verification (PostgreSQL stock_research_db)
sys.path.insert(0, str(Path("backend").resolve()))
from app.database import SessionLocal
from app.models.user import User

db = SessionLocal()
try:
    persisted_user = db.query(User).filter(User.email == test_email).first()
    has_hash = persisted_user is not None and persisted_user.password_hash.startswith("$2b$")
    no_plaintext = "SecurePassword123!" not in (persisted_user.password_hash if persisted_user else "")
    db_verified = has_hash and no_plaintext
    record("PostgreSQL Persistence & Bcrypt Verification", db_verified, f"Saved in 'stock_research_db', bcrypt hash valid, no plain-text")
except Exception as e:
    record("PostgreSQL Persistence & Bcrypt Verification", False, str(e))
finally:
    db.close()

print("=" * 60)
total_passed = sum(1 for _, status, _ in results if status == "PASS")
print(f"TEST SUMMARY: {total_passed}/{len(results)} MODULE TESTS PASSED")
print("=" * 60)

if total_passed == len(results):
    sys.exit(0)
else:
    sys.exit(1)

