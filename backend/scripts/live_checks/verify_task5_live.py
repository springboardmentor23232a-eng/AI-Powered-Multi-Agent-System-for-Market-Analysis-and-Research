import sys
import time
import requests
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"

def test_live_task5():
    print("=== LIVE VERIFICATION: MODULE 1 - TASK 5 (SAVED STOCKS & WATCHLISTS) ===")

    # 1. Register & Login User 1
    session_1 = requests.Session()
    email_1 = f"wl_live_user1_{int(time.time())}@example.com"
    res_reg1 = session_1.post(f"{BASE_URL}/api/auth/register", json={
        "fullName": "Watchlist User One",
        "email": email_1,
        "password": "Password123!",
        "confirmPassword": "Password123!",
    })
    assert res_reg1.status_code == 201
    res_log1 = session_1.post(f"{BASE_URL}/api/auth/login", json={"email": email_1, "password": "Password123!"})
    assert res_log1.status_code == 200
    user_1 = res_log1.json()["data"]
    print(f"[PASS] 1. Registered and logged in User 1: {user_1['email']}")

    # 2. Search stock by company name
    res_search = session_1.get(f"{BASE_URL}/api/stocks/search?q=Infosys")
    assert res_search.status_code == 200
    search_data = res_search.json()
    assert search_data["count"] > 0
    assert any(s["ticker"] == "INFY.NS" for s in search_data["results"])
    print(f"[PASS] 2. Search 'Infosys' returned {search_data['count']} matches including INFY.NS")

    # 3. Add to Watchlist
    res_add1 = session_1.post(f"{BASE_URL}/api/watchlist", json={"ticker": "INFY.NS"})
    assert res_add1.status_code == 201
    item_1 = res_add1.json()
    assert item_1["ticker"] == "INFY.NS"
    assert item_1["user_id"] == user_1["user_id"]
    saved_stock_id_1 = item_1["saved_stock_id"]
    print(f"[PASS] 3. Added INFY.NS to watchlist (SavedStock ID #{saved_stock_id_1})")

    # 4. Attempt duplicate addition -> 409 Conflict
    res_dup = session_1.post(f"{BASE_URL}/api/watchlist", json={"ticker": "INFY.NS"})
    assert res_dup.status_code == 409
    assert "already in your watchlist" in res_dup.json()["detail"]
    print("[PASS] 4. Duplicate ticker rejected with HTTP 409 Conflict")

    # 5. Retrieve watchlist for User 1
    res_get1 = session_1.get(f"{BASE_URL}/api/watchlist")
    assert res_get1.status_code == 200
    wl_1 = res_get1.json()
    assert wl_1["count"] == 1
    assert wl_1["data"][0]["ticker"] == "INFY.NS"
    assert wl_1["data"][0]["company_name"] == "Infosys Limited"
    print(f"[PASS] 5. User 1 retrieved watchlist with 1 stock: {wl_1['data'][0]['company_name']}")

    # 6. User 2 Registration and strict isolation
    session_2 = requests.Session()
    email_2 = f"wl_live_user2_{int(time.time())}@example.com"
    session_2.post(f"{BASE_URL}/api/auth/register", json={
        "fullName": "Watchlist User Two",
        "email": email_2,
        "password": "Password123!",
        "confirmPassword": "Password123!",
    })
    session_2.post(f"{BASE_URL}/api/auth/login", json={"email": email_2, "password": "Password123!"})

    res_get2 = session_2.get(f"{BASE_URL}/api/watchlist")
    assert res_get2.status_code == 200
    assert res_get2.json()["count"] == 0
    print("[PASS] 6. User 2's watchlist is empty (User 1's stocks are isolated)")

    # 7. User 2 can save the same ticker independently
    res_add2 = session_2.post(f"{BASE_URL}/api/watchlist", json={"ticker": "INFY.NS"})
    assert res_add2.status_code == 201
    saved_stock_id_2 = res_add2.json()["saved_stock_id"]
    assert saved_stock_id_2 != saved_stock_id_1
    print(f"[PASS] 7. User 2 saved INFY.NS independently (SavedStock ID #{saved_stock_id_2})")

    # 8. Cross-user deletion blocked -> 404 Not Found
    res_cross_del = session_2.delete(f"{BASE_URL}/api/watchlist/{saved_stock_id_1}")
    assert res_cross_del.status_code == 404
    print(f"[PASS] 8. User 2 attempting to delete User 1's saved stock rejected with HTTP 404 Not Found")

    # 9. User 1 deletes their own stock
    res_del1 = session_1.delete(f"{BASE_URL}/api/watchlist/{saved_stock_id_1}")
    assert res_del1.status_code == 200
    assert "successfully removed" in res_del1.json()["message"]

    res_get1_after = session_1.get(f"{BASE_URL}/api/watchlist")
    assert res_get1_after.json()["count"] == 0
    print("[PASS] 9. User 1 deleted their stock; watchlist count is now 0")

    # 10. Unauthenticated access rejected -> 401
    res_unauth = requests.get(f"{BASE_URL}/api/watchlist")
    assert res_unauth.status_code == 401
    print("[PASS] 10. Unauthenticated request rejected with HTTP 401 Unauthorized")

    print("\nALL 10 LIVE CHECKS PASSED LIVE ON POSTGRESQL & FASTAPI!")

if __name__ == "__main__":
    test_live_task5()

