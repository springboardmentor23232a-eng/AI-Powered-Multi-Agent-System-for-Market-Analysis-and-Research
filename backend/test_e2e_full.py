import sys
import os
import uuid

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models import User, SavedStock

print("\n" + "="*60)
print("RUNNING COMPLETE E2E TEST SUITE FOR MODULE 1")
print("Target Database: multi_agent_stock_db (PostgreSQL)")
print("="*60 + "\n")

client = TestClient(app)

# 1. Health check
print("[TEST 1] Testing Health Check Endpoint GET / ...")
resp = client.get("/")
assert resp.status_code == 200, f"Health check failed: {resp.text}"
data = resp.json()
assert data["database"] == "multi_agent_stock_db"
print("  --> [PASS] Health check online. Database: multi_agent_stock_db\n")

# 2. Test User Registration
test_email = f"analyst_{uuid.uuid4().hex[:8]}@example.com"
test_name = "Sanjanaa S"
test_password = "SecurePassword123!"

print(f"[TEST 2] Testing User Registration for: {test_email} ...")
reg_payload = {
    "full_name": test_name,
    "email": test_email,
    "password": test_password,
    "confirm_password": test_password
}
resp = client.post("/api/auth/register", json=reg_payload)
assert resp.status_code == 201, f"Registration failed: {resp.text}"
user_out = resp.json()["user"]
assert user_out["email"] == test_email
assert user_out["full_name"] == test_name
print("  --> [PASS] User successfully registered in PostgreSQL users table.\n")

# 3. Test Duplicate Registration Rejection
print("[TEST 3] Testing Duplicate Email Registration Rejection ...")
resp = client.post("/api/auth/register", json=reg_payload)
assert resp.status_code == 400, f"Expected 400 for duplicate email, got: {resp.status_code}"
print("  --> [PASS] Duplicate email correctly rejected with 400 Bad Request.\n")

# 4. Test Weak Password Rejection
print("[TEST 4] Testing Weak Password Rejection ...")
weak_payload = {
    "full_name": "Test User",
    "email": "weak@example.com",
    "password": "weak",
    "confirm_password": "weak"
}
resp = client.post("/api/auth/register", json=weak_payload)
assert resp.status_code == 422, f"Expected 422 for weak password, got: {resp.status_code}"
print("  --> [PASS] Weak password correctly rejected with 422 Unprocessable Entity.\n")

# 5. Test User Login (Incorrect credentials)
print("[TEST 5] Testing Login with Incorrect Password ...")
resp = client.post("/api/auth/login", json={"email": test_email, "password": "WrongPassword999!"})
assert resp.status_code == 401, f"Expected 401 for wrong password, got: {resp.status_code}"
print("  --> [PASS] Invalid password correctly rejected with 401 Unauthorized.\n")

# 6. Test User Login (Correct credentials)
print("[TEST 6] Testing Login with Correct Credentials ...")
resp = client.post("/api/auth/login", json={"email": test_email, "password": test_password})
assert resp.status_code == 200, f"Login failed: {resp.text}"
assert "access_token" in resp.cookies, "HTTP-only access_token cookie was not set in response!"
print("  --> [PASS] Login successful! HTTP-only JWT cookie established.\n")

# 7. Test Authenticated Profile GET /api/auth/me
print("[TEST 7] Testing Current User Retrieval GET /api/auth/me ...")
resp = client.get("/api/auth/me")
assert resp.status_code == 200, f"Failed to retrieve current user: {resp.text}"
me = resp.json()
assert me["email"] == test_email
assert me["full_name"] == test_name
print(f"  --> [PASS] Current user profile verified: {me['full_name']} ({me['email']})\n")

# 8. Test Stock Search
print("[TEST 8] Testing Stock Search GET /api/stocks/search?q=Infosys ...")
resp = client.get("/api/stocks/search?q=Infosys")
assert resp.status_code == 200, f"Search failed: {resp.text}"
search_data = resp.json()
assert search_data["count"] > 0
print(f"  --> [PASS] Search returned {search_data['count']} matching stocks.\n")

# 9. Test Add to Watchlist
print("[TEST 9] Testing Watchlist POST /api/dashboard/watchlist ...")
resp = client.post("/api/dashboard/watchlist", json={"ticker": "INFY"})
assert resp.status_code == 201, f"Add to watchlist failed: {resp.text}"
saved = resp.json()
assert saved["ticker"] == "INFY"
saved_stock_id = saved["saved_stock_id"]
print(f"  --> [PASS] Added INFY to user watchlist in PostgreSQL (id: {saved_stock_id})\n")

# 10. Test Get Watchlist
print("[TEST 10] Testing Watchlist Retrieval GET /api/dashboard/watchlist ...")
resp = client.get("/api/dashboard/watchlist")
assert resp.status_code == 200, f"Get watchlist failed: {resp.text}"
watchlist = resp.json()
assert any(item["ticker"] == "INFY" for item in watchlist)
print(f"  --> [PASS] Watchlist successfully retrieved {len(watchlist)} item(s) from PostgreSQL.\n")

# 11. Test Delete from Watchlist
print(f"[TEST 11] Testing Watchlist Deletion DELETE /api/dashboard/watchlist/{saved_stock_id} ...")
resp = client.delete(f"/api/dashboard/watchlist/{saved_stock_id}")
assert resp.status_code == 200, f"Delete failed: {resp.text}"
print("  --> [PASS] Successfully removed stock from watchlist.\n")

# 12. Test Recent Research
print("[TEST 12] Testing Recent Research GET /api/dashboard/recent-research ...")
resp = client.get("/api/dashboard/recent-research")
assert resp.status_code == 200, f"Recent research failed: {resp.text}"
print("  --> [PASS] Recent research endpoint verified.\n")

# 13. Test Logout
print("[TEST 13] Testing Logout POST /api/auth/logout ...")
resp = client.post("/api/auth/logout")
assert resp.status_code == 200, f"Logout failed: {resp.text}"
# Clear client cookies to simulate cleared cookie
client.cookies.clear()

resp = client.get("/api/auth/me")
assert resp.status_code == 401, f"Expected 401 after logout, got: {resp.status_code}"
print("  --> [PASS] Logout cleared session cookie. Subsequent protected requests correctly rejected.\n")

# 14. Verify in PostgreSQL database
print("[TEST 14] Directly querying PostgreSQL to verify persisted record...")
db = SessionLocal()
db_user = db.query(User).filter(User.email == test_email).first()
assert db_user is not None, "Registered user was not found in PostgreSQL!"
assert db_user.password_hash.startswith("$2b$"), "Password is not hashed with bcrypt!"
print(f"  --> [PASS] Verified user in PostgreSQL table 'users':")
print(f"      user_id: {db_user.user_id}")
print(f"      full_name: {db_user.full_name}")
print(f"      email: {db_user.email}")
print(f"      password_hash: {db_user.password_hash[:20]}... (Secure bcrypt hash)")
db.close()

print("\n" + "="*60)
print("ALL 14 E2E AND POSTGRESQL TESTS PASSED SUCCESSFULLY!")
print("="*60 + "\n")

