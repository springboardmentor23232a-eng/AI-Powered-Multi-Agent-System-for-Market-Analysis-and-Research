import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

import psycopg2
from psycopg2.extras import RealDictCursor, execute_values
from fastapi.testclient import TestClient

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.config import settings
from app.main import app
from app.security import hash_password


PASSWORD = "Stage4!Test123"
BOUNDARY_CAPTURE = "__stage4_boundary_499"
TRIGGER_CAPTURE = "__stage4_trigger_501"
HISTORICAL_CAPTURE = "__stage4_historical_501"


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


def expect(client, method, path, token, expected_status, params=None):
    response = client.request(
        method,
        path,
        params=params,
        headers={"Authorization": f"Bearer {token}"} if token else None,
    )
    if response.status_code != expected_status:
        raise AssertionError(
            f"{method} {path}: got {response.status_code}, "
            f"expected {expected_status}: {response.text}"
        )
    return response


def insert_test_packets(connection, capture_id, count, port_spread, capture_source="live_capture"):
    with connection:
        with connection.cursor() as cursor:
            rows = []
            for index in range(count):
                port = 8000 + (index % port_spread)
                import_key = f"{capture_id}-{index}-{uuid.uuid4()}"
                rows.append((
                    datetime.now(timezone.utc).replace(tzinfo=None),
                    "192.0.2.44",
                    "198.51.100.20",
                    443,
                    port,
                    "TCP",
                    64,
                    capture_id,
                    index + 1,
                    True,
                    "confirmed",
                    "unknown",
                    capture_source,
                    import_key,
                ))
            execute_values(
                cursor,
                """
                INSERT INTO public.network_packets (
                    packet_timestamp, source_ip, destination_ip,
                    source_port, destination_port, protocol, packet_size,
                    capture_id, frame_number, protocol_confirmed,
                    protocol_confidence, traffic_direction,
                    capture_source, import_key
                ) VALUES %s
                """,
                rows,
                page_size=500,
            )


