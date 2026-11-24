import sys
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


PASSWORD = "Stage2!Test123"


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


def expect_get(client, path, token, expected_status):
    response = client.get(
        path,
        headers={"Authorization": f"Bearer {token}"} if token else None,
    )
    if response.status_code != expected_status:
        raise AssertionError(
            f"GET {path}: got {response.status_code}, "
            f"expected {expected_status}: {response.text}"
        )
    return response


def main():
    connection = connect()
    test_ids = {}
    before_packet_count = None

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) AS count FROM public.network_packets")
            before_packet_count = cursor.fetchone()["count"]

            cursor.execute(
                """
                SELECT r.role_name, p.permission_code
                FROM roles r
                JOIN role_permissions rp ON rp.role_id = r.id
                JOIN permissions p ON p.id = rp.permission_id
                WHERE p.permission_code IN (
                    'network.view',
                    'network.analyze',
                    'reports.generate'
                )
                ORDER BY r.role_name, p.permission_code
                """
            )
            mappings = cursor.fetchall()

        permission_map = {}
        for row in mappings:
            permission_map.setdefault(row["role_name"], set()).add(
                row["permission_code"]
            )

        required = {
            "administrator": {"network.view", "network.analyze", "reports.generate"},
            "team_lead": {"network.view", "reports.generate"},
            "security_analyst": {
                "network.view",
                "network.analyze",
                "reports.generate",
            },
        }
        for role_name, permissions in required.items():
            actual = permission_map.get(role_name, set())
            if not permissions.issubset(actual):
                raise AssertionError(
                    f"{role_name} missing network permissions: "
                    f"{sorted(permissions - actual)}"
                )
            print(f"PASS network_permissions role={role_name}")

        with connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    DELETE FROM audit_logs
                    WHERE actor_user_id IN (
                        SELECT id FROM users
                        WHERE username LIKE '__stage2_network_%'
                    )
                    """
                )
                cursor.execute(
                    "DELETE FROM users WHERE username LIKE '__stage2_network_%'"
                )

                password_hash = hash_password(PASSWORD)
                cursor.execute(
                    """
                    INSERT INTO users
                        (username, email, full_name, password_hash, status)
                    VALUES
                        ('__stage2_network_lead__', '__stage2_network_lead@example.invalid', 'Stage 2 Team Lead', %s, 'active'),
                        ('__stage2_network_analyst__', '__stage2_network_analyst@example.invalid', 'Stage 2 Analyst', %s, 'active')
                    RETURNING username, id
                    """,
                    (password_hash, password_hash),
                )
                test_ids.update({row["username"]: row["id"] for row in cursor.fetchall()})

                cursor.execute(
                    "SELECT id, role_name FROM roles WHERE role_name IN ('team_lead','security_analyst')"
                )
                roles = {row["role_name"]: row["id"] for row in cursor.fetchall()}
                cursor.executemany(
                    "INSERT INTO user_roles (user_id, role_id) VALUES (%s, %s)",
                    (
                        (test_ids["__stage2_network_lead__"], roles["team_lead"]),
                        (
                            test_ids["__stage2_network_analyst__"],
                            roles["security_analyst"],
                        ),
                    ),
                )

        with TestClient(app) as client:
            lead_token = login(
                client, "__stage2_network_lead__", "team_lead"
            )
            analyst_token = login(
                client, "__stage2_network_analyst__", "security_analyst"
            )

            expect_get(client, "/api/v1/network/summary", None, 401)
            expect_get(
                client,
                "/api/v1/network/protocols",
                lead_token,
                403,
            )
            expect_get(
                client,
                "/api/v1/network/report",
                lead_token,
                200,
            )
            expect_get(
                client,
                "/api/v1/network/report",
                analyst_token,
                200,
            )

            summary_response = expect_get(
                client,
                "/api/v1/network/summary",
                analyst_token,
                200,
            )
            summary = summary_response.json()
            if summary["total_packets"] != before_packet_count:
                raise AssertionError("Network summary packet count differs from database")
            if summary["data_source"] != "historical_import":
                raise AssertionError("Summary does not identify imported historical data")
            if summary["live_capture_enabled"] is not False:
                raise AssertionError("Summary claims live capture is enabled")
            print(
                f"PASS network_summary packets={summary['total_packets']} "
                "historical_import=true live_capture=false"
            )

            protocols = expect_get(
                client,
                "/api/v1/network/protocols",
                analyst_token,
                200,
            ).json()
            if not protocols["protocols"]:
                raise AssertionError("Protocol statistics returned no protocol rows")
            print(
                f"PASS protocol_statistics protocol_rows="
                f"{len(protocols['protocols'])}"
            )

            packet_page_1 = expect_get(
                client,
                "/api/v1/network/packets?page=1&page_size=10",
                analyst_token,
                200,
            ).json()
            packet_page_2 = expect_get(
                client,
                "/api/v1/network/packets?page=2&page_size=10",
                analyst_token,
                200,
            ).json()
            if packet_page_1["page"] != 1 or packet_page_2["page"] != 2:
                raise AssertionError("Packet pagination page metadata is incorrect")
            if packet_page_1["items"] == packet_page_2["items"]:
                raise AssertionError("Packet pagination returned identical rows")
            print(
                f"PASS packet_pagination total={packet_page_1['total']} "
                f"page1={len(packet_page_1['items'])} page2={len(packet_page_2['items'])}"
            )

            first = packet_page_1["items"][0]
            if first["source_ip"]:
                filtered = expect_get(
                    client,
                    f"/api/v1/network/packets?source_ip={first['source_ip']}&page=1&page_size=10",
                    analyst_token,
                    200,
                ).json()
                if filtered["items"] and any(
                    item["source_ip"] != first["source_ip"]
                    for item in filtered["items"]
                ):
                    raise AssertionError("Source IP filter returned a mismatched row")
                print("PASS packet_filter source_ip")

            if first["protocol"]:
                filtered_protocol = expect_get(
                    client,
                    f"/api/v1/network/packets?protocol={first['protocol']}&page=1&page_size=10",
                    analyst_token,
                    200,
                ).json()
                print(
                    f"PASS packet_filter protocol={first['protocol']} "
                    f"matches={filtered_protocol['total']}"
                )

            for bucket in ("minute", "hour", "day"):
                timeline = expect_get(
                    client,
                    f"/api/v1/network/timeline?bucket={bucket}",
                    analyst_token,
                    200,
                ).json()
                if "items" not in timeline:
                    raise AssertionError(f"{bucket} timeline response is malformed")
                print(
                    f"PASS packet_timeline bucket={bucket} "
                    f"points={len(timeline['items'])}"
                )

            report = expect_get(
                client,
                "/api/v1/network/report",
                analyst_token,
                200,
            )
            report_data = report.json()
            if report_data["data_source"] != "historical_import":
                raise AssertionError("JSON report does not identify historical data")
            if report_data["live_capture_enabled"] is not False:
                raise AssertionError("JSON report claims live capture is enabled")
            if report.headers.get("content-disposition") is None:
                raise AssertionError("JSON report lacks attachment disposition")
            print("PASS json_report attachment=true historical_import=true")

        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) AS count FROM public.network_packets")
            after_packet_count = cursor.fetchone()["count"]
        if after_packet_count != before_packet_count:
            raise AssertionError("Packet record count changed during Stage 2 verification")
        print(
            f"PASS packet_records_unchanged count={before_packet_count}"
        )
    finally:
        with connection:
            with connection.cursor() as cursor:
                if test_ids:
                    cursor.execute(
                        "DELETE FROM audit_logs WHERE actor_user_id = ANY(%s)",
                        (list(test_ids.values()),),
                    )
                cursor.execute(
                    "DELETE FROM users WHERE username LIKE '__stage2_network_%'"
                )
        connection.close()
        print("PASS temporary Stage 2 test accounts cleaned up")


if __name__ == "__main__":
    main()
