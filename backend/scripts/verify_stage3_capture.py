import sys
import time
from pathlib import Path

import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi.testclient import TestClient

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.config import settings
from app.main import app
from app.security import hash_password


PASSWORD = "Stage3!Test123"


def connect():
    return psycopg2.connect(
        host=settings.DATABASE_HOST,
        port=settings.DATABASE_PORT,
        dbname=settings.DATABASE_NAME,
        user=settings.DATABASE_USER,
        password=settings.DATABASE_PASSWORD,
        cursor_factory=RealDictCursor,
    )


def login(client, username, role):
    response = client.post(
        "/api/v1/auth/login",
        json={"identifier": username, "password": PASSWORD, "role": role},
    )
    if response.status_code != 200:
        raise AssertionError(
            f"Login failed for {username}: {response.status_code} {response.text}"
        )
    return response.json()["access_token"]


def main():
    connection = connect()
    test_ids = {}
    session_ids = []

    try:
        with connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT count(*) AS count FROM public.network_packets "
                    "WHERE capture_source = 'historical_import'"
                )
                historical_before = cursor.fetchone()["count"]
                cursor.execute(
                    "SELECT count(*) AS count FROM public.network_packets "
                    "WHERE capture_source = 'live_capture'"
                )
                live_before = cursor.fetchone()["count"]

                cursor.execute(
                    "DELETE FROM audit_logs WHERE actor_user_id IN "
                    "(SELECT id FROM users WHERE username LIKE '__stage3_capture_%')"
                )
                cursor.execute(
                    "DELETE FROM users WHERE username LIKE '__stage3_capture_%'"
                )

                password_hash = hash_password(PASSWORD)
                cursor.execute(
                    """
                    INSERT INTO users
                        (username, email, full_name, password_hash, status)
                    VALUES
                        ('__stage3_capture_lead__', '__stage3_capture_lead@example.invalid', 'Stage 3 Lead', %s, 'active'),
                        ('__stage3_capture_analyst__', '__stage3_capture_analyst@example.invalid', 'Stage 3 Analyst', %s, 'active')
                    RETURNING username, id
                    """,
                    (password_hash, password_hash),
                )
                test_ids.update({row["username"]: row["id"] for row in cursor.fetchall()})

                cursor.execute(
                    "SELECT id, role_name FROM roles "
                    "WHERE role_name IN ('team_lead','security_analyst')"
                )
                roles = {row["role_name"]: row["id"] for row in cursor.fetchall()}
                cursor.executemany(
                    "INSERT INTO user_roles (user_id, role_id) VALUES (%s, %s)",
                    (
                        (test_ids["__stage3_capture_lead__"], roles["team_lead"]),
                        (
                            test_ids["__stage3_capture_analyst__"],
                            roles["security_analyst"],
                        ),
                    ),
                )

        with TestClient(app) as client:
            unauthorized = client.get("/api/v1/network/interfaces")
            if unauthorized.status_code != 401:
                raise AssertionError(
                    f"Unauthorized interface discovery returned "
                    f"{unauthorized.status_code}"
                )
            print("PASS capture_interface_discovery unauthorized=401")

            lead_token = login(
                client, "__stage3_capture_lead__", "team_lead"
            )
            analyst_token = login(
                client, "__stage3_capture_analyst__", "security_analyst"
            )

            denied_start = client.post(
                "/api/v1/network/capture/start",
                params={"interface_id": "invalid"},
                headers={"Authorization": f"Bearer {lead_token}"},
            )
            if denied_start.status_code != 403:
                raise AssertionError(
                    f"Team Lead capture start returned "
                    f"{denied_start.status_code}, expected 403"
                )
            print("PASS capture_start team_lead=403")

            interfaces_response = client.get(
                "/api/v1/network/interfaces",
                headers={"Authorization": f"Bearer {analyst_token}"},
            )
            if interfaces_response.status_code != 200:
                raise AssertionError(
                    f"Interface discovery returned {interfaces_response.status_code}"
                )
            interfaces = interfaces_response.json()["interfaces"]
            wifi = next(
                (
                    item
                    for item in interfaces
                    if "Intel" in item["name"]
                    and "Wi-Fi" in item["name"]
                ),
                None,
            )
            if wifi is None:
                raise AssertionError("No Wi-Fi interface was discovered")
            print(
                f"PASS capture_interface_discovery interface="
                f"{wifi['name']} id={wifi['id']}"
            )

            invalid = client.post(
                "/api/v1/network/capture/start",
                params={"interface_id": "{invalid-interface}"},
                headers={"Authorization": f"Bearer {analyst_token}"},
            )
            if invalid.status_code != 400:
                raise AssertionError(
                    f"Invalid interface returned {invalid.status_code}, expected 400"
                )
            print("PASS capture_start invalid_interface=400")

            started = client.post(
                "/api/v1/network/capture/start",
                params={"interface_id": wifi["id"]},
                headers={"Authorization": f"Bearer {analyst_token}"},
            )
            if started.status_code != 200:
                raise AssertionError(
                    f"Capture start returned {started.status_code}: {started.text}"
                )
            started_data = started.json()
            session_id = started_data["id"]
            session_ids.append(session_id)
            print(
                f"PASS capture_start status=running "
                f"session={session_id[:8]} interface={wifi['name']}"
            )

            conflicting = client.post(
                "/api/v1/network/capture/start",
                params={"interface_id": wifi["id"]},
                headers={"Authorization": f"Bearer {analyst_token}"},
            )
            if conflicting.status_code != 409:
                raise AssertionError(
                    f"Conflicting capture returned "
                    f"{conflicting.status_code}, expected 409"
                )
            print("PASS capture_start conflict=409")

            time.sleep(10)

            status_response = client.get(
                "/api/v1/network/capture/status",
                headers={"Authorization": f"Bearer {analyst_token}"},
            )
            if status_response.status_code != 200:
                raise AssertionError(
                    f"Capture status returned {status_response.status_code}"
                )
            status_data = status_response.json()
            if not status_data["active"]:
                raise AssertionError("Capture was not active after start")

            stopped = client.post(
                "/api/v1/network/capture/stop",
                params={"session_id": session_id},
                headers={"Authorization": f"Bearer {analyst_token}"},
            )
            if stopped.status_code != 200:
                raise AssertionError(
                    f"Capture stop returned {stopped.status_code}: {stopped.text}"
                )
            stopped_data = stopped.json()
            if stopped_data["active"]:
                raise AssertionError("Capture remained active after stop")
            print(
                f"PASS capture_stop active=false "
                f"received={status_data['session']['packets_received']}"
            )

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT count(*) AS count FROM public.network_packets "
                "WHERE capture_source = 'historical_import'"
            )
            historical_after = cursor.fetchone()["count"]
            cursor.execute(
                "SELECT count(*) AS count FROM public.network_packets "
                "WHERE capture_source = 'live_capture'"
            )
            live_after = cursor.fetchone()["count"]
            cursor.execute(
                "SELECT status, packets_received, packets_inserted, "
                "packets_dropped, error_message "
                "FROM network_capture_sessions WHERE id = %s",
                (session_id,),
            )
            session_row = cursor.fetchone()

        if historical_after != historical_before:
            raise AssertionError(
                "Historical packet record count changed during live capture"
            )
        print(
            f"PASS historical_records_unchanged count={historical_after}"
        )
        print(
            f"PASS live_capture_records live_before={live_before} "
            f"live_after={live_after}"
        )
        if session_row is None:
            raise AssertionError("Capture session row was not stored")
        print(
            f"PASS capture_session_db status={session_row['status']} "
            f"received={session_row['packets_received']} "
            f"inserted={session_row['packets_inserted']} "
            f"dropped={session_row['packets_dropped']}"
        )

        if live_after <= live_before:
            print("INFO no live packet metadata was recorded in the passive 10-second test window")
        else:
            print("PASS live_packet_metadata_stored")
    finally:
        with connection:
            with connection.cursor() as cursor:
                if session_ids:
                    cursor.execute(
                        "DELETE FROM public.network_packets "
                        "WHERE capture_source = 'live_capture' "
                        "AND capture_id = ANY(%s)",
                        (session_ids,),
                    )
                    cursor.execute(
                        "DELETE FROM network_capture_sessions WHERE id = ANY(%s)",
                        (session_ids,),
                    )
                cursor.execute(
                    "DELETE FROM audit_logs WHERE actor_user_id = ANY(%s)",
                    (list(test_ids.values()),),
                )
                cursor.execute(
                    "DELETE FROM users WHERE username LIKE '__stage3_capture_%'"
                )
        connection.close()
        print("PASS temporary Stage 3 test data cleaned up")


if __name__ == "__main__":
    main()
