import time
import requests
import jwt
from datetime import timedelta
import sys
from pathlib import Path

BASE_BACKEND = "http://127.0.0.1:8000"
BASE_FRONTEND = "http://localhost:5173"

# Import backend settings for secret inspection
backend_dir = Path(__file__).resolve().parents[2]
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))
from app.config import settings
from app.services.security import create_access_token

print("=" * 65)
print("TESTING MODULE 1 - TASK 3: JWT-BASED AUTHENTICATION (LIVE)")
print("=" * 65)

test_results = []

def record(test_num, title, passed, detail=""):
    status_str = "PASS" if passed else "FAIL"
    test_results.append((test_num, title, status_str, detail))
    print(f"[{status_str}] Test {test_num}: {title} -> {detail}")

session = requests.Session()

# 1. Existing Registration Functionality
reg_email = f"jwt_analyst_{int(time.time())}@infosys.com"
reg_payload = {
    "fullName": "JWT Verification Analyst",
    "email": reg_email,
    "password": "SecurePassword2026!",
    "confirmPassword": "SecurePassword2026!",
}
r_reg = requests.post(f"{BASE_BACKEND}/api/auth/register", json=reg_payload)
record(1, "Existing Registration Flow", r_reg.status_code == 201, f"HTTP {r_reg.status_code}")
user_id = r_reg.json().get("data", {}).get("user_id")

# 2. Login & JWT Generation (HttpOnly Cookie)
login_payload = {
    "email": reg_email,
    "password": "SecurePassword2026!",
}
r_login = session.post(f"{BASE_BACKEND}/api/auth/login", json=login_payload)
cookie_present = settings.AUTH_COOKIE_NAME in session.cookies
token = session.cookies.get(settings.AUTH_COOKIE_NAME)
record(2, "Login Generates JWT in HttpOnly Cookie", r_login.status_code == 200 and cookie_present, f"HTTP {r_login.status_code}, Cookie '{settings.AUTH_COOKIE_NAME}' present: {cookie_present}")

# 3. JWT Claims Verification (sub & exp)
try:
    decoded = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    has_sub = decoded.get("sub") == str(user_id)
    has_exp = "exp" in decoded and decoded["exp"] > time.time()
    record(3, "JWT Claims Verification (sub & exp)", has_sub and has_exp, f"sub matches user_id ({has_sub}), exp valid ({has_exp})")
except Exception as e:
    record(3, "JWT Claims Verification (sub & exp)", False, str(e))

# 4. Valid JWT Permits Access to Protected Research Endpoints
r_search = session.get(f"{BASE_BACKEND}/api/stocks/search?q=INFY")
r_overview = session.get(f"{BASE_BACKEND}/api/stocks/INFY.NS/overview")
r_history = session.get(f"{BASE_BACKEND}/api/stocks/INFY.NS/history?period=1mo")
all_research_ok = r_search.status_code == 200 and r_overview.status_code == 200 and r_history.status_code == 200
record(4, "Valid JWT Grants Access to /api/stocks/*", all_research_ok, f"Search HTTP {r_search.status_code}, Overview HTTP {r_overview.status_code}, History HTTP {r_history.status_code}")

# 5. Missing Token Rejection (HTTP 401)
unauth_res = requests.get(f"{BASE_BACKEND}/api/stocks/INFY.NS/overview")
record(5, "Missing Token Rejected", unauth_res.status_code == 401, f"HTTP {unauth_res.status_code}, Detail: {unauth_res.json().get('detail')}")

# 6. Invalid Token Rejection (HTTP 401)
bad_session = requests.Session()
bad_session.cookies.set(settings.AUTH_COOKIE_NAME, "completely.forged.and.invalid.jwt.token")
invalid_res = bad_session.get(f"{BASE_BACKEND}/api/stocks/INFY.NS/overview")
record(6, "Invalid Token Rejected", invalid_res.status_code == 401, f"HTTP {invalid_res.status_code}, Detail: {invalid_res.json().get('detail')}")

# 7. Expired Token Rejection (HTTP 401)
expired_token = create_access_token(
    user_id=user_id,
    email=reg_email,
    expires_delta=timedelta(minutes=-30)  # Expired 30 mins ago
)
expired_session = requests.Session()
expired_session.cookies.set(settings.AUTH_COOKIE_NAME, expired_token)
exp_res = expired_session.get(f"{BASE_BACKEND}/api/stocks/INFY.NS/overview")
record(7, "Expired Token Rejected", exp_res.status_code == 401, f"HTTP {exp_res.status_code}, Detail: {exp_res.json().get('detail')}")

# 8. Nonexistent User ID in Token Rejection (HTTP 401)
ghost_token = create_access_token(
    user_id=999999,
    email="ghost@example.com",
)
ghost_session = requests.Session()
ghost_session.cookies.set(settings.AUTH_COOKIE_NAME, ghost_token)
ghost_res = ghost_session.get(f"{BASE_BACKEND}/api/stocks/INFY.NS/overview")
record(8, "Nonexistent User ID Rejected", ghost_res.status_code == 401, f"HTTP {ghost_res.status_code}, Detail: {ghost_res.json().get('detail')}")

# 9. Protected Profile /api/auth/me Endpoint
me_res = session.get(f"{BASE_BACKEND}/api/auth/me")
me_ok = me_res.status_code == 200 and me_res.json().get("data", {}).get("email") == reg_email
record(9, "Protected /api/auth/me Profile Check", me_ok, f"HTTP {me_res.status_code}, User: {me_res.json().get('data', {}).get('full_name')}")

# 10. Logout Clears Authentication Cookie
r_logout = session.post(f"{BASE_BACKEND}/api/auth/logout")
post_logout_check = session.get(f"{BASE_BACKEND}/api/auth/me")
logout_ok = r_logout.status_code == 200 and post_logout_check.status_code == 401
record(10, "Logout Clears Cookie & Blocks Access", logout_ok, f"Logout HTTP {r_logout.status_code}, Post-logout check HTTP {post_logout_check.status_code}")

# 11. Frontend Server Accessibility
r_front = requests.get(BASE_FRONTEND)
record(11, "Frontend Server Accessible", r_front.status_code == 200, f"HTTP {r_front.status_code}")

print("=" * 65)
passed_count = sum(1 for _, _, status, _ in test_results if status == "PASS")
print(f"VERIFICATION RESULTS: {passed_count}/{len(test_results)} TESTS PASSED")
print("=" * 65)

if passed_count == len(test_results):
    sys.exit(0)
else:
    sys.exit(1)