def main():
    connection = connect()
    test_ids = []

    try:
        insert_test_packets(connection, BOUNDARY_CAPTURE, 499, 1)
        insert_test_packets(connection, TRIGGER_CAPTURE, 501, 25)
        insert_test_packets(
            connection,
            HISTORICAL_CAPTURE,
            501,
            25,
            capture_source="historical_import",
        )

        with connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM network_alerts WHERE capture_id LIKE '__stage4_%'"
                )
                cursor.execute(
                    "DELETE FROM audit_logs WHERE actor_user_id IN "
                    "(SELECT id FROM users WHERE username LIKE '__stage4_%')"
                )
                cursor.execute(
                    "DELETE FROM users WHERE username LIKE '__stage4_%'"
                )
                password_hash = hash_password(PASSWORD)
                cursor.execute(
                    """
                    INSERT INTO users
                        (username, email, full_name, password_hash, status)
                    VALUES
                        ('__stage4_admin__', '__stage4_admin@example.invalid', 'Stage 4 Admin', %s, 'active'),
                        ('__stage4_lead__', '__stage4_lead@example.invalid', 'Stage 4 Lead', %s, 'active'),
                        ('__stage4_analyst__', '__stage4_analyst@example.invalid', 'Stage 4 Analyst', %s, 'active')
                    RETURNING username, id
                    """,
                    (password_hash, password_hash, password_hash),
                )
                test_users = {row["username"]: row["id"] for row in cursor.fetchall()}
                test_ids = list(test_users.values())
                cursor.execute(
                    "SELECT id, role_name FROM roles "
                    "WHERE role_name IN ('administrator','team_lead','security_analyst')"
                )
                roles = {row["role_name"]: row["id"] for row in cursor.fetchall()}
                cursor.executemany(
                    "INSERT INTO user_roles (user_id, role_id) VALUES (%s, %s)",
                    (
                        (test_users["__stage4_admin__"], roles["administrator"]),
                        (test_users["__stage4_lead__"], roles["team_lead"]),
                        (test_users["__stage4_analyst__"], roles["security_analyst"]),
                    ),
                )

        with TestClient(app) as client:
            expect(client, "GET", "/api/v1/network/alerts", None, 401)

            admin_token = login(client, "__stage4_admin__", "administrator")
            lead_token = login(client, "__stage4_lead__", "team_lead")
            analyst_token = login(client, "__stage4_analyst__", "security_analyst")

            expect(client, "GET", "/api/v1/network/alerts", admin_token, 200)
            expect(client, "GET", "/api/v1/network/alerts", lead_token, 200)
            expect(client, "GET", "/api/v1/network/alerts", analyst_token, 200)
            expect(
                client,
                "POST",
                "/api/v1/network/alerts/evaluate",
                lead_token,
                403,
                {"capture_source": "live_capture", "capture_id": TRIGGER_CAPTURE},
            )

            boundary = expect(
                client,
                "POST",
                "/api/v1/network/alerts/evaluate",
                analyst_token,
                200,
                {"capture_source": "live_capture", "capture_id": BOUNDARY_CAPTURE},
            ).json()
            if boundary["created_count"] != 0:
                raise AssertionError(
                    f"499-packet boundary unexpectedly created {boundary['created_count']} alerts"
                )
            print("PASS threshold_boundary 499_packets=0_alerts")

            triggered = expect(
                client,
                "POST",
                "/api/v1/network/alerts/evaluate",
                analyst_token,
                200,
                {"capture_source": "live_capture", "capture_id": TRIGGER_CAPTURE},
            ).json()
            if triggered["created_count"] != 2:
                raise AssertionError(
                    f"501-packet trigger created {triggered['created_count']} alerts, expected 2"
                )
            print("PASS detection_rules 501_packets=2_alerts")

            duplicate = expect(
                client,
                "POST",
                "/api/v1/network/alerts/evaluate",
                analyst_token,
                200,
                {"capture_source": "live_capture", "capture_id": TRIGGER_CAPTURE},
            ).json()
            if duplicate["created_count"] != 0:
                raise AssertionError("Duplicate alert was created inside cooldown")
            print("PASS alert_deduplication duplicate=0")

            historical = expect(
                client,
                "POST",
                "/api/v1/network/alerts/evaluate",
                analyst_token,
                200,
                {
                    "capture_source": "historical_import",
                    "capture_id": HISTORICAL_CAPTURE,
                },
            ).json()
            if historical["created_count"] != 2:
                raise AssertionError(
                    f"Historical source created {historical['created_count']} alerts, expected 2"
                )
            if any(
                alert["capture_source"] != "historical_import"
                for alert in historical["created"]
            ):
                raise AssertionError("Historical alert was not source-labelled")
            print("PASS historical_source_identification alerts=2")

            listed = expect(
                client,
                "GET",
                "/api/v1/network/alerts",
                analyst_token,
                200,
                {
                    "capture_source": "live_capture",
                    "rule_name": "High Packet Volume",
                },
            ).json()
            if listed["total"] != 1:
                raise AssertionError(
                    f"High Packet Volume filter returned {listed['total']} alerts"
                )
            alert_id = listed["items"][0]["id"]

            expect(
                client,
                "POST",
                f"/api/v1/network/alerts/{alert_id}/acknowledge",
                lead_token,
                403,
            )
            acknowledged = expect(
                client,
                "POST",
                f"/api/v1/network/alerts/{alert_id}/acknowledge",
                analyst_token,
                200,
            ).json()
            if acknowledged["status"] != "acknowledged":
                raise AssertionError("Alert acknowledgement did not persist")
            print("PASS alert_acknowledgement")

            resolved = expect(
                client,
                "POST",
                f"/api/v1/network/alerts/{alert_id}/resolve",
                analyst_token,
                200,
            ).json()
            if resolved["status"] != "resolved":
                raise AssertionError("Alert resolution did not persist")
            print("PASS alert_resolution")

            summary = expect(
                client,
                "GET",
                "/api/v1/network/alerts/summary",
                analyst_token,
                200,
            ).json()
            if summary["total"] < 2:
                raise AssertionError("Alert summary did not include stored alerts")
            print(
                f"PASS alert_summary total={summary['total']} "
                f"medium={summary['by_severity'].get('medium', 0)}"
            )
    finally:
        with connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM network_alerts WHERE capture_id LIKE '__stage4_%'"
                )
                cursor.execute(
                    "DELETE FROM public.network_packets "
                    "WHERE capture_id IN (%s, %s, %s)",
                    (BOUNDARY_CAPTURE, TRIGGER_CAPTURE, HISTORICAL_CAPTURE),
                )
                if test_ids:
                    cursor.execute(
                        "DELETE FROM audit_logs WHERE actor_user_id = ANY(%s)",
                        (test_ids,),
                    )
                cursor.execute(
                    "DELETE FROM users WHERE username LIKE '__stage4_%'"
                )
        connection.close()
        print("PASS isolated Stage 4 test data cleaned up")


if __name__ == "__main__":
    main()
